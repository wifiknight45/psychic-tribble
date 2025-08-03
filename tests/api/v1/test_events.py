import pytest
from fastapi import status
from datetime import datetime, timedelta

# Helper to create a user before creating events
def create_test_user(client):
    payload = {"name": "Event Host", "email": "host@example.com"}
    resp = client.post("/api/v1/users", json=payload)
    return resp.json()["id"]

def iso_now(offset_hours=0):
    return (datetime.utcnow() + timedelta(hours=offset_hours)).isoformat()

def test_list_events_empty(client):
    response = client.get("/api/v1/events")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert response.json() == []

def test_create_event_success(client):
    host_id = create_test_user(client)
    payload = {
        "title": "Team Sync",
        "description": "Weekly project update",
        "start_time": iso_now(1),
        "end_time": iso_now(2),
        "host_id": host_id
    }
    resp = client.post("/api/v1/events", json=payload)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["host_id"] == host_id

def test_create_event_missing_title(client):
    host_id = create_test_user(client)
    payload = {
        "description": "No title here",
        "start_time": iso_now(1),
        "end_time": iso_now(2),
        "host_id": host_id
    }
    resp = client.post("/api/v1/events", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_event_success(client):
    host_id = create_test_user(client)
    create_payload = {
        "title": "Board Meeting",
        "description": "Annual financial review",
        "start_time": iso_now(1),
        "end_time": iso_now(3),
        "host_id": host_id
    }
    event_id = client.post("/api/v1/events", json=create_payload).json()["id"]

    resp = client.get(f"/api/v1/events/{event_id}")
    assert resp.status_code == status.HTTP_200_OK
    event = resp.json()
    assert event["id"] == event_id
    assert event["title"] == create_payload["title"]

def test_get_event_not_found(client):
    resp = client.get("/api/v1/events/999999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND

def test_update_event_success(client):
    host_id = create_test_user(client)
    create_payload = {
        "title": "Sprint Planning",
        "description": "Plan tasks for sprint",
        "start_time": iso_now(1),
        "end_time": iso_now(2),
        "host_id": host_id
    }
    event_id = client.post("/api/v1/events", json=create_payload).json()["id"]

    update_payload = {"title": "Sprint Retrospective"}
    resp = client.put(f"/api/v1/events/{event_id}", json=update_payload)
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json()["title"] == "Sprint Retrospective"

def test_delete_event_success(client):
    host_id = create_test_user(client)
    create_payload = {
        "title": "One-off Workshop",
        "description": "Hands-on lab",
        "start_time": iso_now(1),
        "end_time": iso_now(2),
        "host_id": host_id
    }
    event_id = client.post("/api/v1/events", json=create_payload).json()["id"]

    del_resp = client.delete(f"/api/v1/events/{event_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Confirm deletion
    assert client.get(f"/api/v1/events/{event_id}").status_code == status.HTTP_404_NOT_FOUND

def test_delete_event_not_found(client):
    resp = client.delete("/api/v1/events/888888")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
