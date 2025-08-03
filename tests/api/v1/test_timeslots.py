import pytest
from fastapi import status
from datetime import datetime, timedelta

# Helpers to create prerequisites
def iso_now(offset_minutes=0):
    return (datetime.utcnow() + timedelta(minutes=offset_minutes)).isoformat()

def create_test_user(client):
    payload = {"name": "Slot User", "email": "slot@example.com"}
    return client.post("/api/v1/users", json=payload).json()["id"]

def create_test_event(client, host_id):
    payload = {
        "title": "Slot Event",
        "description": "Event for slots",
        "start_time": iso_now(10),
        "end_time": iso_now(70),
        "host_id": host_id
    }
    return client.post("/api/v1/events", json=payload).json()["id"]

def test_list_timeslots_empty(client):
    response = client.get("/api/v1/timeslots")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

def test_create_timeslot_success(client):
    user_id = create_test_user(client)
    event_id = create_test_event(client, user_id)
    payload = {
        "event_id": event_id,
        "start_time": iso_now(15),
        "end_time": iso_now(30)
    }
    resp = client.post("/api/v1/timeslots", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert "id" in data
    assert data["event_id"] == event_id

def test_create_timeslot_missing_times(client):
    user_id = create_test_user(client)
    event_id = create_test_event(client, user_id)
    payload = {"event_id": event_id}
    resp = client.post("/api/v1/timeslots", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_timeslot_success(client):
    user_id = create_test_user(client)
    event_id = create_test_event(client, user_id)
    create_resp = client.post("/api/v1/timeslots", json={
        "event_id": event_id,
        "start_time": iso_now(20),
        "end_time": iso_now(40)
    })
    slot_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/timeslots/{slot_id}")
    assert resp.status_code == status.HTTP_200_OK
    ts = resp.json()
    assert ts["id"] == slot_id
    assert ts["event_id"] == event_id

def test_get_timeslot_not_found(client):
    resp = client.get("/api/v1/timeslots/999999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND

def test_update_timeslot_success(client):
    user_id = create_test_user(client)
    event_id = create_test_event(client, user_id)
    slot_id = client.post("/api/v1/timeslots", json={
        "event_id": event_id,
        "start_time": iso_now(25),
        "end_time": iso_now(35)
    }).json()["id"]

    update_payload = {"end_time": iso_now(45)}
    resp = client.put(f"/api/v1/timeslots/{slot_id}", json=update_payload)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["end_time"] == update_payload["end_time"]

def test_delete_timeslot_success(client):
    user_id = create_test_user(client)
    event_id = create_test_event(client, user_id)
    slot_id = client.post("/api/v1/timeslots", json={
        "event_id": event_id,
        "start_time": iso_now(30),
        "end_time": iso_now(50)
    }).json()["id"]

    del_resp = client.delete(f"/api/v1/timeslots/{slot_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Confirm deletion
    assert client.get(f"/api/v1/timeslots/{slot_id}").status_code == status.HTTP_404_NOT_FOUND

def test_delete_timeslot_not_found(client):
    resp = client.delete("/api/v1/timeslots/888888")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
