from flask import Flask
from flask_socketio import SocketIO
from .database import db
from .routes import staff_bp, student_bp, index_bp

import os

socketio = SocketIO(
    logger=True,
    cors_allows_origins = "*",
    cors_credentials = False,
)

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///study_mates.sqlite")

    db.init_app(app)
    socketio.init_app(app)

    # Register blueprints
    app.register_blueprint(index_bp)
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(student_bp)

    from . import sockets

    return app
