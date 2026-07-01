from flask import Flask, Blueprint
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_jwt_extended import JWTManager
from datetime import timedelta
from dotenv import load_dotenv
import os

from .database import db
from .routes import staff_bp
from .sockets import register_staff_events, register_student_events, timer
from .populate import populate_all


load_dotenv()
LOGGER = os.getenv("SOCKETIO_LOGGER", "false").lower() in {"true", "t", "1"}

FLASK_KEY = os.getenv("FLASK_SECRET_KEY")
DB_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///study_mates.sqlite")

JWT_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY = int(os.getenv("JWT_EXPIRATION_HOURS")) if os.getenv("JWT_EXPIRATION_HOURS", "").isdigit() else 24

ALL_ORIGINS = os.getenv("FRONTEND_ORIGINS")
if ALL_ORIGINS:
    FRONTEND_ORIGINS = [origin.strip() for origin in ALL_ORIGINS.split(',') if origin.strip()]
else:
    FRONTEND_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]


socketio = SocketIO(logger=LOGGER, cors_allowed_origins=FRONTEND_ORIGINS, async_mode=None)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = FLASK_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    app.config["JWT_SECRET_KEY"] = JWT_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=JWT_EXPIRY)
    
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25)

    CORS(app, origins=FRONTEND_ORIGINS, supports_credentials=True)
    JWTManager(app)
    
    # Register blueprints
    api_bp = Blueprint('api', __name__)
    api_bp.register_blueprint(staff_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    register_student_events(socketio)
    register_staff_events(socketio)
    
    timer.app_ctx = app
    timer.socketio = socketio

    with app.app_context():
        db.create_all()
        populate_all()
    
    return app, socketio