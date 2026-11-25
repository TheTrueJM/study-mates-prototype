from flask import Blueprint, request, jsonify
from flask_bcrypt import generate_password_hash, check_password_hash
from flask_jwt_extended import get_jwt, jwt_required

from ..auth import GUEST, ACCOUNT, create_staff_token, get_staff_identity
from ..database import db, Staff, AccountInvite


staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Invalid login data or format"}), 400

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
        return jsonify({"message": "Enter your username and password"}), 400

    # The same message for an Unknown Username or Wrong Password, so Usernames can't be discovered
    staff: Staff | None = Staff.query.filter_by(username=username).first()
    if not staff or not check_password_hash(staff.password_hash, password):
        return jsonify({"message": "Incorrect username or password"}), 401

    return jsonify({
        "token": create_staff_token(staff),
        "staff_type": ACCOUNT,
        "username": staff.username,
        "message": "Login successful",
    }), 200


@staff_bp.route("/guest", methods=["POST"])
def guest():
    return jsonify({
        "token": create_staff_token(),
        "staff_type": GUEST,
        "username": None,
        "message": "Continuing as a guest",
    }), 200


@staff_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Validates the request's access token, returning the staff identity it belongs to"""
    identity = get_staff_identity(get_jwt())
    if not identity:
        return jsonify({"message": "Your sign in is no longer valid"}), 401

    return jsonify({"staff_type": identity["type"], "username": identity["username"]}), 200


@staff_bp.route("/create-tutorial", methods=["POST"])
def create_tutorial():
    # This endpoint is handled via Socket.IO events
    return jsonify({"message": "Use Socket.IO to create tutorial"}), 400

@staff_bp.route("/end-tutorial", methods=["POST"])
def end_tutorial():
    # This endpoint is handled via Socket.IO events
    return jsonify({"message": "Use Socket.IO to end tutorial"}), 400
