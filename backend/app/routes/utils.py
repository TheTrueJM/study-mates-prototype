from flask import Blueprint, session, jsonify
from flask_login import current_user

util_bp = Blueprint("main", __name__)


@util_bp.route("/session", methods=["GET"])
def get_session():
    # Check if staff is authenticated
    if current_user.is_authenticated:

    # Check if student has details set
    if session.get("currentGPA") is not None and session.get("goalGPA") is not None:
        details = {
            "currentGPA": session.get("currentGPA"),
            "goalGPA": session.get("goalGPA"),
            "availability": session.get("availability", []),
        }
        }), 200

    # No valid session
    return "", 204
