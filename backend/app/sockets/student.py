# student.py
import logging
import uuid

from flask import request
from flask_socketio import emit
from .. import socketio
from . import utils
from .errors import ERR_CODE_REQUIRED, ERR_SESSION_NOT_FOUND, ERR_TUTORIAL_NOT_FOUND, ERR_NOT_IN_TUTORIAL, ERR_INVALID_GPA

logger = logging.getLogger(__name__)


@socketio.on("connect")
def connect(auth: dict = {}):
    user_id = auth.get("uuid", str(uuid.uuid4()))

    existing_tutorial = None
    if user_id in utils.users:
        existing_tutorial = utils.users[user_id].get("tutorial")
    else:
        utils.users[user_id] = {
            "sessions": set(),
            "role": "student",
            "tutorial": None
        }

    code = auth.get("code", existing_tutorial)

    utils.users[user_id]["sessions"].add(request.sid)
    utils.sessions[request.sid] = user_id

    emit("session",
        {
            "uuid": user_id,
            "role": "student",
            "code": utils.users[user_id]["tutorial"]
        }
    )

    utils._join_tutorial(user_id, code, {}, namespace="/")
    

@socketio.on("join_tutorial")
def join_tutorial(data: dict = {}):
    if not (code := data.get("code")):
        emit("error", ERR_CODE_REQUIRED, to=request.sid)
        return

    details = data.get("details")
    if isinstance(details, dict):
        try:
            current = float(data.get("currentGPA", 4.5))
            goal = float(data.get("goalGPA", 4.0))
            if current < 0 or current > 7 or goal < 0 or goal > 7:
                raise ValueError
        except ValueError:
            emit("error", ERR_INVALID_GPA, to=request.sid)
            return

    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", ERR_SESSION_NOT_FOUND, to=request.sid)
        return

    utils._join_tutorial(user_id, code, details, namespace="/")


@socketio.on("fetch_tutorial")
def fetch_tutorial():
    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", ERR_SESSION_NOT_FOUND, to=request.sid)
        return

    if not (code := utils.users.get(user_id, {}).get("tutorial")):
        emit("error", ERR_NOT_IN_TUTORIAL, to=request.sid)
        return

    if not utils.tutorials.get(code):
        emit("error", ERR_TUTORIAL_NOT_FOUND, to=request.sid)
        return

    utils._emit_tutorial_update(code)


@socketio.on("reset_session")
def reset_session():
    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", ERR_SESSION_NOT_FOUND, to=request.sid)
        return

    code = utils.users.get(user_id, {}).get("tutorial")
    if code and code in utils.tutorials:
        tutorial = utils.tutorials[code]
        if user_id in tutorial.get("students", {}):
            tutorial["students"].pop(user_id, None)
        utils._emit_tutorial_update(code)

    utils.users[user_id]["tutorial"] = None

    emit("session_cleared", {"message": "Session cleared"}, to=request.sid)
