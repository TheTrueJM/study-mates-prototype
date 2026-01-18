from flask import Blueprint, send_file
import os

index_bp = Blueprint("index", __name__)

@index_bp.route("/")
def index():
    client_path = os.path.join(
        os.getcwd(), "../frontend/public/tmp/student_client.html"
    )
    return send_file(client_path)

@index_bp.route("/teacher")
def teacher():
    client_path = os.path.join(
        os.getcwd(), "../frontend/public/tmp/teacher_client.html"
    )
    return send_file(client_path)
