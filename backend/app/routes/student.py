from flask import Blueprint, session, request, redirect, url_for, send_file, render_template
import os
from ..database import db, Student



student_bp = Blueprint("student", __name__)


@student_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        code = request.form.get("code")
        name = request.form.get("name") # Generate Random on Frontend, Here, or Socket-Server?
        session["tutorial_code"] = code
        session["name"] = name
        student = Student(tutorial_code=code, username=name)
        db.session.add(student)
        db.session.commit()
        session["student_id"] = student.id
        return redirect(url_for("student.details"))

    client_path = os.path.join(os.getcwd(), "../frontend/public/student/index.html")
    return send_file(client_path)



@student_bp.route("/details", methods=["GET", "POST"])
def details():
    if not session.get("tutorial_code"):
        return redirect(url_for("student.index"))

    if request.method == "POST":
        session["currentGPA"] = request.form.get("currentGPA")
        session["goalGPA"] = request.form.get("goalGPA", 4)
        session["availability"] = request.form.get("availability")
        student = Student.query.get(session["student_id"])
        student.currentGPA = float(session["currentGPA"])
        student.goalGPA = float(session["goalGPA"])
        db.session.commit()
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
