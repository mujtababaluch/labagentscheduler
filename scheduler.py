"""
scheduler.py
Core data layer for the SAIT Lab Scheduling System.
Handles schedule loading, availability checks, and booking persistence.
"""

import json
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# File paths (resolved relative to this script so the app can run from any cwd)
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEDULE_FILE = os.path.join(_BASE_DIR, "Lab_status.json")
BOOKINGS_FILE = os.path.join(_BASE_DIR, "bookings.json")

# ---------------------------------------------------------------------------
# Lookup tables
# ---------------------------------------------------------------------------

# Slot letter → time range string and the hours that fall inside that slot
SLOT_INFO = {
    "B": {"label": "09:00–11:00", "hours": [9, 10]},
    "C": {"label": "11:00–13:00", "hours": [11, 12]},
    "D": {"label": "13:00–15:00", "hours": [13, 14]},
    "E": {"label": "15:00–17:00", "hours": [15, 16]},
    "F": {"label": "17:00–19:00", "hours": [17, 18]},
    "G": {"label": "19:00–21:00", "hours": [19, 20]},
}

# Day name → day-pattern key used in the JSON
DAY_TO_PATTERN = {
    "monday":    "MWF",
    "wednesday": "MWF",
    "friday":    "MWF",
    "tuesday":   "TTS",
    "thursday":  "TTS",
    "saturday":  "TTS",
}

