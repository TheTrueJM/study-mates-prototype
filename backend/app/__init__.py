from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_login import LoginManager
from .database import db, Staff
from .routes import staff_bp, student_bp

import os
import threading
from threading import Lock

_env_frontend = os.getenv("FRONTEND_ORIGINS")
if _env_frontend:
    FRONTEND_ORIGINS = [o.strip() for o in _env_frontend.split(',') if o.strip()]
else:
    FRONTEND_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://study-mates-deployment.vercel.app",
        "https://study-mates-deployment-studymates-projects-4d298d59.vercel.app"
    ]

socketio = SocketIO(
    logger=True,
    cors_allowed_origins=FRONTEND_ORIGINS,
)

timer_threads = dict()
timer_locks = dict()
app_context_holder = None


def _start_timer_thread(code):
    if code in timer_threads and timer_threads[code].is_alive():
        return

    timer_locks.setdefault(code, Lock())

    def timer_loop():
        from time import sleep

        while True:
            sleep(1)

            if not app_context_holder:
                continue

            with app_context_holder.app_context():
                from .sockets import utils

                lock = timer_locks.get(code)
                if not lock:
                    return

                with lock:
                    tutorial = utils.tutorials.get(code)
                    if not tutorial or not tutorial.get("timer", {}).get("running", False):
                        return

                    timer = tutorial["timer"]
                    timer["remaining"] = max(0, timer["remaining"] - 1)

                    if timer["remaining"] == 0:
                        timer["running"] = False
                        message = {"message": "Time's up!"}
                        socketio.emit("timer_notification", message, room=code, namespace="/")
                        socketio.emit("timer_notification", message, room=code, namespace="/staff")
                    else:
                        utils._emit_tutorial_update(code)

    timer_threads[code] = threading.Thread(target=timer_loop, daemon=True)
    timer_threads[code].start()


def _stop_timer_thread(code):
    timer_threads.pop(code, None)
    timer_locks.pop(code, None)


def create_app():
    app = Flask(__name__)

    global app_context_holder
    app_context_holder = app

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "insecure-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///study_mates.sqlite")
    
    # Configure session cookie for cross-site usage when using HTTPS
    # Use secure cookies when any frontend origin is https
    has_https_origin = any(o.startswith("https://") for o in FRONTEND_ORIGINS)
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = bool(has_https_origin)

    db.init_app(app)
    CORS(app, origins=FRONTEND_ORIGINS, supports_credentials=True) # Update Origins
    socketio.init_app(app)

    with app.app_context():
        db.create_all()

    # Register blueprints
    app.register_blueprint(staff_bp, url_prefix="/staff")
    app.register_blueprint(student_bp)

    from . import sockets

    login_manager = LoginManager()
    login_manager.login_view = "staff.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(username):
        return db.session.scalar(db.select(Staff).where(Staff.username==username))

    return app
