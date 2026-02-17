from flask import Blueprint, session, request, redirect, url_for, send_file, render_template, jsonify
import os
from app.enums import get_availability_code, Day, TimePeriod, parse_availability


student_bp = Blueprint("student", __name__)


@student_bp.route("/join/<code>", methods=["POST"])
def join_tutorial(code):
    if not code:
        return jsonify({"error": "Invalid tutorial code"}), 400

    session["tutorial_code"] = code
    return jsonify({"message": "Tutorial code set"}), 200


@student_bp.route("/details", methods=["GET", "POST"])
def details():
    # Require that the tutorial code is present in session before accessing details
    if not session.get("tutorial_code"):
        return redirect(url_for("student.index"))

    if request.method == "POST":
        try:
            current = float(request.form.get("currentGPA", 0.0))
            goal = float(request.form.get("goalGPA", 4.0))
        except ValueError:
            return redirect(url_for("student.details"))

        availability_list = request.form.getlist("availability")
        session["currentGPA"] = current
        session["goalGPA"] = goal
        session["availability"] = list(parse_availability(availability_list))
        session["attributes_confirmed"] = True
        return redirect(url_for("student.tutorial", code=session["tutorial_code"]))

    client_path = os.path.join(os.getcwd(), "../frontend/public/student/details.html")
    return send_file(client_path)


@student_bp.route("/tutorial/<code>", methods=["GET"])
def tutorial(code):
    ## To-Do: Kick back to Index if Tutorial doesn't exist on server
    # Must have joined a tutorial and confirmed attributes
    if not session.get("tutorial_code"):
        return redirect(url_for("student.index"))

    if not session.get("attributes_confirmed"):
        return redirect(url_for("student.details"))

    session["role"] = "student"

    client_path = os.path.join(os.getcwd(), "../frontend/public/student/tutorial.html")
    return send_file(client_path)