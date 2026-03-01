from flask import Blueprint, request, jsonify


student_bp = Blueprint("student", __name__)


@student_bp.route("/validate_details", methods=["POST"])
def validate_details():   
    details = request.get_json()
    if not isinstance(details, dict):
        return jsonify({"error": "Invalid details data or format"}), 400

    try:
        current = float(details.get("currentGPA", 4.5))
        goal = float(details.get("goalGPA", 4.0))
    except ValueError:
        return jsonify({"error": "Invalid details provided"}), 400
    
    if current < 0 or current > 7 or goal < 0 or goal > 7:
        return jsonify({"error": "Invalid GPA. Values must be between 0.0 and 7.0"}), 400

    return jsonify({"message": "Student details are valid"}), 200