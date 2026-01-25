from flask import Blueprint, session, request, redirect, url_for, send_file, render_template
import os


student_bp = Blueprint("student", __name__)

@student_bp.route("/")
def index():
    client_path = os.path.join(
        os.getcwd(), "../frontend/public/tmp/student_client.html"
    )
    return send_file(client_path)


@student_bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        code = request.form.get("code")
        session["tutorial_code"] = code
        return redirect(url_for("student.details"))

    client_path = os.path.join(
        os.getcwd(), "../frontend/public/student/index.html"
    )
    return send_file(client_path)


@student_bp.route("/details", methods=["GET", "POST"]) # Possibly Unnessary Route, and can Fully handle on frontend
def details():
    if not session.get("tutorial_code"):
        return redirect(url_for("student.index"))

    if request.method == "POST":
        session["student_details"] = {
            "name": request.form.get("name"), # Generate Random on Frontend, Here, or Socket-Server?
            "currentGPA": request.form.get("currentGPA"),
            "goalGPA": request.form.get("goalGPA", 4),
            "availability": request.form.get("availability")
        }
        session["role"] = "student"
        return redirect(url_for("student.tutorial", code=session["tutorial_code"]))


    client_path = os.path.join(
        os.getcwd(), "../frontend/public/student/details.html"
    )
    return send_file(client_path)


@student_bp.route("/tutorial/<code>", methods=["GET"])
def tutorial(code):
    """
    Student tutorial view.
    Group + discussion updates occur without route changes.
    """

    ## Emit User to Tutorial Session

    client_path = os.path.join(
        os.getcwd(), "../frontend/public/student/tutorial.html"
    )
    return send_file(client_path)