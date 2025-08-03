import pytest
from fastapi import status

# client is provided by tests/conftest.py
def test_create_user_success(client):
    payload = {"name": "Alice", "email": "alice@example.com"}
    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "id" in data
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"

def test_create_user_missing_email(client):
    payload = {"name": "Bob"}
    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_get_user_success(client):
    # First, create
    payload = {"name": "Carol", "email": "carol@example.com"}
    create_resp = client.post("/api/v1/users", json=payload)
    user_id = create_resp.json()["id"]

    # Then, retrieve
    get_resp = client.get(f"/api/v1/users/{user_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    user = get_resp.json()
    assert user["id"] == user_id
    assert user["email"] == payload["email"]

def test_get_user_not_found(client):
    response = client.get("/api/v1/users/999999")
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_update_user_success(client):
    payload = {"name": "Dave", "email": "dave@example.com"}
    user_id = client.post("/api/v1/users", json=payload).json()["id"]

    update_payload = {"name": "David"}
    update_resp = client.put(f"/api/v1/users/{user_id}", json=update_payload)
    assert update_resp.status_code == status.HTTP_200_OK
    assert update_resp.json()["name"] == "David"

def test_delete_user_success(client):
    payload = {"name": "Eve", "email": "eve@example.com"}
    user_id = client.post("/api/v1/users", json=payload).json()["id"]

    del_resp = client.delete(f"/api/v1/users/{user_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Confirm deletion
    assert client.get(f"/api/v1/users/{user_id}").status_code == status.HTTP_404_NOT_FOUND

def test_delete_user_not_found(client):
    response = client.delete("/api/v1/users/888888")
    assert response.status_code == status.HTTP_404_NOT_FOUND
