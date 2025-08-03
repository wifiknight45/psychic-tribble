-------
├── core/test_utils.py ├── services/test_user_service.py ├── db/test_models.py └── conftest.py │ ├── core/ │ │ └── test_utils.py

import pytest
from fastapi import status
from datetime import datetime, timedelta

# --- Helpers ---

def iso_now(offset_hours: int = 0) -> str:
    return (datetime.utcnow() + timedelta(hours=offset_hours)).isoformat()

def create_test_user(client):
    payload = {"name": "Cal User", "email": "cal@example.com"}
    return client.post("/api/v1/users", json=payload).json()["id"]

def create_test_event(client, host_id, start_off=1, end_off=2):
    payload = {
        "title": "Calendar Event",
        "description": "Used in calendar tests",
        "start_time": iso_now(start_off),
        "end_time": iso_now(end_off),
        "host_id": host_id
    }
    return client.post("/api/v1/events", json=payload).json()["id"]

def create_test_timeslot(client, event_id, start_off=1, end_off=1.5):
    payload = {
        "event_id": event_id,
        "start_time": iso_now(start_off),
        "end_time": iso_now(end_off)
    }
    return client.post("/api/v1/timeslots", json=payload).json()["id"]

# --- Tests ---

def test_list_calendar_empty(client):
    resp = client.get("/api/v1/calendar")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []

def test_get_calendar_with_entries(client):
    # setup: user → event → timeslot
    user_id  = create_test_user(client)
    event_id = create_test_event(client, user_id)
    slot_id  = create_test_timeslot(client, event_id)

    resp = client.get("/api/v1/calendar")
    assert resp.status_code == status.HTTP_200_OK

    entries = resp.json()
    # Expect one calendar entry linking event + its timeslots
    assert isinstance(entries, list) and len(entries) == 1

    entry = entries[0]
    assert entry["event"]["id"] == event_id
    assert entry["event"]["host_id"] == user_id

    timeslots = entry.get("timeslots", [])
    assert any(ts["id"] == slot_id for ts in timeslots)

def test_get_calendar_invalid_date_filter(client):
    # invalid ISO‐8601 in query triggers 422
    resp = client.get("/api/v1/calendar?start_date=not-a-date")
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
