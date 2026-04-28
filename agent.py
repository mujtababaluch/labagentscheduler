"""
agent.py
AI agent layer for the SAIT Lab Scheduling System.
Uses Groq API (llama3-70b-8192) with tool-calling to answer scheduling queries.
"""

import json
import os
from groq import Groq
from scheduler import (
    check_lab_status,
    find_free_labs,
    book_lab,
    get_schedule_summary,
)

# ---------------------------------------------------------------------------
# Groq tool definitions — one per scheduler function
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_lab_status",
            "description": (
                "Check whether a specific lab is FREE or BUSY on a given day and time. "
                "Always use this before telling the user a lab is available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lab":  {"type": "string", "description": "Lab ID, e.g. '104', 'G01', '108'"},
                    "day":  {"type": "string", "description": "Full day name, e.g. 'Monday', 'Thursday'"},
                    "time": {"type": "string", "description": "Time string, e.g. '9am', '2pm', '14:00'"},
                },
                "required": ["lab", "day", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "find_free_labs",
            "description": (
                "Find all labs that are free on a given day and time. "
                "Use this when the user asks 'which labs are free' or needs alternatives."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "day":  {"type": "string", "description": "Full day name, e.g. 'Monday', 'Thursday'"},
                    "time": {"type": "string", "description": "Time string, e.g. '9am', '11am', '3pm'"},
                },
                "required": ["day", "time"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "book_lab",
            "description": (
                "Book a lab for a teacher at a specific day and time. "
                "This saves the booking permanently. Only call after user confirms intent."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lab":     {"type": "string", "description": "Lab ID to book, e.g. '109'"},
                    "day":     {"type": "string", "description": "Full day name, e.g. 'Friday'"},
                    "time":    {"type": "string", "description": "Time, e.g. '3pm'"},
                    "teacher": {"type": "string", "description": "Teacher's full name, e.g. 'Mr. Ahmed'"},
                },
                "required": ["lab", "day", "time", "teacher"],
            },
        },
    },
]

# Maps tool name → actual Python function
TOOL_DISPATCH = {
    "check_lab_status": check_lab_status,
    "find_free_labs":   find_free_labs,
    "book_lab":         book_lab,
}

# ---------------------------------------------------------------------------
# System prompt (schedule context is injected at call time)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """\
You are a helpful Lab Scheduling Assistant for SAIT (South Asian Institute of Technology).
You help institute staff check lab availability and make bookings.

RULES:
1. Always call the appropriate tool to verify real-time data before answering.
2. State FREE or BUSY clearly and prominently.
3. If a lab is BUSY, name who is using it and suggest free alternatives.
4. If a booking succeeds, confirm: lab number, day, time slot, teacher name.
5. If user says "morning" assume 9am (slot B). "Afternoon" assume 1pm (slot D). "Evening" assume 5pm (slot F).
6. If the day or time is ambiguous, ask the user to clarify before calling a tool.
7. Days run Monday–Saturday. Sunday is not a working lab day.
8. Never fabricate schedule data — always use the tools.

{schedule_summary}
"""

# Keep at most this many prior exchanges to avoid exceeding context limits
MAX_HISTORY_PAIRS = 6


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_agent(user_message: str, conversation_history: list) -> str:
    """
    Process one user message and return the assistant's reply.

    Args:
        user_message:         The latest text from the user.
        conversation_history: List of prior {"role": ..., "content": ...} dicts
                              (only user/assistant pairs, no tool messages).

    Returns:
        The agent's final natural-language reply as a string.
    """
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. "
            "Add it to a .env file or export it as an environment variable."
        )

    client = Groq(api_key=api_key)

    # Truncate history to stay within token budget
    trimmed_history = conversation_history[-(MAX_HISTORY_PAIRS * 2):]

    # Build the full message list for this API call
    system_content = SYSTEM_PROMPT_TEMPLATE.format(
        schedule_summary=get_schedule_summary()
    )
    messages: list[dict] = [{"role": "system", "content": system_content}]
    messages.extend(trimmed_history)
    messages.append({"role": "user", "content": user_message})

    # -----------------------------------------------------------------
    # Agentic loop: call Groq → execute tools → repeat until final reply
    # -----------------------------------------------------------------
    while True:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,     # low temp for factual scheduling answers
            max_tokens=1024,
        )

        assistant_msg = response.choices[0].message

        # No tool calls → model has produced the final answer
        if not assistant_msg.tool_calls:
            return assistant_msg.content or "(no response)"

        # Append the assistant turn (with tool_calls) to the working message list
        messages.append({
            "role": "assistant",
            "content": assistant_msg.content,  # may be None or a preamble
            "tool_calls": [
                {
                    "id":   tc.id,
                    "type": "function",
                    "function": {
                        "name":      tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in assistant_msg.tool_calls
            ],
        })

        # Execute every requested tool and feed results back
        for tool_call in assistant_msg.tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                func_args = {}

            if func_name in TOOL_DISPATCH:
                result = TOOL_DISPATCH[func_name](**func_args)
            else:
                result = {"error": f"Unknown tool '{func_name}'"}

            messages.append({
                "role":         "tool",
                "tool_call_id": tool_call.id,
                "content":      json.dumps(result),
            })

        # Loop back to get the model's next response (may include more tool calls
        # or may be the final answer)
