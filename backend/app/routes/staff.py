from flask import Blueprint, jsonify


staff_bp = Blueprint("staff", __name__)

# GET all users
@staff_bp.route("/")
def index():
    return jsonify(None), 200