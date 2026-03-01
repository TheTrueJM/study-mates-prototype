from flask import Blueprint, request, jsonify
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_login import login_required, login_user, logout_user, current_user
import random, string

from ..database import db, Staff, AccountInvite


staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Invalid login data or format"}), 400
    
    username = data.get("username")
    password = data.get("password")
    
    staff: Staff | None =  Staff.query.filter_by(username=username).first()

    # Validate staff identity and password
    if not isinstance(staff, Staff):
        return jsonify({"error": "Staff username not found"}), 400
    if not check_password_hash(staff.password_hash, password):
        return jsonify({"error": "Incorrect password"}), 401
    
    login_user(staff)

    return jsonify({"message": "Login successful"}), 200


@staff_bp.route("/status", methods=["GET"])
def status():
    # Check staff authentication status
    if current_user.is_authenticated:
        return jsonify({"role": "staff", "authenticated": True}), 200
    return jsonify({"role": "student", "authenticated": False}), 200


@staff_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200


# ===== Staff Account Invitation & Registration ===== #

# @staff_bp.route("/invite", methods=["GET", "POST"])
# @login_required
# def generate_invite():
#     if request.method == "POST":
#         code = _generate_invite_code()

#         if code:
#             invite = AccountInvite(code=code, staff=current_user)
#             db.session.add(invite)
#             db.session.commit()

#             invite_url = url_for("staff.register", code=code, _external=True)
#             print(invite_url)

#     client_path = os.path.join(os.getcwd(), "../frontend/public/staff/invites.html")
#     return send_file(client_path)

# def _generate_invite_code(length = 20):
#     codes: list[AccountInvite] = AccountInvite.query.with_entities(AccountInvite.code).all()
#     for _ in range(1 + len(codes) * 2):
#         code = ''.join(random.choices(string.ascii_letters, k=length))
#         if code not in codes:
#             return code
#     return None


# @staff_bp.route("/register/<code>", methods=["GET", "POST"])
# def register(code: str):
#     invite = AccountInvite.query.filter_by(code=code).first()

#     if not invite or not invite.active:
#         return jsonify({"error": "This invitation is invalid or has already been used"}), 400
    
#     if current_user.is_authenticated:
#         return jsonify({"error": "Your are already authenticated"}), 401
    
#     data = request.get_json()

#     if not isinstance(data, dict):
#         return jsonify({"error": "Invalid login data or format"}), 400
    
#     username = data.get("username")
#     password = data.get("password")

#     staff: Staff | None =  Staff.query.filter_by(username=username).first()

#     # Validate staff identity and password
#     if isinstance(staff, Staff):
#         return jsonify({"error": "Staff username is already taken"}), 400
#     if not username or not password:
#         return jsonify({"error": "Must provide a username and password"}), 400

#     staff = Staff(
#         username=username,
#         password_hash=generate_password_hash(password),
#     )
#     db.session.add(staff)
#     invite.active = False # Expire invite
#     db.session.commit()

#     login_user(staff)

#     return jsonify({"message": "Register successful"}), 200