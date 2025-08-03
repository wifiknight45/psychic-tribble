# test_app.py

import pytest
from fastapi.testclient import TestClient

from psychic_tribble.app import create_app

# ─── Dummy DTOs ────────────────────────────────────────────────────────────────

class DummyUser:
    def __init__(self, user_id):
        self.user_id = user_id

class DummyEvent:
    def __init__(self, event_id):
        self.event_id = event_id

class DummyTimeslot:
    def __init__(self, timeslot_id):
        self.timeslot_id = timeslot_id

# ─── Shared TestClient Fixture ────────────────────────────────────────────────

@pytest.fixture
def client(monkeypatch):
    # Patch UserService.create_user
    monkeypatch.setattr(
        "psychic_tribble.routes.users.user_service.create_user",
        lambda data: DummyUser("u-123")
    )
    # Patch EventService.create_event
    monkeypatch.setattr(
        "psychic_tribble.routes.events.event_service.create_event",
        lambda data: DummyEvent("e-456")
    )
    # Patch TimeslotService methods
    monkeypatch.setattr(
        "psychic_tribble.routes.timeslots.timeslot_service.add_timeslot",
        lambda event_id, day, start, end: DummyTimeslot("ts-789")
    )
    monkeypatch.setattr(
        "psychic_tribble.routes.timeslots.timeslot_service.assign_user",
        lambda timeslot_id, user_id: None
    )
    # Patch CalendarService.build_calendar
    monkeypatch.setattr(
        "psychic_tribble.routes.calendar.calendar_service.build_calendar",
        lambda: {"events": [], "timeslots": []}
    )

    app = create_app()
    return TestClient(app)

# ─── User Tests ────────────────────────────────────────────────────────────────

def test_create_user_success(client):
    resp = client.post("/users", json={"name": "Alice"})
    assert resp.status_code == 201
    assert resp.json() == {"user_id": "u-123"}

def test_create_user_missing_name(client):
    resp = client.post("/users", json={})
    assert resp.status_code == 400
    assert "name" in resp.json().get("error", "")

# ─── Event Tests ───────────────────────────────────────────────────────────────

def test_create_event_success(client):
    resp = client.post("/events", json={"name": "Party"})
    assert resp.status_code == 201
    assert resp.json() == {"event_id": "e-456"}

def test_create_event_missing_name(client):
    resp = client.post("/events", json={})
    assert resp.status_code == 400

# ─── Timeslot Tests ───────────────────────────────────────────────────────────

def test_add_timeslot_success(client):
    payload = {"day": "2025-08-01", "start": "09:00", "end": "11:00"}
    resp = client.post("/events/ev-1/timeslots", json=payload)
    assert resp.status_code == 201
    assert resp.json() == {"timeslot_id": "ts-789"}

def test_add_timeslot_event_not_found(client, monkeypatch):
    def raise_event_not_found(eid, d, s, e):
        raise KeyError("Event not found")

    monkeypatch.setattr(
        "psychic_tribble.routes.timeslots.timeslot_service.add_timeslot",
        raise_event_not_found
    )
    payload = {"day": "2025-08-01", "start": "09:00", "end": "11:00"}
    resp = client.post("/events/ev-42/timeslots", json=payload)
    assert resp.status_code == 404

def test_assign_to_slot_success(client):
    resp = client.post("/timeslots/ts-789/assign", json={"user_id": "u-123"})
    assert resp.status_code == 200
    assert resp.json() == {"message": "Assigned successfully"}

def test_assign_to_slot_user_not_found(client, monkeypatch):
    def raise_user_not_found(ts_id, uid):
        raise KeyError("User not found")

    monkeypatch.setattr(
        "psychic_tribble.routes.timeslots.timeslot_service.assign_user",
        raise_user_not_found
    )
    resp = client.post("/timeslots/ts-789/assign", json={"user_id": "u-999"})
    assert resp.status_code == 404

# ─── Calendar Tests ───────────────────────────────────────────────────────────

def test_view_calendar_success(client):
    resp = client.get("/calendar")
    assert resp.status_code == 200
    assert resp.json() == {"events": [], "timeslots": []}
