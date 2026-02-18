from flask import Blueprint, session, request, jsonify
from app.enums import parse_availability


student_bp = Blueprint("student", __name__)


@student_bp.route("/details", methods=["POST"])
def details():   
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid details data or format"}), 400

    try:
        current = float(data.get("currentGPA", 4.5))
        current = max(0, min(current, 7))
        goal = float(data.get("goalGPA", 4.0))
        goal = max(0, min(goal, 7))
        availability = parse_availability(data.get("availability"))
    except ValueError:
        return jsonify({"error": "Invalid details provided"}), 400

    session["currentGPA"] = current
    session["goalGPA"] = goal
    session["availability"] = availability
    return jsonify({"message": "Student details set"}), 200


@student_bp.route("/join/<code>", methods=["POST"])
def join_tutorial(code):
    if not code:
        return jsonify({"error": "Invalid tutorial code"}), 400
    
    if session.get("currentGPA") is None or session.get("goalGPA")  is None or session.get("availability") is None:
        return jsonify({"error": "Must set details before joining tutorial"}), 400

    session["tutorial_code"] = code
    session["role"] = "student"
    return jsonify({"message": "Tutorial code set"}), 200