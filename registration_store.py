"""
registration_store.py — CSIA Cyberfox bot: welcome-channel registration data

Same JSON-file pattern as attendance_store.py, so it's a drop-in that fits
the rest of the project without introducing a new storage approach.
"""

import json
import os
from datetime import datetime, timezone

DATA_FILE = os.path.join(os.path.dirname(__file__), "registrations.json")


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


def save_registration(user_id: int, full_name: str, personal_email: str,
                       hau_email: str, is_linux_attendee: bool,
                       wants_membership: bool = False) -> None:
    data = _load()
    data[str(user_id)] = {
        "full_name": full_name,
        "personal_email": personal_email,
        "hau_email": hau_email,
        "is_linux_attendee": is_linux_attendee,
        "wants_membership": wants_membership,
        "submitted_at": datetime.now(timezone.utc).isoformat(),
    }
    _save(data)


def get_registration(user_id: int):
    """Returns the registration dict for this user, or None if not registered."""
    return _load().get(str(user_id))


def has_registered(user_id: int) -> bool:
    return get_registration(user_id) is not None


def get_all_registrations() -> dict:
    """Officer/export use — returns the full {user_id: registration} dict."""
    return _load()


def update_registration_field(user_id: int, field: str, value) -> bool:
    """
    Updates a single field on an existing registration. Returns True if the
    user had a registration to update, False otherwise (nothing is created —
    use save_registration() for that).
    """
    data = _load()
    uid = str(user_id)
    if uid not in data:
        return False
    data[uid][field] = value
    _save(data)
    return True