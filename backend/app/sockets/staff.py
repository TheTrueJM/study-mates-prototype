import logging
import uuid
import random

from flask import request, session
from flask_socketio import emit, join_room
from .. import socketio
from . import utils

logger = logging.getLogger(__name__)


@socketio.on("connect", namespace="/staff")
def connect(auth):
    user_id = auth.get("uuid") if auth else None
    role = session.get("role", "staff")
    code = session.get("tutorial_code")

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
        },
        namespace="/staff"
    )

    utils._join_tutorial(user_id, code, namespace="/staff")


# -----------------------------
# Tutorial management
# -----------------------------


@socketio.on("create_tutorial", namespace="/staff")
def create_tutorial(data):
    user_id = utils.sessions.get(request.sid)

    logger.info(f"Creating tutorial for {user_id}")

    if not user_id or utils.users.get(user_id, {}).get("role") != "staff":
        return

    name = data.get("name")
    group_size = int(data.get("group_size")) or None
    # TODO: Discussion Questions, Discussion Time

    if not group_size or group_size < 2:
        emit("create_failed", namespace="/staff")
        return

    code = utils._generate_code()

    utils.tutorials[code] = {
        "staff": user_id,
        "name": name,
        "state": "lobby",
        "group_size": group_size,
        "students": dict(),
        "groups": dict(),
        "questions": list(),
    }

    logger.info(f"Created tutorial {code} for {user_id}")

    utils.users[user_id]["tutorial"] = code
    join_room(code, namespace="/staff")

    emit("tutorial_created", {"code": code}, namespace="/staff")


@socketio.on("reset_lobby", namespace="/staff")
def reset_lobby():
    user_id = utils.sessions.get(request.sid)
    code = utils.users[user_id]["tutorial"]
    tutorial = utils.tutorials.get(code)

    if tutorial and tutorial["staff"] == user_id:
        tutorial["state"] = "lobby"
        tutorial["groups"].clear()
        tutorial["questions"].clear()

        utils._emit_tutorial_update(code)


# -----------------------------
# Grouping
# -----------------------------

@socketio.on("start_grouping", namespace="/staff")
def start_grouping():
    user_id = utils.sessions.get(request.sid)

    if user_id:
        code = utils.users[user_id]["tutorial"]
        tutorial = utils.tutorials.get(code)

        if tutorial and tutorial["staff"] == user_id:
            tutorial["questions"].clear()
            group_size = tutorial["group_size"]
            students = list(tutorial["students"].keys())
            random.shuffle(students)

            tutorial["groups"].clear()
            tutorial["state"] = "groups"

            for idx, student_id in enumerate(students):
                group_id = 1 + idx // group_size
                tutorial["groups"].setdefault(group_id, []).append(student_id)
                tutorial["students"][student_id]["group"] = group_id

            utils._emit_tutorial_update(code)


# -----------------------------
# Discussion
# -----------------------------


@socketio.on("start_discussion", namespace="/staff")
def start_discussion():
    user_id = utils.sessions.get(request.sid)
    code = utils.users[user_id]["tutorial"]
    tutorial = utils.tutorials.get(code)

    if tutorial and tutorial["staff"] == user_id:
        tutorial["state"] = "discussion"

        # Placeholder: questions = db.get_questions(code)
        questions = ["Question Test1", "Question Test2", "Question Test3"]
        tutorial["questions"] = questions
        # emit("discussion_started", {"questions": questions}, room=code, namespace="/staff")

        utils._emit_tutorial_update(code)
