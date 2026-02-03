import logging
import uuid
import random
from collections import deque

from flask import request, session
from flask_socketio import emit, join_room
from .. import socketio
from . import utils

from sqlalchemy.sql.expression import func
from ..database import db, DiscussionQuestion

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
    # TODO: Discussion Questions, Discussion Time

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

    ### Below is the Basic Code for the proper Matching Algorithm
    # connections: dict[tuple, float] = _build_graph(tutorial["students"])
    # unmatched = list(tutorial["students"].keys())
    # queue = deque()
    # group_id = 1

    # # This should be created and stored within the tutorial, so that it is preserved between matchings
    # previous_matches = dict({student: set() for student in unmatched})
    # # This should be created and stored within the tutorial, so that it is preserved between matchings
    # threshold = 0.75

    # while unmatched and queue:
    #     current_student = queue.popleft() or unmatched.pop()
    #     tutorial["groups"][group_id] = [current_student]
    #     for (new_student, weight) in connections[current_student]:
    #         if new_student in unmatched:
    #             unmatched.remove(new_student)
    #             if weight >= threshold:
    #                 queue.append(new_student)
    #                 if len(tutorial["groups"][group_id]) < group_size: # Handle previous_matches
    #                     tutorial["groups"][group_id].append(new_student)
    #                     if len(tutorial["groups"][group_id]) == group_size:
    #                         # Add all students in the current group to eachother's previous matches
    #                         group_id += 1
    #                         break
    #             else:
    #                 queue.appendleft(new_student)

    # threshold = max(threshold - 0.15, 0.45)

    utils._emit_tutorial_update(code)



    def _build_graph(students: dict[str, dict]):
        vertices = students.keys()
        edges = dict()
        maximum = 0

        for i in range(len(vertices) - 1):
            s1 = vertices[i]
            for j in range(i + 1, len(vertices)):
                s2 = vertices[j]

                score = 0
                if students[s1]["currentGPA"] and students[s2]["currentGPA"] and abs(students[s1]["currentGPA"] - students[s2]["currentGPA"]) <= 0.5:
                    score += 5
                if not students[s1]["currentGPA"] and not students[s2]["currentGPA"]:
                    score += 5
                if abs(students[s1]["goalGPA"] - students[s2]["goalGPA"]) <= 0.5:
                    score += 5

                # TODO: Implement this when "availability" is a list or set
                # for availability in students[s1]["availability"]:
                #     if availability in students[s2]["availability"]:
                #         score += 1

                if score:
                    maximum = max(maximum, score)
                    edges.setdefault(vertices[i], []).append(vertices[j], score)
                    edges.setdefault(vertices[j], []).append(vertices[i], score)
                    # Alternative way for edges
                    # edges[(max(vertices[i], vertices[j]), min(vertices[i], vertices[j]))] = score
        
        if maximum:
            # Normalise Results to values between 0.0-1.0
            for u in edges:
                # For Alterntive Edge Structure:
                # edges[edge] /= maximum
                for _ in range(len(edges[u])):
                    v, weight = edges[u]
                    edges[u].append((v, weight / maximum))
        
        return edges


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

    academic: DiscussionQuestion = db.session.query(DiscussionQuestion).filter(DiscussionQuestion.category_name == "academic").order_by(func.random()).first()
    casual: DiscussionQuestion = db.session.query(DiscussionQuestion).filter(DiscussionQuestion.category_name == "casual").order_by(func.random()).first()
    study: DiscussionQuestion = db.session.query(DiscussionQuestion).filter(DiscussionQuestion.category_name == "study").order_by(func.random()).first()


    questions = [academic.question, casual.question, study.question]
    tutorial["questions"] = questions

    utils._emit_tutorial_update(code)
