from .. import socketio
from flask_socketio import emit
import uuid

@socketio.on("connect")
def connect():
    print("connected")
    userID = str(uuid.uuid4())
    emit("session", {"uuid": userID})
