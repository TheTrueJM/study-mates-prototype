# student.py
import logging
import uuid
from flask import request, session
from flask_socketio import emit
from .. import socketio
from . import utils
from .errors import ERR_CODE_REQUIRED, ERR_SESSION_NOT_FOUND, ERR_TUTORIAL_NOT_FOUND, ERR_NOT_IN_TUTORIAL

logger = logging.getLogger(__name__)


@socketio.on("connect")
def connect(auth):
    user_id = auth.get("uuid") if auth else None
    role = session.get("role", "student")

    existing_tutorial = None
    if user_id and user_id in utils.users:
        existing_tutorial = utils.users[user_id].get("tutorial")

    code = session.get("tutorial_code") or existing_tutorial

    if not user_id: user_id = str(uuid.uuid4())

    if user_id not in utils.users:
        utils.users[user_id] = {
            "sessions": set(),
            "role": role,
            "tutorial": None
        }

    utils.users[user_id]["sessions"].add(request.sid)
    utils.sessions[request.sid] = user_id

    emit("session",
        {
            "uuid": user_id,
            "role": role,
            "tutorial": utils.users[user_id]["tutorial"]
        }
    )

    utils._join_tutorial(user_id, code, namespace="/")
    

@socketio.on("join_tutorial")
def join_tutorial(data):
    if not (code := data.get("code")):
        emit("error", ERR_CODE_REQUIRED, to=request.sid)
        return

    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", ERR_SESSION_NOT_FOUND, to=request.sid)
        return

    utils._join_tutorial(user_id, code, namespace="/")


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

            # Clean up from groups
            for group_id, members in tutorial.get("groups", {}).items():
                if user_id in members:
                    members[:] = [m for m in members if m != user_id]
        utils._emit_tutorial_update(code)

    utils.users[user_id]["tutorial"] = None

    emit("session_cleared", {"message": "Session cleared"}, to=request.sid)
