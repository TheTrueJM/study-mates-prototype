from flask import Flask, Blueprint
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from datetime import timedelta
from dotenv import load_dotenv
import os

from .database import db
from .routes import staff_bp, saved_bp
from .sockets import register_staff_events, register_student_events, run_cleanup, timer
from .populate import populate_all


load_dotenv()
LOGGER = os.getenv("SOCKETIO_LOGGER", "false").lower() in {"true", "t", "1"}

FLASK_KEY = os.getenv("FLASK_SECRET_KEY")
def get_database_uri(uri):
    """
    The database to use: SQLite by default, or Postgres (e.g. a Render Postgres database's URL).
    Postgres URLs are given as postgres:// or postgresql://, so are pointed at the installed driver (psycopg 3).
    """
    if not uri:
        return "sqlite:///study_mates.sqlite"
    for scheme in ("postgres://", "postgresql://"):
        if uri.startswith(scheme):
            return "postgresql+psycopg://" + uri[len(scheme):]
    return uri

DB_URI = get_database_uri(os.getenv("SQLALCHEMY_DATABASE_URI"))

JWT_KEY = os.getenv("JWT_SECRET_KEY")
JWT_EXPIRY = int(os.getenv("JWT_EXPIRATION_HOURS")) if os.getenv("JWT_EXPIRATION_HOURS", "").isdigit() else 24

ALL_ORIGINS = os.getenv("FRONTEND_ORIGINS")
if ALL_ORIGINS:
    FRONTEND_ORIGINS = [origin.strip() for origin in ALL_ORIGINS.split(",") if origin.strip()]
else:
    FRONTEND_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


socketio = SocketIO(logger=LOGGER, cors_allowed_origins=FRONTEND_ORIGINS, async_mode="gevent")


def create_app():
    # Access Tokens can't be issued without a Key (the flask key is used if there is no JWT key)
    if not JWT_KEY and not FLASK_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY must be set before the server can start (see backend/.env.example). "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = FLASK_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    # Hosted databases close idle connections, so check each one before it's used (and replace them regularly)
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 300}
    app.config["JWT_SECRET_KEY"] = JWT_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=JWT_EXPIRY)
    
    db.init_app(app)
    socketio.init_app(app, async_mode="gevent", cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

    CORS(app, origins=FRONTEND_ORIGINS, supports_credentials=True)
    JWTManager(app)
    
    # Register blueprints
    api_bp = Blueprint("api", __name__)
    api_bp.register_blueprint(staff_bp)
    api_bp.register_blueprint(saved_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    
    register_student_events(socketio)
    register_staff_events(socketio)
    
    timer.app_ctx = app
    timer.socketio = socketio

    with app.app_context():
        db.create_all()
        populate_all()

    socketio.start_background_task(run_cleanup, app, socketio)
    
    return app, socketio