import logging

from flask import Blueprint, jsonify, Response

import services.calendar_service as calendar_service

logger = logging.getLogger(__name__)

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.route("/calendar", methods=["GET"])
def view_calendar() -> Response:
    """
    Retrieve the full calendar with all events and timeslots.

    Returns:
        JSON calendar object and HTTP 200.
    """
    logger.info("Building full calendar")
    cal = calendar_service.build_calendar()
    logger.info("Calendar built successfully")
    return jsonify(cal), 200
tests/test_users.py
python
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
