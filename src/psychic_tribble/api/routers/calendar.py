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
