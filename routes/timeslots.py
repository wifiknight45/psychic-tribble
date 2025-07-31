import logging

from flask import Blueprint, abort, jsonify, request, Response
from marshmallow import ValidationError

import services.timeslot_service as timeslot_service
from schemas import TimeslotCreateSchema, AssignmentSchema

logger = logging.getLogger(__name__)

timeslots_bp = Blueprint("timeslots", __name__)


@timeslots_bp.route("/events/<event_id>/timeslots", methods=["POST"])
def add_timeslot(event_id: str) -> Response:
    """
    Add a new timeslot to an event.

    URL parameter:
        event_id: ID of the event

    Expects JSON payload:
    {
        "day": "<YYYY-MM-DD>",
        "start": "<HH:MM>",
        "end": "<HH:MM>"
    }

    Returns:
        JSON with {"timeslot_id": <id>} and HTTP 201.
    """
    payload = request.get_json()
    if payload is None:
        logger.error("No JSON payload provided")
        abort(400, "Invalid JSON payload")

    try:
        data = TimeslotCreateSchema().load(payload)
    except ValidationError:
        raise

    logger.info(
        f"Adding timeslot to event={event_id} day={data['day']} "
        f"start={data['start']} end={data['end']}"
    )

    try:
        ts = timeslot_service.add_timeslot(
            event_id, data["day"], data["start"], data["end"]
        )
    except KeyError:
        logger.error(f"Event not found: {event_id}")
        abort(404, "Event not found")
    except ValueError as exc:
        logger.error(f"Invalid timeslot data: {exc}")
        abort(400, str(exc))

    logger.info(f"Timeslot created with id={ts.ts_id}")
    return jsonify({"timeslot_id": ts.ts_id}), 201


@timeslots_bp.route("/timeslots/<ts_id>/assign", methods=["POST"])
def assign_to_slot(ts_id: str) -> Response:
    """
    Assign a user to an existing timeslot.

    URL parameter:
        ts_id: ID of the timeslot

    Expects JSON payload:
    {
        "user_id": "<user_id>"
    }

    Returns:
        JSON with a success message and HTTP 200.
    """
    payload = request.get_json()
    if payload is None:
        logger.error("No JSON payload provided")
        abort(400, "Invalid JSON payload")

    try:
        data = AssignmentSchema().load(payload)
    except ValidationError:
        raise

    logger.info(f"Assigning user={data['user_id']} to timeslot={ts_id}")
    try:
        timeslot_service.assign_user(ts_id, data["user_id"])
    except KeyError as exc:
        logger.error(f"Assignment failed: {exc}")
        abort(404, str(exc))

    logger.info(f"User {data['user_id']} assigned to {ts_id}")
    return jsonify({"message": "Assigned successfully"}), 200
