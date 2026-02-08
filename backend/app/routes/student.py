from flask import Blueprint, session, request, redirect, url_for, send_file, render_template
import os
from app.enums import get_availability_code, Day, TimePeriod, parse_availability


student_bp = Blueprint("student", __name__)


@student_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        code = request.form.get("code")
        name = request.form.get("name") # Generate Random on Frontend, Here, or Socket-Server?
        session["tutorial_code"] = code
        session["name"] = name
        return redirect(url_for("student.details"))

    client_path = os.path.join(os.getcwd(), "../frontend/public/student/index.html")
    return send_file(client_path)


@student_bp.route("/details", methods=["GET", "POST"])
def details():
    if not session.get("tutorial_code"):
        return redirect(url_for("student.index"))

    if request.method == "POST":
        session["currentGPA"] = float(request.form.get("currentGPA", 0.0))
        session["goalGPA"] = float(request.form.get("goalGPA", 4.0))
        # e.g form output: ['MONM', 'WEDA', 'THUA', 'FRIA', 'SUNN']
        availability_list = request.form.getlist("availability")
        session["availability"] = list(parse_availability(availability_list))
        return redirect(url_for("student.tutorial", code=session["tutorial_code"]))

    client_path = os.path.join(os.getcwd(), "../frontend/public/student/details.html")
    return send_file(client_path)


@student_bp.route("/tutorial/<code>", methods=["GET"])
def tutorial(code):
    ## To-Do: Kick back to Index if Tutorial doesn't exist on server
    if not session.get("tutorial_code"):
        return redirect(url_for("student.index"))

    session["role"] = "student"

    client_path = os.path.join(os.getcwd(), "../frontend/public/student/tutorial.html")
    return send_file(client_path)
