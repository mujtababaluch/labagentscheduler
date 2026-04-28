"""
app.py  -  Professional Streamlit UI for the SAIT Lab Scheduling Assistant.
Two tabs:
  1. Chat Assistant  -  conversational agent
  2. Lab Schedule    -  full visual timetable grid for all labs
Run with:  streamlit run app.py
"""

import os
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent import run_agent
from scheduler import load_bookings, load_schedule, SLOT_INFO

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lab Scheduler",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Professional CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global ─────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}
.stApp { background: #eef2f7 !important; }
[data-testid="stAppViewContainer"] { background: #eef2f7 !important; }
[data-testid="stMain"] { background: #eef2f7 !important; }
[data-testid="stVerticalBlock"] { background: transparent !important; }
section.main { background: #eef2f7 !important; }
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; background: #eef2f7 !important; }

/* ── Sidebar ────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0f172a !important;
    box-shadow: 3px 0 18px rgba(0,0,0,0.45) !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] .stCaption > p {
    color: #64748b !important; font-size: 0.78rem !important; line-height: 1.5 !important;
}
section[data-testid="stSidebar"] h1 {
    color: #f1f5f9 !important; font-size: 0.95rem !important;
    font-weight: 700 !important; letter-spacing: -0.01em !important; margin: 0 !important;
}
section[data-testid="stSidebar"] h2 {
    color: #334155 !important; font-size: 0.63rem !important; font-weight: 600 !important;
    text-transform: uppercase !important; letter-spacing: 0.1em !important; margin-bottom: 5px !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.06) !important; margin: 0.55rem 0 !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    color: #94a3b8 !important; border-radius: 7px !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.78rem !important;
    font-weight: 400 !important; text-align: left !important;
    padding: 7px 11px !important; margin-bottom: 2px !important;
    width: 100% !important; box-shadow: none !important; line-height: 1.35 !important;
    transition: background 0.15s, border-color 0.15s, color 0.15s, transform 0.15s !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(59,130,246,0.12) !important;
    border-color: rgba(59,130,246,0.28) !important;
    color: #e2e8f0 !important; transform: translateX(3px) !important; box-shadow: none !important;
}
section[data-testid="stSidebar"] .stButton > button:focus { box-shadow: none !important; }
section[data-testid="stSidebar"] [data-testid="stMetric"] {
    background: rgba(59,130,246,0.07) !important;
    border: 1px solid rgba(59,130,246,0.16) !important;
    border-radius: 9px !important; padding: 10px 14px !important;
}
[data-testid="stMetricValue"] { color: #60a5fa !important; font-weight: 700 !important; font-size: 1.45rem !important; }
[data-testid="stMetricLabel"] { color: #475569 !important; font-size: 0.72rem !important; }

/* ── Tab navigation ─────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #1a2d45 !important;
    gap: 0 !important;
    padding: 0 28px !important;
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
}
.stTabs [data-baseweb="tab"] {
    color: #64748b !important;
    font-size: 0.82rem !important; font-weight: 500 !important;
    padding: 12px 24px !important; border-radius: 0 !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    transition: color 0.15s !important;
}
.stTabs [aria-selected="true"] {
    color: #f1f5f9 !important;
    border-bottom: 2px solid #3b82f6 !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
    color: #94a3b8 !important;
    background: rgba(255,255,255,0.03) !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* ── Chat messages ──────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: transparent !important; border: none !important;
    padding: 4px 2.5rem !important; max-width: 900px !important; margin: 0 auto !important;
}

/* ── Chat input ─────────────────────────────────────── */
[data-testid="stChatInput"] {
    background: #fff !important; border: 1.5px solid #dde3ea !important;
    border-radius: 12px !important; box-shadow: 0 2px 14px rgba(0,0,0,0.06) !important;
    max-width: 900px !important; margin: 0 auto 1.25rem !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.1), 0 2px 14px rgba(0,0,0,0.06) !important;
}
[data-testid="stChatInput"] textarea {
    font-family: 'Inter', sans-serif !important; font-size: 0.875rem !important; color: #1e293b !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #94a3b8 !important; }
[data-testid="stChatInputSubmitButton"] > button {
    background: #2563eb !important; border-radius: 8px !important; transition: background 0.15s !important;
}
[data-testid="stChatInputSubmitButton"] > button:hover { background: #1d4ed8 !important; }

/* ── Selectbox (day picker) ─────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: #fff !important;
    border: 1.5px solid #dde3ea !important;
    border-radius: 9px !important;
    font-size: 0.85rem !important;
}

/* ── Fix white area around chat input ───────────────── */
[data-testid="stBottom"] {
    background: #eef2f7 !important;
    border-top: none !important;
}
[data-testid="stBottom"] > div {
    background: #eef2f7 !important;
}

/* ── Spinner ────────────────────────────────────────── */
.stSpinner > div { border-top-color: #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)


# ── Session state ─────────────────────────────────────────────────────────────
def _init():
    if "messages"       not in st.session_state: st.session_state.messages      = []
    if "history"        not in st.session_state: st.session_state.history       = []
    if "pending_query"  not in st.session_state: st.session_state.pending_query = None

_init()


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:18px 16px 14px;border-bottom:1px solid rgba(255,255,255,0.06);margin-bottom:10px;">
        <div style="color:#f1f5f9;font-size:0.95rem;font-weight:700;letter-spacing:-0.01em;line-height:1.2;">
            Lab Scheduler
        </div>
        <div style="display:inline-block;margin-top:8px;background:rgba(59,130,246,0.12);
                    border:1px solid rgba(59,130,246,0.22);color:#60a5fa;font-size:0.65rem;
                    font-weight:600;padding:2px 8px;border-radius:20px;letter-spacing:0.04em;
                    text-transform:uppercase;">
            AI Scheduling Assistant
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Availability")
    for label, query in [
        ("Free labs  -  Monday morning",     "Which labs are free on Monday morning?"),
        ("Free labs  -  Thursday afternoon", "Which labs are free on Thursday afternoon?"),
        ("Free labs  -  Wednesday evening",  "Which labs are free on Wednesday evening?"),
        ("Free labs  -  Saturday 9am",       "Which labs are free on Saturday at 9am?"),
        ("Free labs  -  Friday 3pm",         "Which labs are free on Friday at 3pm?"),
    ]:
        if st.button(label, key=f"a_{label}", use_container_width=True):
            st.session_state.pending_query = query

    st.divider()
    st.markdown("## Lab Status")
    for label, query in [
        ("Lab 104  -  full schedule",   "Show me the full schedule for Lab 104"),
        ("Lab 107  -  who is using it", "Who is using Lab 107 this week?"),
        ("Lab 108  -  availability",    "What is the availability of Lab 108?"),
        ("Lab 109  -  all slots",       "Show all time slots for Lab 109"),
    ]:
        if st.button(label, key=f"s_{label}", use_container_width=True):
            st.session_state.pending_query = query

    st.divider()
    st.markdown("## Book a Lab")
    for label, query in [
        ("Book Lab 109  -  Mon 9am",  "Book Lab 109 for Monday at 9am for Mr. Ahmed"),
        ("Book Lab 110  -  Thu 3pm",  "Book Lab 110 for Thursday at 3pm for Ms. Sara"),
        ("Book Lab 111  -  Sat 11am", "Book Lab 111 for Saturday at 11am for Mr. Usman"),
        ("Book Lab 108  -  Wed 5pm",  "Book Lab 108 for Wednesday at 5pm for Mr. Rizwan"),
    ]:
        if st.button(label, key=f"b_{label}", use_container_width=True):
            st.session_state.pending_query = query

    st.divider()
    st.markdown("## Time Slots")
    slot_rows = "".join(
        f'<tr><td style="color:#60a5fa;font-weight:600;padding:3px 10px 3px 0;font-size:0.78rem;">{k}</td>'
        f'<td style="color:#94a3b8;font-size:0.78rem;">{v["label"]}</td></tr>'
        for k, v in SLOT_INFO.items()
    )
    st.markdown(f"""
    <table style="border-collapse:collapse;width:100%;margin-bottom:8px;">{slot_rows}</table>
    <div style="font-size:0.72rem;margin-top:4px;color:#334155;">
        <span style="color:#94a3b8;">MWF</span>&nbsp; Mon &middot; Wed &middot; Fri
        &nbsp;&nbsp;
        <span style="color:#94a3b8;">TTS</span>&nbsp; Tue &middot; Thu &middot; Sat
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    try:
        booking_count = len(load_bookings())
    except Exception:
        booking_count = 0
    st.metric("Active Bookings", booking_count)

    st.divider()
    if st.button("Clear Conversation", key="clear", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history  = []
        st.rerun()


# ── Top header bar (shown on both tabs) ──────────────────────────────────────
today_str = datetime.now().strftime("%A, %d %B %Y")
st.markdown(f"""
<div style="background:linear-gradient(90deg,#0f172a 0%,#1e3a5f 55%,#1e40af 100%);
            padding:14px 36px;display:flex;align-items:center;justify-content:space-between;
            box-shadow:0 2px 10px rgba(0,0,0,0.22);">
    <div>
        <div style="color:#f8fafc;font-size:0.98rem;font-weight:600;letter-spacing:-0.01em;">
            Lab Availability and Booking System
        </div>
    </div>
    <div style="text-align:right;">
        <div style="color:#334155;font-size:0.65rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;">Today</div>
        <div style="color:#cbd5e1;font-size:0.78rem;font-weight:500;margin-top:1px;">{today_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Two tabs ──────────────────────────────────────────────────────────────────
tab_chat, tab_schedule, tab_status = st.tabs(["  Chat Assistant  ", "  Lab Schedule  ", "  Lab Status  "])


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT ASSISTANT
# ═══════════════════════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    WELCOME = """\
**Welcome to the Lab Scheduling Assistant.**

I can help you with the following:

- Check whether a specific lab is **free or busy** at any time slot
- Find **all available labs** on a given day and time
- **Book a lab** for a teacher and save the reservation

**To get started, try asking:**

- *Is Lab 104 free at 2pm Monday?*
- *Which labs are free Thursday morning?*
- *Book Lab 109 for Friday 3pm for Mr. Ahmed*

You can also use the quick-action buttons in the left panel.
"""
    if not st.session_state.messages:
        st.session_state.messages.append({"role": "assistant", "content": WELCOME})

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    def _process(text: str) -> None:
        st.session_state.messages.append({"role": "user", "content": text})
        with st.chat_message("user"):
            st.markdown(text)
        with st.chat_message("assistant"):
            with st.spinner("Checking schedule..."):
                try:
                    reply = run_agent(text, st.session_state.history)
                except EnvironmentError as exc:
                    reply = f"**Configuration error:** {exc}"
                except Exception as exc:
                    msg = str(exc)
                    if "rate_limit_exceeded" in msg or "429" in msg:
                        reply = (
                            "**Rate limit reached.** The Groq API daily token quota is exhausted.  \n"
                            "Please wait a while and try again, or upgrade your Groq plan at "
                            "[console.groq.com/settings/billing](https://console.groq.com/settings/billing)."
                        )
                    else:
                        reply = f"**Error:** {exc}"
            st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.history.append({"role": "user",      "content": text})
        st.session_state.history.append({"role": "assistant", "content": reply})

    if st.session_state.pending_query:
        q = st.session_state.pending_query
        st.session_state.pending_query = None
        _process(q)

    if user_input := st.chat_input("Ask about lab availability or make a booking..."):
        _process(user_input)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — LAB SCHEDULE GRID
# ═══════════════════════════════════════════════════════════════════════════════
with tab_schedule:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── Day selector + summary stats row ─────────────────────────────────────
    col_day, col_stats = st.columns([2, 5], gap="large")

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    with col_day:
        selected_day = st.selectbox(
            "Select Day",
            DAYS,
            index=0,
            key="grid_day",
            label_visibility="visible",
        )

    pattern = "MWF" if selected_day in ["Monday", "Wednesday", "Friday"] else "TTS"

    # Load data
    schedule  = load_schedule()
    bookings  = load_bookings()
    labs      = list(schedule["labs"].keys())
    slots     = list(SLOT_INFO.keys())

    # Build booked lookup: {(lab, slot): teacher}
    booked_map = {
        (b["lab"], b["slot"]): b["teacher"]
        for b in bookings
        if b["day"].lower() == selected_day.lower()
    }

    # Count totals for the selected day
    total_cells = len(labs) * len(slots)
    free_count  = sum(
        1 for lab in labs for slot in slots
        if schedule["labs"][lab]["schedule"][slot][pattern] == "FREE"
        and (lab, slot) not in booked_map
    )
    busy_count   = sum(
        1 for lab in labs for slot in slots
        if schedule["labs"][lab]["schedule"][slot][pattern] != "FREE"
        and (lab, slot) not in booked_map
    )
    booked_count = len(booked_map)

    with col_stats:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:12px 16px;">
                <div style="color:#64748b;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Pattern</div>
                <div style="color:#1e293b;font-size:1.1rem;font-weight:700;margin-top:3px;">{pattern}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:12px 16px;">
                <div style="color:#166534;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Free Slots</div>
                <div style="color:#16a34a;font-size:1.1rem;font-weight:700;margin-top:3px;">{free_count}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div style="background:#fff7f7;border:1px solid #fecaca;border-radius:10px;padding:12px 16px;">
                <div style="color:#991b1b;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Occupied</div>
                <div style="color:#dc2626;font-size:1.1rem;font-weight:700;margin-top:3px;">{busy_count}</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px 16px;">
                <div style="color:#1e40af;font-size:0.7rem;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;">Booked</div>
                <div style="color:#2563eb;font-size:1.1rem;font-weight:700;margin-top:3px;">{booked_count}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── Helper: shorten long occupant names for grid cells ───────────────────
    def _shorten(text: str) -> str:
        if text == "FREE":
            return "FREE"
        if "Reserved for Online Classes" in text:
            return "Online Reserved"
        if text.startswith("NAVTTC"):
            rest = text[6:].strip().lstrip("-").strip()
            abbr = {
                "Graphic Design (UI/UX)": "Graphic Design",
                "Mobile Application Development": "Mobile Dev",
                "Cyber Security (CEH)": "Cyber Security",
            }
            return "NAVTTC  " + abbr.get(rest, rest[:14])
        return text if len(text) <= 20 else text[:18] + "..."

    # ── Build the HTML grid table ─────────────────────────────────────────────
    # -- Column headers (lab IDs + capacity)
    th_style = (
        "background:#1e2d45;color:#94a3b8;font-size:0.72rem;font-weight:600;"
        "padding:9px 6px;text-align:center;white-space:nowrap;"
        "border-right:1px solid rgba(255,255,255,0.06);"
    )
    header_html = f'<th style="{th_style} min-width:90px;">Slot / Time</th>'
    for lab in labs:
        cap = schedule["labs"][lab]["capacity"]
        header_html += (
            f'<th style="{th_style}">'
            f'<div style="color:#e2e8f0;font-weight:700;">Lab {lab}</div>'
            f'<div style="color:#475569;font-size:0.65rem;margin-top:2px;">{cap} seats</div>'
            f'</th>'
        )

    # -- Data rows
    rows_html = ""
    for slot in slots:
        time_label = SLOT_INFO[slot]["label"]
        slot_td = (
            f'<td style="background:#1e2d45;color:#60a5fa;font-weight:700;font-size:0.8rem;'
            f'padding:10px 10px;text-align:center;white-space:nowrap;'
            f'border-right:1px solid rgba(255,255,255,0.08);border-bottom:1px solid rgba(255,255,255,0.05);">'
            f'<div style="font-size:0.9rem;">{slot}</div>'
            f'<div style="color:#475569;font-size:0.65rem;font-weight:400;margin-top:2px;">{time_label}</div>'
            f'</td>'
        )
        cells = ""
        for lab in labs:
            border = "border-right:1px solid #eef2f7;border-bottom:1px solid #eef2f7;"

            if (lab, slot) in booked_map:
                teacher = booked_map[(lab, slot)]
                short   = teacher if len(teacher) <= 18 else teacher[:16] + "..."
                cells += (
                    f'<td title="{teacher}" style="background:#dbeafe;{border}'
                    f'padding:8px 6px;text-align:center;vertical-align:middle;">'
                    f'<div style="color:#1e40af;font-size:0.68rem;font-weight:600;'
                    f'text-transform:uppercase;letter-spacing:0.04em;">Booked</div>'
                    f'<div style="color:#1d4ed8;font-size:0.7rem;margin-top:2px;'
                    f'line-height:1.3;">{short}</div>'
                    f'</td>'
                )
            else:
                occupant = schedule["labs"][lab]["schedule"][slot][pattern]
                display  = _shorten(occupant)

                if occupant == "FREE":
                    cells += (
                        f'<td style="background:#f0fdf4;{border}'
                        f'padding:8px 6px;text-align:center;vertical-align:middle;">'
                        f'<div style="color:#16a34a;font-size:0.78rem;font-weight:700;'
                        f'letter-spacing:0.03em;">FREE</div>'
                        f'</td>'
                    )
                elif "Reserved for Online Classes" in occupant:
                    cells += (
                        f'<td style="background:#f8fafc;{border}'
                        f'padding:8px 6px;text-align:center;vertical-align:middle;">'
                        f'<div style="color:#94a3b8;font-size:0.68rem;font-weight:500;'
                        f'line-height:1.35;">{display}</div>'
                        f'</td>'
                    )
                else:
                    cells += (
                        f'<td title="{occupant}" style="background:#fff7f7;{border}'
                        f'padding:8px 6px;text-align:center;vertical-align:middle;">'
                        f'<div style="color:#991b1b;font-size:0.68rem;font-weight:500;'
                        f'line-height:1.35;">{display}</div>'
                        f'</td>'
                    )

        rows_html += f"<tr>{slot_td}{cells}</tr>"

    # -- Assemble full table
    grid_html = f"""
    <div style="overflow-x:auto;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.08);
                border:1px solid rgba(255,255,255,0.08);">
        <table style="border-collapse:collapse;width:100%;min-width:900px;background:#fff;">
            <thead>
                <tr style="border-bottom:2px solid rgba(255,255,255,0.08);">
                    {header_html}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    st.markdown(grid_html, unsafe_allow_html=True)

    # ── Legend ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;gap:20px;margin-top:14px;flex-wrap:wrap;">
        <div style="display:flex;align-items:center;gap:7px;">
            <div style="width:14px;height:14px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:3px;"></div>
            <span style="font-size:0.75rem;color:#64748b;">Free</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;">
            <div style="width:14px;height:14px;background:#fff7f7;border:1px solid #fecaca;border-radius:3px;"></div>
            <span style="font-size:0.75rem;color:#64748b;">Occupied by teacher / class</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;">
            <div style="width:14px;height:14px;background:#dbeafe;border:1px solid #bfdbfe;border-radius:3px;"></div>
            <span style="font-size:0.75rem;color:#64748b;">Manually booked</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;">
            <div style="width:14px;height:14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:3px;"></div>
            <span style="font-size:0.75rem;color:#64748b;">Reserved for online classes</span>
        </div>
    </div>
    <div style="height:24px;"></div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — LAB STATUS OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
with tab_status:
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    _sched  = load_schedule()
    _books  = load_bookings()
    _slots  = list(SLOT_INFO.keys())
    _labs   = list(_sched["labs"].keys())

    # Active booking counts per lab
    _booked_per_lab = {}
    for b in _books:
        _booked_per_lab[b["lab"]] = _booked_per_lab.get(b["lab"], 0) + 1

    # Classify each slot-pattern cell for a lab (ignores per-day booking detail
    # for the overview — bookings are shown separately as a badge count)
    def _cell_status(lab_id: str, slot: str, pattern: str) -> str:
        occupant = _sched["labs"][lab_id]["schedule"][slot][pattern]
        if occupant.upper() == "FREE":
            return "FREE"
        if "Reserved for Online Classes" in occupant:
            return "RESERVED"
        return "BUSY"

    # Build summary per lab
    _STATUS_COLORS = {
        "FREE":     ("#16a34a", "#dcfce7", "#bbf7d0"),
        "BUSY":     ("#dc2626", "#fee2e2", "#fecaca"),
        "RESERVED": ("#94a3b8", "#f1f5f9", "#e2e8f0"),
    }

    _OVERALL_BADGE = {
        "FULLY FREE": ("background:#dcfce7;border:1.5px solid #86efac;color:#166534;",  "Fully Free"),
        "OCCUPIED":   ("background:#fee2e2;border:1.5px solid #fca5a5;color:#991b1b;",  "Occupied"),
        "RESERVED":   ("background:#f1f5f9;border:1.5px solid #cbd5e1;color:#475569;",  "Reserved"),
        "PARTIAL":    ("background:#fefce8;border:1.5px solid #fde68a;color:#854d0e;",  "Partial"),
    }

    labs_info = []
    for _lab_id in _labs:
        _lab_data = _sched["labs"][_lab_id]
        _free = _busy = _rsv = 0
        _grid = {}
        for _slot in _slots:
            _grid[_slot] = {}
            for _pat in ("MWF", "TTS"):
                _st = _cell_status(_lab_id, _slot, _pat)
                _grid[_slot][_pat] = _st
                if _st == "FREE":     _free += 1
                elif _st == "BUSY":   _busy += 1
                else:                 _rsv  += 1

        _total = _free + _busy + _rsv
        if _rsv == _total:
            _overall = "RESERVED"
        elif _free == _total:
            _overall = "FULLY FREE"
        elif _busy == _total:
            _overall = "OCCUPIED"
        else:
            _overall = "PARTIAL"

        labs_info.append({
            "id":       _lab_id,
            "capacity": _lab_data["capacity"],
            "free":     _free,
            "busy":     _busy,
            "reserved": _rsv,
            "total":    _total,
            "overall":  _overall,
            "grid":     _grid,
            "bookings": _booked_per_lab.get(_lab_id, 0),
        })

    # ── Summary row ──────────────────────────────────────────────────────────
    _n_total  = len(labs_info)
    _n_free   = sum(1 for l in labs_info if l["overall"] == "FULLY FREE")
    _n_occ    = sum(1 for l in labs_info if l["overall"] == "OCCUPIED")
    _n_rsv    = sum(1 for l in labs_info if l["overall"] == "RESERVED")
    _n_part   = sum(1 for l in labs_info if l["overall"] == "PARTIAL")
    _n_books  = sum(l["bookings"] for l in labs_info)

    _sc1, _sc2, _sc3, _sc4, _sc5 = st.columns(5)
    for _col, _bg, _bdr, _tc, _vc, _label, _val in [
        (_sc1, "#fff",    "#e2e8f0", "#475569", "#0f172a",  "Total Labs",      _n_total),
        (_sc2, "#dcfce7", "#86efac", "#166534", "#15803d",  "Fully Free",      _n_free),
        (_sc3, "#fee2e2", "#fca5a5", "#991b1b", "#dc2626",  "Occupied",        _n_occ),
        (_sc4, "#f1f5f9", "#cbd5e1", "#475569", "#334155",  "Online Reserved", _n_rsv),
        (_sc5, "#eff6ff", "#bfdbfe", "#1e40af", "#2563eb",  "Active Bookings", _n_books),
    ]:
        with _col:
            st.markdown(f"""
            <div style="background:{_bg};border:1px solid {_bdr};border-radius:10px;
                        padding:12px 16px;text-align:center;margin-bottom:8px;">
                <div style="color:{_tc};font-size:0.68rem;font-weight:600;
                            text-transform:uppercase;letter-spacing:0.07em;">{_label}</div>
                <div style="color:{_vc};font-size:1.55rem;font-weight:800;
                            margin-top:4px;line-height:1;">{_val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Lab cards (4 per row) ─────────────────────────────────────────────────
    _COLS = 4
    for _row_start in range(0, len(labs_info), _COLS):
        _row_labs = labs_info[_row_start : _row_start + _COLS]
        _row_cols = st.columns(_COLS)

        for _ci, _lab in enumerate(_row_labs):
            with _row_cols[_ci]:
                _badge_css, _badge_label = _OVERALL_BADGE[_lab["overall"]]

                # Mini slot heatmap: rows = slots, cols = MWF / TTS
                _mini = (
                    '<table style="border-collapse:collapse;margin:8px auto 4px;">'
                    '<tr>'
                    '<th style="font-size:0.56rem;color:#94a3b8;padding:0 5px 3px;font-weight:500;text-align:center;">MWF</th>'
                    '<th style="font-size:0.56rem;color:#94a3b8;padding:0 5px 3px;font-weight:500;text-align:center;">TTS</th>'
                    '<th style="font-size:0.56rem;color:#64748b;padding:0 0 3px 6px;font-weight:600;text-align:left;"></th>'
                    '</tr>'
                )
                for _s in _slots:
                    _mini += "<tr>"
                    for _p in ("MWF", "TTS"):
                        _st = _lab["grid"][_s][_p]
                        _fc, _bg, _bd = _STATUS_COLORS[_st]
                        _mini += (
                            f'<td style="padding:2px 5px;">'
                            f'<div title="{_st}" style="width:22px;height:13px;background:{_bg};'
                            f'border:1px solid {_bd};border-radius:3px;"></div></td>'
                        )
                    _time = SLOT_INFO[_s]["label"]
                    _mini += (
                        f'<td style="padding:2px 0 2px 6px;font-size:0.57rem;'
                        f'color:#64748b;white-space:nowrap;">'
                        f'<span style="color:#475569;font-weight:700;">{_s}</span>'
                        f'&nbsp;{_time}</td>'
                    )
                    _mini += "</tr>"
                _mini += "</table>"

                # Free/Busy/Booked counters
                _counters = []
                if _lab["free"]:
                    _counters.append(f'<span style="color:#16a34a;font-weight:700;">{_lab["free"]} Free</span>')
                if _lab["busy"]:
                    _counters.append(f'<span style="color:#dc2626;font-weight:700;">{_lab["busy"]} Busy</span>')
                if _lab["reserved"]:
                    _counters.append(f'<span style="color:#94a3b8;font-weight:600;">{_lab["reserved"]} Rsvd</span>')
                _counter_html = '<div style="font-size:0.63rem;display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:6px;">' + "".join(_counters) + "</div>"

                # Booking badge
                _book_html = ""
                if _lab["bookings"]:
                    _n = _lab["bookings"]
                    _book_html = (
                        f'<div style="margin-top:7px;">'
                        f'<span style="background:#eff6ff;border:1px solid #bfdbfe;color:#2563eb;'
                        f'font-size:0.6rem;font-weight:600;padding:2px 9px;border-radius:20px;">'
                        f'{_n} active booking{"s" if _n != 1 else ""}</span></div>'
                    )

                st.markdown(f"""
                <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;
                            padding:16px 10px 14px;text-align:center;
                            box-shadow:0 1px 8px rgba(0,0,0,0.06);margin-bottom:14px;">
                    <div style="font-size:1.25rem;font-weight:800;color:#0f172a;
                                letter-spacing:-0.02em;">Lab {_lab["id"]}</div>
                    <div style="font-size:0.67rem;color:#94a3b8;margin-top:2px;">
                        {_lab["capacity"]} seats
                    </div>
                    <div style="margin-top:8px;margin-bottom:2px;">
                        <span style="{_badge_css}padding:3px 12px;border-radius:20px;
                                      font-size:0.63rem;font-weight:700;text-transform:uppercase;
                                      letter-spacing:0.06em;">{_badge_label}</span>
                    </div>
                    {_mini}
                    {_counter_html}
                    {_book_html}
                </div>
                """, unsafe_allow_html=True)

    # ── Legend ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex;gap:22px;margin-top:6px;flex-wrap:wrap;padding:0 4px;">
        <div style="display:flex;align-items:center;gap:7px;">
            <div style="width:18px;height:12px;background:#dcfce7;border:1px solid #86efac;border-radius:3px;"></div>
            <span style="font-size:0.73rem;color:#64748b;">Free slot</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;">
            <div style="width:18px;height:12px;background:#fee2e2;border:1px solid #fca5a5;border-radius:3px;"></div>
            <span style="font-size:0.73rem;color:#64748b;">Occupied (teacher / class)</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;">
            <div style="width:18px;height:12px;background:#f1f5f9;border:1px solid #cbd5e1;border-radius:3px;"></div>
            <span style="font-size:0.73rem;color:#64748b;">Reserved for online classes</span>
        </div>
        <div style="display:flex;align-items:center;gap:7px;">
            <div style="width:18px;height:12px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:3px;"></div>
            <span style="font-size:0.73rem;color:#64748b;">Active bookings (see Lab Schedule tab for details)</span>
        </div>
    </div>
    <div style="height:28px;"></div>
    """, unsafe_allow_html=True)
