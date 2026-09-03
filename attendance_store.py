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


def _load() -> dict:
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def record_attendance(user_id: int, event_name: str) -> tuple[int, bool]:
    """
    Records that user_id attended event_name.
    Returns a tuple of (new_event_count, is_new_record).
    If the event was already recorded for this user, returns (current_count, False).
    """
    clean_event = event_name.strip().strip("\"'")
    data = _load()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"events": []}

    # Check for existing attendance for the same event name (case-insensitive)
    already_attended = any(
        e.get("event", "").strip().lower() == clean_event.lower()
        for e in data[uid]["events"]
    )
    if already_attended:
        return len(data[uid]["events"]), False

    data[uid]["events"].append({
        "event": clean_event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _save(data)
    return len(data[uid]["events"]), True


def get_attendance_count(user_id: int) -> int:
    data = _load()
    uid = str(user_id)
    if uid not in data:
        return 0
    return len(data[uid]["events"])


def get_event_history(user_id: int) -> list[dict]:
    data = _load()
    uid = str(user_id)
    if uid not in data:
        return []
    return data[uid]["events"]