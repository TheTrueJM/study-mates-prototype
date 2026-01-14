from flask import Blueprint, jsonify


student_bp = Blueprint("student", __name__)

# GET all users
@student_bp.route("/")
def index():
    return jsonify(None), 200