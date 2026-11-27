from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, jwt_required

from ..auth import (
    GUEST, ACCOUNT, MAX_LOGIN_ATTEMPTS, MAX_REGISTER_ATTEMPTS, create_staff_token, get_staff_identity,
    is_possible_login, verify_staff_login, validate_staff_account, register_staff, record_attempt, clear_attempts
)


staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/login", methods=["POST"])
def login():
    username, password, error = _get_credentials()
    if error:
        return error

    # The same message for an Unknown Username or Wrong Password, so Usernames can't be discovered
    incorrect = jsonify({"message": "Incorrect username or password"}), 401
    if not is_possible_login(username, password):
        return incorrect

    attempt = ("login", request.remote_addr, username.lower())
    if not record_attempt(*attempt, limit=MAX_LOGIN_ATTEMPTS):
        return _too_many_attempts()

    staff = verify_staff_login(username, password)
    if not staff:
        return incorrect

    clear_attempts(*attempt)
    return _signed_in(staff, "Login successful"), 200


@staff_bp.route("/register", methods=["POST"])
def register():
    username, password, error = _get_credentials()
    if error:
        return error

    username = username.strip()
    if message := validate_staff_account(username, password):
        return jsonify({"message": message}), 400

    # Every attempt is counted, as these show which Usernames are taken
    if not record_attempt("register", request.remote_addr, limit=MAX_REGISTER_ATTEMPTS):
        return _too_many_attempts()

    staff = register_staff(username, password)
    if not staff:
        return jsonify({"message": "This username is already taken"}), 409

    return _signed_in(staff, "Register successful"), 201


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


def _get_credentials():
    """Returns a tuple of the request's username and password, and an error response"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, None, (jsonify({"message": "Invalid login data or format"}), 400)

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
        return None, None, (jsonify({"message": "Enter your username and password"}), 400)

    return username, password, None


def _signed_in(staff, message):
    return jsonify({
        "token": create_staff_token(staff),
        "staff_type": ACCOUNT,
        "username": staff.username,
        "message": message,
    })


def _too_many_attempts():
    return jsonify({"message": "Too many attempts. Please wait a few minutes and try again."}), 429
