"""
ticket_store.py — CSIA Cyberfox bot: support ticket tracking

Same JSON-file pattern as attendance_store.py / registration_store.py, so
it's a drop-in that fits the rest of the project. Tracks which Discord
channel belongs to which open ticket, so the bot can:
  1. stop a member from opening a second ticket while one is already open
  2. know who opened a channel (and its ticket number) when it gets closed

Closed tickets are removed from this file, not kept forever — the ticket
channel itself gets deleted on close, so there's nothing left to look up
locally anyway. If you want a permanent record of past tickets, set
config.TICKET_LOG_CHANNEL_ID — a summary embed gets posted there on every
close, before the record here is dropped.
"""

import json
import os
from datetime import datetime, timezone

DATA_FILE = os.path.join(os.path.dirname(__file__), "tickets.json")


def _default() -> dict:
    return {"tickets": {}, "next_number": 1}


def _load() -> dict:
    if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
        return _default()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _default()
    data.setdefault("tickets", {})
    data.setdefault("next_number", 1)
    return data


def _save(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def create_ticket(channel_id: int, opener_id: int) -> int:
    """Records a new open ticket for channel_id. Returns its ticket number."""
    data = _load()
    number = data["next_number"]
    data["tickets"][str(channel_id)] = {
        "opener_id": opener_id,
        "number": number,
        "opened_at": datetime.now(timezone.utc).isoformat(),
    }
    data["next_number"] = number + 1
    _save(data)
    return number


def get_ticket(channel_id: int) -> dict | None:
    """Returns the ticket record for this channel, or None."""
    return _load()["tickets"].get(str(channel_id))


def get_open_ticket_channel_id(opener_id: int) -> int | None:
    """Returns the channel_id of opener_id's open ticket, or None if they
    don't have one. Used to block opening a second ticket at once."""
    for channel_id, ticket in _load()["tickets"].items():
        if ticket["opener_id"] == opener_id:
            return int(channel_id)
    return None


def close_ticket(channel_id: int) -> dict | None:
    """Removes the ticket record for channel_id and returns it, or None if
    there wasn't one (e.g. already closed, or not a ticket channel)."""
    data = _load()
    ticket = data["tickets"].pop(str(channel_id), None)
    if ticket is not None:
        _save(data)
    return ticket


def get_all_open_tickets() -> dict:
    """Officer use — returns the full {channel_id: ticket} dict."""
    return _load()["tickets"]