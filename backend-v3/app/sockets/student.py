from flask import request
from flask_socketio import emit, join_room, leave_room

from .utils import tutorials, users, sessions, generate_unique_user_uuid, generate_unique_student_name, emit_tutorial_update
from .. import socketio
from ..enums import TutorialState, AttributeType, VALID_ATTRIBUTES


def register_student_events(socketio):
    @socketio.on("connect", namespace="/")
    def connect(auth: dict = None):
        user_id = auth.get("uuid") if isinstance(auth, dict) else None

        if user_id not in users:
            user_id = generate_unique_user_uuid()
            users[user_id] = {
                "sessions": set(),
                "tutorial": None
            }

        tutorial_code = auth.get("code") if isinstance(auth, dict) else None
        if tutorial_code:
            previous_tutorial = users[user_id]["tutorial"]
            if previous_tutorial and previous_tutorial in tutorials:
                pass # TODO Leave Previous Tutorial
            if tutorial_code in tutorials:
                join_tutorial(user_id, tutorial_code)

        users[user_id]["role"] = "student"
        users[user_id]["sessions"].add(request.sid)
        sessions[request.sid] = user_id

        emit("session",
            {
                "uuid": user_id,
                "role": users[user_id]["role"],
                "code": users[user_id]["tutorial"]
            }
        )

    def join_tutorial(user_id, code):
        join_room(user_id, namespace="/")

        if not (tutorial := tutorials.get(code)):
            emit("error", {"message": "Tutorial Not Found"}, to=request.sid, namespace="/")
            return

        if not (user := users.get(user_id)) or not isinstance(user, dict):
            emit("error", {"message": "User Session Not Found"}, to=request.sid, namespace="/")
            return

        if user.get("role") != "student":
            emit("error", {"message": "Invalid User Role"}, to=request.sid, namespace="/")
            return

        user["tutorial"] = code
        tutorial["students"][user_id] = {
            "name": generate_unique_student_name(code),
            "attributes": dict(),
            "shared_attributes": list(),
            "attributes_complete": False,
            "group": None
        }

        state = tutorial.get("state")
        if state in {TutorialState.GROUPING, TutorialState.INTRODUCTION, TutorialState.DISCUSSION}:
            late_group_assignment(code, user_id)

        join_room(code, namespace="/")

        emit_tutorial_update(code)


def late_group_assignment(tutorial_code, student_id):
    tutorial = tutorials.get(tutorial_code, {})
    students = tutorial.get("students", {})
    groups = tutorial.get("groups", {})

    if not groups or not students.get(student_id):
        return False
    
    group_ids = list(groups.keys())
    best_group_id = group_ids[-1]
    for group_id in group_ids:
        if len(groups[group_id]) < len(groups[best_group_id]):
            best_group_id = group_id
    
    groups[best_group_id].append(student_id)
    students[student_id]["group"] = best_group_id
    return True