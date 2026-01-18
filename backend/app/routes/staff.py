from flask import Blueprint, jsonify


staff_bp = Blueprint("staff", __name__)

@staff_bp.route("/")
def index():
    return jsonify(None), 200
