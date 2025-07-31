python
import logging

from flask import Blueprint, abort, jsonify, request, Response
from marshmallow import ValidationError

import services.event_service as event_service
from schemas import EventCreateSchema

logger = logging.getLogger(__name__)

events_bp = Blueprint("events", __name__)


@events_bp.route("/events", methods=["POST"])
def create_event() -> Response:
    """
    Create a new event.

    Expects JSON payload:
    {
        "name": "<event_name>"
    }

    Returns:
        JSON with {"event_id": <id>} and HTTP 201.
    """
    payload = request.get_json()
    if payload is None:
        logger.error("No JSON payload provided")
        abort(400, "Invalid JSON payload")

    try:
        data = EventCreateSchema().load(payload)
    except ValidationError:
        raise

    logger.info(f"Creating event with name={data['name']}")
    new_event = event_service.create_event(data["name"])
    logger.info(f"Event created with id={new_event.event_id}")

    return jsonify({"event_id": new_event.event_id}), 201
