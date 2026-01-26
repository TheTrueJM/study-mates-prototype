from flask import request, session
from flask_socketio import emit, join_room, leave_room
from .. import socketio

import random, string, uuid


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
    
    emit("tutorial_update", tutorial, room=f"staff:{code}")

    for student_id, data in tutorial["students"].items():
        group_number = data.get("group")
        group = tutorial["groups"].get(group_number)
        members = [tutorial["students"][sid].get("name") for sid in group] if group else None
        payload = {
            "name": tutorial["name"],
            "state": tutorial["state"],
            "group_number": group_number,
            "group_members": members,
            "questions": tutorial["questions"]
        }
        emit("student_update", payload, room=student_id)

    # Alternative: Upload all Groups to all Students - Filter on Frontend using UUID
    # payload = {
    #     "name": tutorial["name"],
    #     "state": tutorial["state"],
    #     "groups": tutorial["groups"]
    # }
    # emit("students_update", payload, room=code)


# -----------------------------
# Socket lifecycle
# -----------------------------


@socketio.on("connect")
def connect(auth):
    user_id = auth.get("uuid") if auth else None
    role = session.get("role", "student")
    code = session.get("tutorial_code")

    if not user_id: user_id = str(uuid.uuid4())

    if user_id not in users:
        users[user_id] = {
            "sessions": set(),
            "role": role,
            "tutorial": None
        }

    users[user_id]["sessions"].add(request.sid)
    sessions[request.sid] = user_id

    emit("session", {"uuid": user_id})

    # Auto-join tutorial if provided
    if code and code in tutorials:
        _join_tutorial(user_id, code)


@socketio.on("disconnect")
def disconnect():
    if user_id := sessions.pop(request.sid, None):
        users[user_id]["sessions"].discard(request.sid)

        if code := users[user_id]["tutorial"]:
            users[user_id]["tutorial"] = None

            if tutorial := tutorials.get(code):
                tutorial["students"].pop(user_id)

        if not users[user_id]["sessions"]:
            users.pop(user_id, None)


# -----------------------------
# Tutorial management
# -----------------------------


@socketio.on("create_tutorial")
def create_tutorial(data):
    user_id = sessions.get(request.sid)
    if not user_id or users[user_id]["role"] != "staff":
        return

    name = data.get("name")
    group_size = int(data.get("group_size")) or None
    # Discussion Questions, Discussion Time

    if not group_size or group_size < 2:
        emit("create_failed")
        return

    code = _generate_code()

    tutorials[code] = {
        "staff": user_id,
        "name": name,
        "state": "lobby",
        "group_size": group_size,
        "students": dict(),
        "groups": dict(),
        "questions": list(),
    }

    users[user_id]["tutorial"] = code
    join_room(f"staff:{code}")

    emit("tutorial_created", {"code": code})


@socketio.on("join_tutorial")
def join_tutorial(data):
    code = data.get("code")

    user_id = sessions.get(request.sid)
    if not user_id or code not in tutorials:
        emit("join_failed")
        return

    _join_tutorial(user_id, code)


def _join_tutorial(user_id, code):
    if tutorial := tutorials.get(code):
        users[user_id]["tutorial"] = code
        join_room(code)
        join_room(user_id) # personal room

        if users[user_id]["role"] == "student":
            name = session.get("name") # Error if no name?
            details = session.get("student_details", dict())
            tutorial["students"][user_id] = {
                "name": name,
                "details": details,
                "group": None
            }

        elif users[user_id]["role"] == "staff":
            join_room(f"staff:{code}")

        _emit_tutorial_update(code)


@socketio.on("reset_lobby")
def reset_lobby():
    user_id = sessions.get(request.sid)
    code = users[user_id]["tutorial"]
    tutorial = tutorials.get(code)

    if tutorial and tutorial["staff"] == user_id:
        tutorial["state"] = "lobby"
        tutorial["groups"].clear()
        tutorial["questions"].clear()

        _emit_tutorial_update(code)


# -----------------------------
# Grouping
# -----------------------------

@socketio.on("start_grouping")
def start_grouping():
    user_id = sessions.get(request.sid)

    if user_id:
        code = users[user_id]["tutorial"]
        tutorial = tutorials.get(code)

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

            _emit_tutorial_update(code)


# -----------------------------
# Discussion
# -----------------------------


@socketio.on("start_discussion")
def start_discussion():
    user_id = sessions.get(request.sid)
    code = users[user_id]["tutorial"]
    tutorial = tutorials.get(code)

    if tutorial and tutorial["staff"] == user_id:
        tutorial["state"] = "discussion"

        # Placeholder: questions = db.get_questions(code)
        questions = ["Question Test1", "Question Test2", "Question Test3"]
        tutorial["questions"] = questions
        # emit("discussion_started", {"questions": questions}, room=code)

        _emit_tutorial_update(code)