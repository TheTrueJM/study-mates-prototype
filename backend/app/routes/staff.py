from flask import Blueprint, session, request, redirect, url_for, send_file, render_template, jsonify
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user, current_user
from sqlalchemy import or_
from ..database import db, Staff, AccountInvite
import random, string

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



@staff_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid login data or format"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    staff: Staff | None = db.session.scalar(db.select(Staff).where(Staff.username==username))

    # Validate staff identity and password
    if not isinstance(staff, Staff):
        return jsonify({"error": "Staff not found"}), 400
    if not check_password_hash(staff.password_hash, password):
        return jsonify({"error": "Incorrect password"}), 401
    
    login_user(staff)

    return jsonify({
        "message": "Login successful",
        "staff": {
            "username": "username"
        }
    }), 200


@staff_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200



@staff_bp.route("/invite", methods=["GET", "POST"])
@login_required
def generate_invite():
    if request.method == "POST":
        code = _generate_invite_code()

        if code:
            invite = AccountInvite(code=code, staff=current_user)
            db.session.add(invite)
            db.session.commit()

            invite_url = url_for("staff.register", code=code, _external=True)
            print(invite_url)

    client_path = os.path.join(os.getcwd(), "../frontend/public/staff/invites.html")
    return send_file(client_path)

def _generate_invite_code(length = 20):
    codes: list[AccountInvite] = db.session.scalars(db.select(AccountInvite.code)).all()
    for _ in range(1 + len(codes) * 2):
        code = ''.join(random.choices(string.ascii_letters, k=length))
        if code not in codes:
            return code
    return None


@staff_bp.route("/register/<code>", methods=["GET", "POST"])
def register(code: str):
    invite = db.session.scalar(db.select(AccountInvite).where(AccountInvite.code==code))

    if not invite or not invite.active:
        # flash("This invitation link is invalid or has already been used.", "danger")
        return redirect(url_for("staff.login"))
    
    if current_user.is_authenticated:
        # flash("You are already logged in.", "info")
        return redirect(url_for("staff.index"))
    
    error: str = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if staff already exists
        staff: Staff | None = db.session.scalar(db.select(Staff).where(Staff.username==username))

        if isinstance(staff, Staff):
            error = "Username already taken"
        elif not username:
            error = "Must provide a username"
        elif not password:
            error = "Must provide a password"
        
        if error:
            # flash(error, "danger")
            pass
        else:
            # Create new user
            staff = Staff(
                username=username,
                password_hash=generate_password_hash(password),
            )
            db.session.add(staff)
            # Expire invite
            invite.active = False
            db.session.commit()

            login_user(staff)
            # flash("Register successful", "success")

            return redirect(url_for("staff.index"))
        
    # return render_template("auth.html", form=register_form, heading="Register")
    client_path = os.path.join(os.getcwd(), "../frontend/public/staff/register.html")
    return send_file(client_path)


### REMOVE THIS LATER
@staff_bp.route("/test_user", methods=["GET", "POST"])
def test_user():
    exists: Staff | None = db.session.scalar(db.select(Staff).where(Staff.username=="test"))
    if exists is None:
        staff = Staff(
            username="test",
            password_hash=generate_password_hash("test"),
        )
        db.session.add(staff)
        db.session.commit()
    return redirect(url_for("staff.login"))