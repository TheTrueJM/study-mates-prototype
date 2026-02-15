import logging
import uuid
import random
import math
from functools import wraps

import numpy as np # Used for Matrix grouping algorithm, can be removed if we switch to a simpler approach

from flask import request, session
from flask_socketio import emit, join_room
from .. import socketio, _start_timer_thread, _stop_timer_thread
from . import utils

logger = logging.getLogger(__name__)


def _with_tutorial_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
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

        return f(user_id, code, tutorial, *args, **kwargs)
    return wrapper


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
    # TODO: Discussion Questions, Discussion Time
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
        "previous_matches": dict(),
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
@_with_tutorial_auth
def reset_lobby(user_id, code, tutorial):
    tutorial["state"] = "lobby"
    tutorial["groups"].clear()
    tutorial["questions"].clear()
    tutorial["timer"]["running"] = False

    for student in tutorial["students"].values():
        student["group"] = None

    utils._emit_tutorial_update(code)


@socketio.on("fetch_tutorial", namespace="/staff")
@_with_tutorial_auth
def fetch_tutorial(user_id, code, tutorial):
    utils._emit_tutorial_update(code)


# -----------------------------
# Grouping
# -----------------------------

@socketio.on("start_grouping", namespace="/staff")
@_with_tutorial_auth
def start_grouping(user_id, code, tutorial):
    tutorial["questions"].clear()
    tutorial["timer"]["running"] = False
    group_size = tutorial["group_size"] 

    students = list(tutorial["students"].keys())

    connections: np.ndarray = _build_matrix(students, tutorial["students"])

    # Print the graph weights for debugging purposes
    # for i, s1 in enumerate(students):
    #     for j, s2 in enumerate(students):
    #         if i != j: print(f"{tutorial['students'][s1]['name']} vs {tutorial['students'][s2]['name']}: {matrix[i][j]:.2f}")

    tutorial["groups"].clear()
    tutorial["state"] = "groups"

    group_id = 1
    unmatched = set(enumerate(students))
    rematch_rate = (0.5 / (group_size ** 1.1))
    while unmatched:
        # Pick a starting student
        group = [unmatched.pop()]

        # Fill group with most compatible students
        while len(group) < group_size and unmatched:
            best_student, best_score = None, -1

            for (candidate, c_id) in unmatched:
                # Compatibility with entire group
                score = rematches = 0
                for (member, m_id) in group:
                    # Track rematches between students in the group, with a slight chance to allow rematches through uncounted
                    if c_id in tutorial["previous_matches"].get(m_id, ()) and random.random() > rematch_rate:
                        rematches += 1
                    score += connections[candidate][member]

                # Penalise score from student rematches 
                if rematches: score *=  0.4 - (0.4 * (rematches / group_size))

                if score > best_score:
                    best_score = score
                    best_student = (candidate, c_id)

            group.append(best_student)
            unmatched.remove(best_student)

        # Save group
        tutorial["groups"][group_id] = []
        member_ids = set({id for (_, id) in group})
        for id in member_ids:
            tutorial["groups"][group_id].append(id)
            tutorial["students"][id]["group"] = group_id
            tutorial["previous_matches"].setdefault(id, set()).update(member_ids)
            
        group_id += 1

    utils._emit_tutorial_update(code)


def _build_matrix(ids, students):
    student_count = len(ids)
    matrix = np.zeros((student_count, student_count))
    max_weight = 0

    for i in range(student_count):
        s1 = ids[i]
        s1_availability = set(students[s1]["availability"])
        for j in range(i + 1, student_count):
            s2 = ids[j]

            w_currentGPA = students[s1]["currentGPA"] - students[s2]["currentGPA"] 
            w_currentGPA = 1 / (1 + abs(w_currentGPA))

            w_goalGPA = students[s1]["goalGPA"] - students[s2]["goalGPA"]
            w_goalGPA = 1 / (1 + abs(w_goalGPA))

            w_availability = 0.2 * sum(1 for time in students[s2]["availability"] if time in s1_availability)

            weight = w_currentGPA + w_goalGPA + w_availability
            matrix[i][j] = matrix[j][i] = weight
            max_weight = max(max_weight, weight)

    # Normalise matrix weights
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            matrix[i][j] = matrix[j][i] = matrix[i][j] / max_weight
    
    return matrix


# -----------------------------
# Discussion
# -----------------------------


@socketio.on("start_discussion", namespace="/staff")
@_with_tutorial_auth
def start_discussion(user_id, code, tutorial):
    tutorial["state"] = "discussion"
    tutorial["timer"]["remaining"] = tutorial["timer"]["duration"]
    tutorial["timer"]["running"] = True
    _start_timer_thread(code)

    questions = ["Question Test1", "Question Test2", "Question Test3"]
    tutorial["questions"] = questions

    utils._emit_tutorial_update(code)


@socketio.on("start_timer", namespace="/staff")
@_with_tutorial_auth
def start_timer(user_id, code, tutorial):
    tutorial["timer"]["running"] = True
    _start_timer_thread(code)
    utils._emit_tutorial_update(code)


@socketio.on("stop_timer", namespace="/staff")
@_with_tutorial_auth
def stop_timer(user_id, code, tutorial):
    tutorial["timer"]["running"] = False
    utils._emit_tutorial_update(code)


@socketio.on("reset_timer", namespace="/staff")
@_with_tutorial_auth
def reset_timer(user_id, code, tutorial, data):
    new_time = math.ceil(float(data.get("time", 10))) * 60 or 600
    tutorial["timer"]["duration"] = new_time
    tutorial["timer"]["remaining"] = new_time
    tutorial["timer"]["running"] = False
    utils._emit_tutorial_update(code)
