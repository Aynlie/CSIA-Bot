"""
bot_state.py — small persisted values the bot needs to survive a restart.

Same JSON-file pattern as attendance_store.py / registration_store.py.
Currently holds just the verification message ID, but any other small
piece of runtime state that used to live in a bare module-level variable
(and therefore silently reset on every restart) belongs here too.
"""

import json
import os

DATA_FILE = os.path.join(os.path.dirname(__file__), "bot_state.json")


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
        json.dump(data, f, indent=2)


def set_verification_message_id(message_id: int) -> None:
    data = _load()
    data["verification_message_id"] = message_id
    _save(data)


def get_verification_message_id() -> int | None:
    return _load().get("verification_message_id")