# Friendly labels for each pattern
PATTERN_LABELS = {
    "MWF": "Monday / Wednesday / Friday",
    "TTS": "Tuesday / Thursday / Saturday",
}


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_schedule() -> dict:
    """Load and return the full schedule from Lab_status.json."""
    with open(SCHEDULE_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_bookings() -> list:
    """Return the bookings list; creates an empty file if none exists yet."""
    if not os.path.exists(BOOKINGS_FILE):
        return []
    with open(BOOKINGS_FILE, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_bookings(bookings: list) -> None:
    """Persist the bookings list to bookings.json."""
    with open(BOOKINGS_FILE, "w", encoding="utf-8") as fh:
        json.dump(bookings, fh, indent=2)


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def time_to_slot(time_str: str) -> str | None:
    """
    Convert a human-readable time string to a slot letter (B–G).

    Accepted formats: '9am', '2pm', '14:00', '2:00pm', '9:30 am', etc.
    Returns None when the string cannot be parsed or maps to no slot.
    """
    raw = time_str.lower().strip()
    hour = None

    if ":" in raw:
        # HH:MM or HH:MM am/pm
        numeric = raw.replace("am", "").replace("pm", "").strip()
        try:
            h = int(numeric.split(":")[0])
            if "pm" in raw and h != 12:
                h += 12
            elif "am" in raw and h == 12:
                h = 0
            hour = h
        except ValueError:
            return None
    elif "am" in raw or "pm" in raw:
        numeric = raw.replace("am", "").replace("pm", "").strip()
        try:
            h = int(numeric)
            if "pm" in raw and h != 12:
                h += 12
            elif "am" in raw and h == 12:
                h = 0
            hour = h
        except ValueError:
            return None
    else:
        try:
            hour = int(raw)
        except ValueError:
            return None

    for slot, info in SLOT_INFO.items():
        if hour in info["hours"]:
            return slot
    return None


def day_to_pattern(day_str: str) -> str | None:
    """
    Convert a day name to its pattern key (MWF or TTS).
    Returns None for days outside Monday–Saturday (e.g. Sunday).
    """
    return DAY_TO_PATTERN.get(day_str.lower().strip())


# ---------------------------------------------------------------------------
# Core scheduling functions (called by the AI agent as tools)
# ---------------------------------------------------------------------------

def check_lab_status(lab: str, day: str, time: str) -> dict:
    """
    Check whether a specific lab is FREE or BUSY at a given day and time.

    Returns a dict with keys:
        lab, day, slot, time_range, capacity, status ("FREE"/"BUSY"/"BOOKED"),
        occupant (None if free, else teacher/class name or booking detail)
    On invalid input returns {"error": "<message>"}.
    """
    schedule = load_schedule()
    bookings = load_bookings()

    slot = time_to_slot(time)
    pattern = day_to_pattern(day)

    if slot is None:
        return {
            "error": (
                f"Could not understand time '{time}'. "
                "Please use formats like '9am', '2pm', or '14:00'."
            )
        }
    if pattern is None:
        return {
            "error": (
                f"'{day}' is not a valid lab day (Monday through Saturday, no Sundays)."
            )
        }

    available_labs = list(schedule["labs"].keys())
    # Normalise lab id — accept '104' or 'Lab 104'
    lab_id = lab.strip().upper().replace("LAB", "").replace(" ", "")
    if lab_id not in schedule["labs"]:
        return {
            "error": (
                f"Lab '{lab}' not found. "
                f"Available labs: {', '.join(available_labs)}"
            )
        }

    # Bookings take precedence over the base schedule
    for booking in bookings:
        if (
            booking["lab"] == lab_id
            and booking["day"].lower() == day.lower()
            and booking["slot"] == slot
        ):
            return {
                "lab": lab_id,
                "day": day.capitalize(),
                "slot": slot,
                "time_range": SLOT_INFO[slot]["label"],
                "capacity": schedule["labs"][lab_id]["capacity"],
                "status": "BOOKED",
                "occupant": f"Booking for {booking['teacher']} (made on {booking['booked_at']})",
            }

    # Base schedule
    occupant = schedule["labs"][lab_id]["schedule"][slot][pattern]
    is_free = occupant.upper() == "FREE"

    return {
        "lab": lab_id,
        "day": day.capitalize(),
        "slot": slot,
        "time_range": SLOT_INFO[slot]["label"],
        "capacity": schedule["labs"][lab_id]["capacity"],
        "status": "FREE" if is_free else "BUSY",
        "occupant": None if is_free else occupant,
    }


def find_free_labs(day: str, time: str) -> dict:
    """
    Return every lab that is free at a given day and time.

    Returns a dict with keys:
        day, slot, time_range, free_labs (list of {lab, capacity}), count
    On invalid input returns {"error": "<message>"}.
    """
    schedule = load_schedule()

    slot = time_to_slot(time)
    pattern = day_to_pattern(day)

    if slot is None:
        return {"error": f"Could not understand time '{time}'."}
    if pattern is None:
        return {"error": f"'{day}' is not a valid lab day."}

    # Collect labs that have bookings on this day/slot
    bookings = load_bookings()
    booked_keys = {
        (b["lab"], b["slot"])
        for b in bookings
        if b["day"].lower() == day.lower()
    }

    free_labs = []
    for lab_id, lab_data in schedule["labs"].items():
        occupant = lab_data["schedule"][slot][pattern]
        if occupant.upper() == "FREE" and (lab_id, slot) not in booked_keys:
            free_labs.append({"lab": lab_id, "capacity": lab_data["capacity"]})

    return {
        "day": day.capitalize(),
        "slot": slot,
        "time_range": SLOT_INFO[slot]["label"],
        "free_labs": free_labs,
        "count": len(free_labs),
    }


def book_lab(lab: str, day: str, time: str, teacher: str) -> dict:
    """
    Attempt to book a lab for a teacher.

    Validates availability first. On conflict returns:
        {"error": "...", "occupant": "...", "alternatives": [...]}
    On success returns booking confirmation dict and persists to bookings.json.
    """
    # Normalise lab id
    lab_id = lab.strip().upper().replace("LAB", "").replace(" ", "")

    availability = check_lab_status(lab_id, day, time)
    if "error" in availability:
        return availability

    if availability["status"] != "FREE":
        alternatives = find_free_labs(day, time)
        alt_labs = [item["lab"] for item in alternatives.get("free_labs", [])]
        return {
            "error": f"Lab {lab_id} is {availability['status']} at that time.",
            "occupant": availability.get("occupant"),
            "alternatives": alt_labs,
        }

    booking = {
        "lab": lab_id,
        "day": day.capitalize(),
        "slot": availability["slot"],
        "time_range": availability["time_range"],
        "teacher": teacher,
        "booked_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    existing = load_bookings()
    existing.append(booking)
    save_bookings(existing)

    return {
        "success": True,
        "lab": lab_id,
        "day": day.capitalize(),
        "slot": availability["slot"],
        "time_range": availability["time_range"],
        "capacity": availability["capacity"],
        "teacher": teacher,
        "booked_at": booking["booked_at"],
    }


# ---------------------------------------------------------------------------
# Schedule summary (injected into the agent's system prompt)
# ---------------------------------------------------------------------------

def get_schedule_summary() -> str:
    """
    Build a compact, human-readable summary of the schedule.
    Used to give the AI agent full context in its system prompt.
    """
    schedule = load_schedule()

    lines = [
        "=== SAIT LAB SCHEDULE ===",
        f"Last updated: {schedule['last_updated']}",
        "",
        "TIME SLOTS:",
    ]
    for letter, time_range in schedule["time_slots"].items():
        lines.append(f"  {letter}: {time_range}")

    lines += [
        "",
        "DAY PATTERNS:",
        "  MWF = Monday, Wednesday, Friday",
        "  TTS = Tuesday, Thursday, Saturday",
        "(Sunday is not a lab day)",
        "",
        "LAB SCHEDULES  (format → Slot [time]: MWF status | TTS status)",
    ]

    for lab_id, lab_data in schedule["labs"].items():
        lines.append(f"\n  Lab {lab_id}  (capacity: {lab_data['capacity']} seats)")
        for slot, patterns in lab_data["schedule"].items():
            time_range = schedule["time_slots"][slot]
            mwf = patterns["MWF"]
            tts = patterns["TTS"]
            lines.append(f"    {slot} [{time_range}]:  MWF→{mwf}  |  TTS→{tts}")

    return "\n".join(lines)
