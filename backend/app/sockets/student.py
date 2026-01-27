import logging
import uuid
from flask import request, session
from flask_socketio import emit
from .. import socketio
from . import utils

logger = logging.getLogger(__name__)


@socketio.on("connect")
def connect(auth):
    logger.info("connect reached")
    user_id = auth.get("uuid") if auth else None
    role = session.get("role", "student")
    code = session.get("tutorial_code")

    if not user_id: user_id = str(uuid.uuid4())

    if user_id not in utils.users:
        utils.users[user_id] = {
            "sessions": set(),
            "role": role,
            "tutorial": None
        }

    logger.info(f"DEBUG: {utils.users[user_id]}")
    utils.users[user_id]["sessions"].add(request.sid)
    logger.info(f"DEBUG: {request.sid}")
    utils.sessions[request.sid] = user_id
    logger.info("Before emit session reached")

    emit("session",
        {
            "uuid": user_id,
            "role": role,
            "tutorial": code
        }
    )

    utils._join_tutorial(user_id, code, namespace="/")


@socketio.on("join_tutorial")
def join_tutorial(data):
    code = data.get("code")

    user_id = utils.sessions.get(request.sid)
    if not user_id or code not in utils.tutorials:
        emit("join_failed")
        return

    utils._join_tutorial(user_id, code, namespace="/")
