from flask import Flask
from flask_socketio import SocketIO
from flask_login import LoginManager
from sqlalchemy import or_
from .database import db, Staff
from .routes import staff_bp, student_bp

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
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(student_bp)

    from . import sockets

    login_manager = LoginManager()

    login_manager.login_view = "staff.login" 
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id_or_name):
        return db.session.scalar(db.select(Staff).where(or_(Staff.id==id_or_name, Staff.username==id_or_name)))

    return app
