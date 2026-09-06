"""
test_stores.py — automated tests for attendance_store.py and registration_store.py

These are the two modules the bot critique flagged as having "no automated
safety net." Both are pure, storage-agnostic functions with no discord.py
dependency, so they're testable without mocking Discord at all — that's
exactly why they were built this way.

RUN THESE BEFORE PUSHING ANY CHANGE to attendance_store.py or
registration_store.py:

    python -m pytest test_stores.py -v

or, if pytest isn't installed:

    pip install pytest --break-system-packages
    python -m pytest test_stores.py -v

Each test uses a temporary data file (via monkeypatching DATA_FILE) so
these tests NEVER touch your real attendance.json / registrations.json.
"""

import os
import sys
import tempfile
import importlib

import pytest

sys.path.insert(0, os.path.dirname(__file__))


@pytest.fixture
def attendance_store(tmp_path, monkeypatch):
    """Fresh attendance_store module pointed at a throwaway temp file."""
    import attendance_store as mod
    importlib.reload(mod)
    temp_file = tmp_path / "attendance_test.json"
    monkeypatch.setattr(mod, "DATA_FILE", str(temp_file))
    return mod


@pytest.fixture
def registration_store(tmp_path, monkeypatch):
    """Fresh registration_store module pointed at a throwaway temp file."""
    import registration_store as mod
    importlib.reload(mod)
    temp_file = tmp_path / "registrations_test.json"
    monkeypatch.setattr(mod, "DATA_FILE", str(temp_file))
    return mod


# ── attendance_store ────────────────────────────────────────────────

def test_record_attendance_first_time_is_new(attendance_store):
    count, is_new = attendance_store.record_attendance(111, "Linux Fundamentals")
    assert count == 1
    assert is_new is True


def test_record_attendance_duplicate_event_not_new(attendance_store):
    attendance_store.record_attendance(111, "Linux Fundamentals")
    count, is_new = attendance_store.record_attendance(111, "Linux Fundamentals")
    assert count == 1  # unchanged
    assert is_new is False


def test_record_attendance_duplicate_is_case_insensitive(attendance_store):
    attendance_store.record_attendance(111, "Linux Fundamentals")
    count, is_new = attendance_store.record_attendance(111, "LINUX FUNDAMENTALS")
    assert count == 1
    assert is_new is False


def test_record_attendance_strips_stray_quotes(attendance_store):
    # Regression test: earlier attendance.json entries had literal quote
    # characters saved inside the event name (e.g. "Test event" with the
    # quotes actually part of the string). New entries should not repeat this.
    attendance_store.record_attendance(111, '"Linux Fundamentals"')
    history = attendance_store.get_event_history(111)
    assert history[0]["event"] == "Linux Fundamentals"


def test_get_attendance_count_zero_for_unknown_user(attendance_store):
    assert attendance_store.get_attendance_count(999) == 0


def test_get_event_history_empty_for_unknown_user(attendance_store):
    assert attendance_store.get_event_history(999) == []


def test_multiple_different_events_all_count(attendance_store):
    attendance_store.record_attendance(111, "Event A")
    attendance_store.record_attendance(111, "Event B")
    count, _ = attendance_store.record_attendance(111, "Event C")
    assert count == 3


def test_corrupted_json_file_does_not_crash(attendance_store):
    with open(attendance_store.DATA_FILE, "w") as f:
        f.write("{not valid json!!!")
    # _load() should recover gracefully instead of raising
    assert attendance_store.get_attendance_count(111) == 0


# ── registration_store ──────────────────────────────────────────────

def test_save_and_get_registration(registration_store):
    registration_store.save_registration(
        222, "Test User", "test@gmail.com", "test@student.hau.edu.ph", True
    )
    reg = registration_store.get_registration(222)
    assert reg["full_name"] == "Test User"
    assert reg["is_linux_attendee"] is True
    assert "wants_membership" not in reg  # membership tracked externally now


def test_has_registered_false_for_unknown_user(registration_store):
    assert registration_store.has_registered(999) is False


def test_has_registered_true_after_save(registration_store):
    registration_store.save_registration(222, "Test User", "test@gmail.com", "", False)
    assert registration_store.has_registered(222) is True


def test_update_registration_field_on_existing_user(registration_store):
    registration_store.save_registration(222, "Test User", "old@gmail.com", "", False)
    updated = registration_store.update_registration_field(222, "personal_email", "new@gmail.com")
    assert updated is True
    assert registration_store.get_registration(222)["personal_email"] == "new@gmail.com"


def test_update_registration_field_on_unknown_user_returns_false(registration_store):
    updated = registration_store.update_registration_field(999, "full_name", "Nobody")
    assert updated is False


def test_get_all_registrations_returns_everyone(registration_store):
    registration_store.save_registration(1, "User One", "one@gmail.com", "", True)
    registration_store.save_registration(2, "User Two", "two@gmail.com", "", False)
    all_regs = registration_store.get_all_registrations()
    assert len(all_regs) == 2
    assert "1" in all_regs and "2" in all_regs


def test_email_regex_rejects_not_at_real(registration_store):
    # This is the exact gap flagged in the bot critique — a bare "@" in
    # personal" check let strings like "not@real" through as "valid."
    import welcome_events
    assert welcome_events.is_valid_email("not@real") is False
    assert welcome_events.is_valid_email("santosjaymee13@gmail.com") is True