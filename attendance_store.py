"""
Simple JSON-backed attendance tracker.
Swap this out for a real database later if CSIA outgrows it —
the rest of the bot only talks to the functions below, so the
storage backend can change without touching bot.py.
"""

import json
import os
from datetime import datetime, timezone

DATA_FILE = os.path.join(os.path.dirname(__file__), "attendance.json")


def _load():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_attendance(user_id: int, event_name: str) -> int:
    """
    Records that user_id attended event_name.
    Returns the member's new total event count.
    """
    data = _load()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"events": []}

    data[uid]["events"].append({
        "event": event_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save(data)
    return len(data[uid]["events"])


def get_attendance_count(user_id: int) -> int:
    data = _load()
    uid = str(user_id)
    if uid not in data:
        return 0
    return len(data[uid]["events"])


def get_event_history(user_id: int):
    data = _load()
    uid = str(user_id)
    if uid not in data:
        return []
    return data[uid]["events"]