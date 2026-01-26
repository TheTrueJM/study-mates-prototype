from flask import Blueprint, session, request, redirect, url_for, send_file, render_template
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user
from sqlalchemy import or_
from ..database import db, Staff

import os


staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/", methods=["GET"])
@login_required
def index():
    session["role"] = "staff"
    session["tutorial_code"] = None

    client_path = os.path.join(os.getcwd(), "../frontend/public/staff/index.html")
    return send_file(client_path)


@staff_bp.route("/tutorial/<code>", methods=["GET"])
@login_required
def tutorial(code):
    ## To-Do: Kick back to Index if Tutorial doesn't exist on server
    session["tutorial_code"] = code

    client_path = os.path.join(os.getcwd(), "../frontend/public/staff/tutorial.html")
    return send_file(client_path)



@staff_bp.route("/login", methods=["GET", "POST"])
def login():
    error: str = None
    
    if request.method == "POST":
        id_or_username = request.form.get("id_or_username")
        password = request.form.get("password")
        
        # Check if staff exists
        # To-Do: Update if Identification changes
        staff: Staff | None = db.session.scalar(db.select(Staff).where(or_(Staff.id==id_or_username, Staff.username==id_or_username)))

        # Validate staff identity and password
        if not isinstance(staff, Staff):
            error = "User not found for that id or username"
        elif not check_password_hash(staff.password_hash, password):
            error = "Incorrect password"
        
        if error:
            print(error)
            # flash(error, "danger")
        else:
            login_user(staff)
            # flash("Login successful", "success")

            # Redirect to the original destination or index
            destination = request.args.get("next") 
            if destination is None or not destination.startswith("/"):
                return redirect(url_for("staff.index"))
            return redirect(destination)
    
    # return render_template("auth.html", form=login_form, heading="Login")
    client_path = os.path.join(os.getcwd(), "../frontend/public/staff/login.html")
    return send_file(client_path)


@staff_bp.route("/logout")
@login_required
def logout():
    logout_user()
    # flash("Logout successful", "info")
    return redirect(url_for("staff.login"))



@staff_bp.route("/register", methods=["GET", "POST"])
def register():
    if False: # Diasble Staff Reigster - until we know how we want this to work
        error: str = None
        if request.method == "POST":
            id = request.form.get("id")
            username = request.form.get("username")
            password = request.form.get("password")
            firstname = request.form.get("firstname")
            surname = request.form.get("surname")

            # Check if staff already exists
            # Update if Identification changes
            staff: Staff | None = db.session.scalar(db.select(Staff).where(or_(Staff.id==id, Staff.username==username)))

            # Also: need to check that username doesn't follow ID pattern (and vice versa)
            if isinstance(staff, Staff):
                error = "Staff ID or Username already taken"
            # elif " " in firstname or " " in surname:
            #     error = "Names cannot contain spaces"
            elif not username and (not firstname and not surname):
                error = "Must specify username or firstname and surname"
            
            if error:
                # flash(error, "danger")
                pass
            else:
                # Create new user
                staff = Staff(
                    id=id,
                    username=username or f"{firstname} {surname}",
                    password_hash=generate_password_hash(password),
                    firstname=firstname,
                    surname=surname
                )
                db.session.add(staff)
                db.session.commit()

                login_user(staff)
                # flash("Register successful", "success")

                # Redirect to the original destination or index
                destination = request.args.get("next") 
                if destination is None or not destination.startswith("/"):
                    return redirect(url_for("staff.index"))
                return redirect(destination)
        
        # return render_template("auth.html", form=register_form, heading="Register")
    client_path = os.path.join(os.getcwd(), "../frontend/public/staff/register.html")
    return send_file(client_path)


### REMOVE THIS LATER
@staff_bp.route("/test_user", methods=["GET", "POST"])
def test_user():
    exists: Staff | None = db.session.scalar(db.select(Staff).where(or_(Staff.id=="n1234", Staff.username=="test")))
    if exists is None:
        staff = Staff(
            id="n1234",
            username="test",
            password_hash=generate_password_hash("test"),
            firstname=None,
            surname=None
        )
        db.session.add(staff)
        db.session.commit()
    return redirect(url_for("staff.login"))