# SAIT Lab Scheduling Assistant

An AI-powered lab availability and booking system for **South Asian Institute of Technology (SAIT)**.  
Staff can check lab availability, view the full weekly timetable, and make bookings — all through a conversational chat interface backed by the **Groq API** (`llama-3.3-70b-versatile`) and a **Streamlit** UI.

---

## Features

| Feature | Description |
|---|---|
| **Chat Assistant** | Natural-language queries — ask about any lab, day, and time |
| **Lab Schedule Grid** | Full visual timetable for all labs on any selected day |
| **Lab Status Overview** | At-a-glance dashboard cards showing every lab's weekly status |
| **Live Bookings** | Book a lab for a teacher; reservations persist across sessions |
| **AI Tool Calling** | Agent uses Groq tool-calling to fetch real data before every answer |

---

## Project Structure

```
Sceneario B/
├── app.py               ← Streamlit UI (3 tabs: Chat · Schedule · Status)
├── agent.py             ← AI layer — Groq tool-calling agent loop
├── scheduler.py         ← Data layer — schedule queries & booking logic
├── Lab_status.json      ← Master schedule data (all labs, all slots)
├── bookings.json        ← Persistent booking records (auto-created)
├── requirements.txt     ← Python dependencies
└── .env                 ← Your secret keys (not committed)
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your Groq API key

Create a `.env` file in this folder:

```
GROQ_API_KEY=your_groq_api_key_here
```

Get a free key at [console.groq.com](https://console.groq.com).

### 3. Run the app

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## Application Tabs

### Tab 1 — Chat Assistant
Conversational interface. Type any question about lab availability or make a booking.
Quick-action buttons in the sidebar let you trigger common queries instantly.

### Tab 2 — Lab Schedule
Select a day from the dropdown to see the full timetable grid for all labs on that day.
Each cell shows who is using the lab, and colour-coded styling makes free slots immediately visible.

### Tab 3 — Lab Status
Visual dashboard with one card per lab showing:
- Overall status badge (Fully Free / Occupied / Reserved / Partial)
- Mini heatmap grid: 6 time slots × 2 day patterns (MWF / TTS)
- Slot counts (free / busy / reserved)
- Active booking badge if the lab has manual bookings

---

## Labs Reference

| Lab | Capacity | Status |
|-----|----------|--------|
| G01 | 24 | Reserved (Online Classes) |
| G02 | 23 | Reserved (Online Classes) |
| G03 | 24 | Reserved (Online Classes) |
| 101 | 18 | Reserved (Online Classes) |
| 102 | 18 | Occupied (teachers + NAVTTC) |
| 103 | 18 | Occupied (teachers + NAVTTC) |
| 104 | 24 | Occupied (teachers + NAVTTC) |
| 105 | 20 | Occupied (teachers + NAVTTC) |
| 106 | 20 | Occupied (teachers + NAVTTC) |
| 107 | 27 | Occupied (teachers + NAVTTC) |
| 108 | 17 | **Fully Free** |
| 109 | 24 | **Fully Free** |
| 110 | 15 | **Fully Free** |
| 111 | 13 | **Fully Free** |

---

## Time Slots

| Slot | Time Window |
|------|-------------|
| B | 09:00 – 11:00 |
| C | 11:00 – 13:00 |
| D | 13:00 – 15:00 |
| E | 15:00 – 17:00 |
| F | 17:00 – 19:00 |
| G | 19:00 – 21:00 |

### Day Patterns

| Pattern | Days |
|---------|------|
| MWF | Monday, Wednesday, Friday |
| TTS | Tuesday, Thursday, Saturday |

> Sunday is not a working lab day.

---

## Example Queries

```
Is Lab 104 free at 2pm Monday?
Which labs are free Thursday morning?
Which labs are free on Saturday at 9am?
Book Lab 109 for Friday 3pm for Mr. Ahmed
Show me all slots for Lab 108
Who is using Lab 107 this week?
What is Lab 110 availability on Wednesday?
```

---

## How It Works

```
User message
     │
     ▼
 app.py  (Streamlit UI)
     │
     ▼
 agent.py  →  Groq API  (llama-3.3-70b-versatile)
                  │
                  │  tool_calls (JSON)
                  ▼
            scheduler.py
            ├── check_lab_status()   — reads Lab_status.json + bookings.json
            ├── find_free_labs()     — scans all labs for a given slot
            └── book_lab()          — validates & writes to bookings.json
                  │
                  │  tool results (JSON)
                  ▼
            Groq API  →  natural-language reply
                  │
                  ▼
           app.py  →  Streamlit chat bubble
```

- **`scheduler.py`** is a pure data layer with no AI — deterministic and testable.
- **`agent.py`** runs a multi-step tool-calling loop: the model can invoke several tools before composing its final answer.
- **`app.py`** maintains `conversation_history` per session so the agent remembers earlier turns.
- Bookings in `bookings.json` always take precedence over the base schedule when checking availability.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| UI framework | Streamlit |
| AI model | Groq — `llama-3.3-70b-versatile` |
| AI client | `groq` Python SDK |
| Data storage | JSON files (schedule + bookings) |
| Environment config | `python-dotenv` |
| Language | Python 3.11+ |

---

## Files  to Modify

- **`Lab_status.json`** — the live institute schedule. Any availability changes must be made by editing this file directly; all bookings should go through the booking system.

---

## Video Link
https://drive.google.com/drive/folders/1q4kSUke1-bOIfPDqoc36jjgEtPVOOD-5?usp=sharing
