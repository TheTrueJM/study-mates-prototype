import logging
import uuid
import random

from flask import request, session
from flask_socketio import emit, join_room
from .. import socketio, _start_timer_thread, _stop_timer_thread
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

    if utils.users.get(user_id, {}).get("role") != "staff":
        emit("error", {"message": "Unauthorized"}, to=request.sid, namespace="/staff")
        return
    elif utils.users.get(user_id, {}).get("tutorial") is not None:
        emit("error", {"message": "Already in a tutorial"}, to=request.sid, namespace="/staff")
        return

    name = data.get("name")
    group_size = int(data.get("group_size")) or None
    discussion_time = int(data.get("discussion_time", 10)) * 60 or 600

    if not group_size or group_size < 2:
        emit("error", {"message": "Invalid group size"}, to=request.sid, namespace="/staff")
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
        "timer": {
            "duration": discussion_time,
            "remaining": discussion_time,
            "running": False
        }
    }

    logger.info(f"Created tutorial {code} for {user_id}")

    utils.users[user_id]["tutorial"] = code
    join_room(code, namespace="/staff")

    emit("tutorial_created", {"code": code}, namespace="/staff")


@socketio.on("reset_lobby", namespace="/staff")
def reset_lobby():
    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", {"message": "Session not found"}, to=request.sid, namespace="/staff")
        return

    if not (code := utils.users.get(user_id, {}).get("tutorial")):
        emit("error", {"message": "No active tutorial"}, to=request.sid, namespace="/staff")
        return

    if not (tutorial := utils.tutorials.get(code)):
        emit("error", {"message": "Tutorial not found"}, to=request.sid, namespace="/staff")
        return

    if tutorial["staff"] != user_id:
        emit("error", {"message": "Unauthorized"}, to=request.sid, namespace="/staff")
        return

    tutorial["state"] = "lobby"
    tutorial["groups"].clear()
    tutorial["questions"].clear()

    for student in tutorial["students"].values():
        student["group"] = None

    utils._emit_tutorial_update(code)


# -----------------------------
# Grouping
# -----------------------------

@socketio.on("start_grouping", namespace="/staff")
def start_grouping():
    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", {"message": "Session not found"}, to=request.sid, namespace="/staff")
        return

    if not (code := utils.users.get(user_id, {}).get("tutorial")):
        emit("error", {"message": "No active tutorial"}, to=request.sid, namespace="/staff")
        return

    if not (tutorial := utils.tutorials.get(code)):
        emit("error", {"message": "Tutorial not found"}, to=request.sid, namespace="/staff")
        return

    if tutorial["staff"] != user_id:
        emit("error", {"message": "Unauthorized"}, to=request.sid, namespace="/staff")
        return

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
    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", {"message": "Session not found"}, to=request.sid, namespace="/staff")
        return

    if not (code := utils.users.get(user_id, {}).get("tutorial")):
        emit("error", {"message": "No active tutorial"}, to=request.sid, namespace="/staff")
        return

    if not (tutorial := utils.tutorials.get(code)):
        emit("error", {"message": "Tutorial not found"}, to=request.sid, namespace="/staff")
        return

    if tutorial["staff"] != user_id:
        emit("error", {"message": "Unauthorized"}, to=request.sid, namespace="/staff")
        return

    tutorial["state"] = "discussion"
    tutorial["timer"]["remaining"] = tutorial["timer"]["duration"]
    tutorial["timer"]["running"] = True
    _start_timer_thread(code)

    questions = ["Question Test1", "Question Test2", "Question Test3"]
    tutorial["questions"] = questions

    utils._emit_tutorial_update(code)


@socketio.on("start_timer", namespace="/staff")
def start_timer():
    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", {"message": "Session not found"}, to=request.sid, namespace="/staff")
        return

    if not (code := utils.users.get(user_id, {}).get("tutorial")):
        emit("error", {"message": "No active tutorial"}, to=request.sid, namespace="/staff")
        return

    if not (tutorial := utils.tutorials.get(code)):
        emit("error", {"message": "Tutorial not found"}, to=request.sid, namespace="/staff")
        return

    if tutorial["staff"] != user_id:
        emit("error", {"message": "Unauthorized"}, to=request.sid, namespace="/staff")
        return

    tutorial["timer"]["running"] = True
    _start_timer_thread(code)
    utils._emit_tutorial_update(code)


@socketio.on("stop_timer", namespace="/staff")
def stop_timer():
    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", {"message": "Session not found"}, to=request.sid, namespace="/staff")
        return

    if not (code := utils.users.get(user_id, {}).get("tutorial")):
        emit("error", {"message": "No active tutorial"}, to=request.sid, namespace="/staff")
        return

    if not (tutorial := utils.tutorials.get(code)):
        emit("error", {"message": "Tutorial not found"}, to=request.sid, namespace="/staff")
        return

    if tutorial["staff"] != user_id:
        emit("error", {"message": "Unauthorized"}, to=request.sid, namespace="/staff")
        return

    tutorial["timer"]["running"] = False
    _stop_timer_thread(code)
    utils._emit_tutorial_update(code)


@socketio.on("edit_timer", namespace="/staff")
def edit_timer(data):
    if not (user_id := utils.sessions.get(request.sid)):
        emit("error", {"message": "Session not found"}, to=request.sid, namespace="/staff")
        return

    if not (code := utils.users.get(user_id, {}).get("tutorial")):
        emit("error", {"message": "No active tutorial"}, to=request.sid, namespace="/staff")
        return

    if not (tutorial := utils.tutorials.get(code)):
        emit("error", {"message": "Tutorial not found"}, to=request.sid, namespace="/staff")
        return

    if tutorial["staff"] != user_id:
        emit("error", {"message": "Unauthorized"}, to=request.sid, namespace="/staff")
        return

    new_time = int(data.get("time", 10)) * 60 or 600
    tutorial["timer"]["duration"] = new_time
    tutorial["timer"]["remaining"] = new_time

    if tutorial["timer"]["running"]:
        _stop_timer_thread(code)
        _start_timer_thread(code)

    utils._emit_tutorial_update(code)
