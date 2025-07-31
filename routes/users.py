import logging

from flask import Blueprint, abort, jsonify, request, Response
from marshmallow import ValidationError

import services.user_service as user_service
from schemas import UserCreateSchema

logger = logging.getLogger(__name__)

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["POST"])
def create_user() -> Response:
    """
    Create a new user.

    Expects JSON payload:
    {
        "name": "<user_name>"
    }

    Returns:
        JSON with {"user_id": <id>} and HTTP 201.
    """
    payload = request.get_json()
    if payload is None:
        logger.error("No JSON payload provided")
        abort(400, "Invalid JSON payload")

    try:
        data = UserCreateSchema().load(payload)
    except ValidationError as err:
        # Let the centralized ValidationError handler catch this
        raise

    logger.info(f"Creating user with name={data['name']}")
    new_user = user_service.create_user(data["name"])
    logger.info(f"User created with id={new_user.user_id}")

    return jsonify({"user_id": new_user.user_id}), 201
