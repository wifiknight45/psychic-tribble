# i. tests/test_users.py
import pytest
from flask import Response

from app import create_app


class DummyUser:
    def __init__(self, uid):
        self.user_id = uid


@pytest.fixture
def client(monkeypatch):
    # Patch the service layer before creating the app
    monkeypatch.setattr(
        "routes.users.user_service.create_user",
        lambda name: DummyUser("u-123")
    )
    app = create_app()
    return app.test_client()


def test_create_user_success(client):
    response: Response = client.post("/users", json={"name": "Alice"})
    assert response.status_code == 201
    payload = response.get_json()
    assert payload == {"user_id": "u-123"}


def test_create_user_missing_name(client):
    response: Response = client.post("/users", json={})
    assert response.status_code == 400
    error = response.get_json().get("error")
    assert "name" in error

# ii. tests/test_events.py
import pytest
from flask import Response

from app import create_app


class DummyEvent:
    def __init__(self, eid):
        self.event_id = eid


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        "routes.events.event_service.create_event",
        lambda name: DummyEvent("e-456")
    )
    app = create_app()
    return app.test_client()


def test_create_event_success(client):
    response: Response = client.post("/events", json={"name": "Party"})
    assert response.status_code == 201
    assert response.get_json() == {"event_id": "e-456"}


def test_create_event_missing_name(client):
    response: Response = client.post("/events", json={})
    assert response.status_code == 400

# iii. tests/test_timeslots.pyy
import pytest
from flask import Response

from app import create_app


class DummyTimeslot:
    def __init__(self, ts_id):
        self.ts_id = ts_id


@pytest.fixture
def client(monkeypatch):
    # Default happy‐path
    monkeypatch.setattr(
        "routes.timeslots.timeslot_service.add_timeslot",
        lambda eid, d, s, e: DummyTimeslot("ts-789")
    )
    monkeypatch.setattr(
        "routes.timeslots.timeslot_service.assign_user",
        lambda ts_id, uid: None
    )
    app = create_app()
    return app.test_client()


def test_add_timeslot_success(client):
    payload = {"day": "2025-08-01", "start": "09:00", "end": "11:00"}
    resp: Response = client.post("/events/ev-1/timeslots", json=payload)
    assert resp.status_code == 201
    assert resp.get_json() == {"timeslot_id": "ts-789"}


def test_add_timeslot_event_not_found(client, monkeypatch):
    def raise_key(eid, d, s, ed):
        raise KeyError("Event not found")

    monkeypatch.setattr(
        "routes.timeslots.timeslot_service.add_timeslot",
        raise_key
    )
    payload = {"day": "2025-08-01", "start": "09:00", "end": "11:00"}
    resp: Response = client.post("/events/ev-42/timeslots", json=payload)
    assert resp.status_code == 404


def test_assign_to_slot_success(client):
    resp: Response = client.post("/timeslots/ts-789/assign", json={"user_id": "u-123"})
    assert resp.status_code == 200
    assert resp.get_json() == {"message": "Assigned successfully"}


def test_assign_to_slot_user_not_found(client, monkeypatch):
    def raise_key(ts_id, uid):
        raise KeyError("User not found")

    monkeypatch.setattr(
        "routes.timeslots.timeslot_service.assign_user",
        raise_key
    )
    resp: Response = client.post("/timeslots/ts-789/assign", json={"user_id": "u-999"})
    assert resp.status_code == 404

# iv. tests/test_calendar.py
import pytest
from flask import Response

from app import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        "routes.calendar.calendar_service.build_calendar",
        lambda: {"events": [], "timeslots": []}
    )
    app = create_app()
    return app.test_client()


def test_view_calendar_success(client):
    resp: Response = client.get("/calendar")
    assert resp.status_code == 200
    assert resp.get_json() == {"events": [], "timeslots": []}
