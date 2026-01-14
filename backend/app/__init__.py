from flask import Flask
from .database import db
from .routes import staff_bp, student_bp

import os

def create_app():
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///study_mates.sqlite")

    db.init_app(app)

    # Register blueprints
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(student_bp)

    return app