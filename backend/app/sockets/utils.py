import random
import string
import uuid
import logging
from flask import session, request
from flask_socketio import emit, join_room
from .. import socketio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

users = dict() # { UUID: {sessions: {sID, ...}, role: student|staff, tutorial: code}, ... }
sessions = dict() # { sID: UUID }
tutorials = dict()
# {
#   code: {
#       staff: UUID,
#       name: name,
#       state: lobby|groups|discussion,
#       group_size: size,
#       students: { UUID, ... },
#       groups: { id: [ UUID, ... ], ... },
#       questions: [question, ...]
#   },
#   ...
# }


# -----------------------------
# Helpers
# -----------------------------


def _generate_code(length=6):
    while True:
        code  = ''.join(random.choices(string.ascii_uppercase, k=length))
        if code not in tutorials:
            return code


def _emit_tutorial_update(code):
    tutorial = tutorials.get(code)
    if not tutorial:
        return

    emit("tutorial_update", tutorial, room=code, namespace="/staff")

    for student_id, data in tutorial["students"].items():
        group_number = data.get("group")
        group = tutorial["groups"].get(group_number)
        members = [tutorial["students"][sid].get("name") for sid in group] if group else None
        payload = {
            "name": tutorial["name"],
            "state": tutorial["state"],
            "group_number": group_number,
            "group_members": members,
            "questions": tutorial["questions"],
            "tutorial_code": code
        }
        emit("student_update", payload, room=student_id)

    # Alternative: Upload all Groups to all Students - Filter on Frontend using UUID
    # payload = {
    #     "name": tutorial["name"],
    #     "state": tutorial["state"],
    #     "groups": tutorial["groups"]
    # }
    # emit("students_update", payload, room=code)


def _join_tutorial(user_id, code, namespace):
    if tutorial := tutorials.get(code, None):
        users[user_id]["tutorial"] = code

        if users[user_id]["role"] == "student":
            if user_id not in tutorial["students"]:
                tutorial["students"][user_id] = {
                    "name": session.get("name"),
                    "currentGPA": session.get("currentGPA"),
                    "goalGPA": session.get("goalGPA"),
                    "availability": session.get("availability"),
                    "group": None
                }
                session.pop("student_details", None)
                session.pop("currentGPA", None)
                session.pop("goalGPA", None)
                session.pop("availability", None)
            join_room(code, namespace=namespace)
        elif users[user_id]["role"] == "staff":
            join_room(code, namespace=namespace)

        join_room(user_id, namespace=namespace)
        _emit_tutorial_update(code)
    else:
        emit("fail", {"message": "Tutorial not found"}, namespace=namespace)


def multi_namespace_event(event, namespaces):
    def decorator(f):
        for ns in namespaces:
            socketio.on(event, namespace=ns)(f)
        return f
    return decorator


# -----------------------------
# Socket lifecycle
# -----------------------------


@multi_namespace_event("disconnect", ["/", "/staff"])
def disconnect():
    if user_id := sessions.pop(request.sid, None):
        users[user_id]["sessions"].discard(request.sid)

        if code := users[user_id]["tutorial"]:
            users[user_id]["tutorial"] = None

            if tutorial := tutorials.get(code):
                tutorial["students"].pop(user_id, None)

        if not users[user_id]["sessions"]:
            users.pop(user_id, None)
