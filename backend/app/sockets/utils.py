import random
import string
import uuid
import threading
import logging
import time

from flask import session, request
from flask_socketio import emit, join_room
from .. import socketio
from .errors import ERR_TUTORIAL_NOT_FOUND

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tutorials = dict()
disconnected_students = dict()  # { code: { user_id: disconnected_at, ... } }

RECONNECT_GRACE_PERIOD = 5.0  # seconds

# {
#   code: {
#       staff: UUID,
#       name: name,
#       state: lobby|groups|discussion,
#       group_size: size,
#       students: { UUID, ... },
#       groups: { id: [ UUID, ... ], ... },
#       questions: [question, ...],
#       timer: { duration: int, remaining: int, running: bool }
#   },
#   ...
# }


# -----------------------------
# Helpers
# -----------------------------


def _generate_code(length=6):
    while True:
        if code not in tutorials:
            return code


def _cleanup_stale_users(code):
    if not (tutorial := tutorials.get(code)):
        disconnected_students.pop(code, None)
        return

    now = time.time()
    threshold = now - RECONNECT_GRACE_PERIOD
    student_threshold = now - RECONNECT_GRACE_PERIOD
    staff_threshold = now - STAFF_RECONNECT_GRACE_PERIOD

    if staff_disconnect_time := disconnected_staff.get(code):
        if staff_disconnect_time <= staff_threshold:
            _close_tutorial(code)
            return

    if not (disconnected := disconnected_students.get(code)):
        return

    if not (stale_ids := [sid for sid, ts in disconnected.items() if ts <= threshold]):
    if not (
        stale_ids := [
            sid for sid, ts in disconnected.items() if ts <= student_threshold
        ]
    ):
        return

    disconnected_students[code] = {sid: ts for sid, ts in disconnected.items() if ts > threshold}
    disconnected_students[code] = {
        sid: ts for sid, ts in disconnected.items() if ts > student_threshold
    }

    students = tutorial["students"]
    for student_id in stale_ids:
        if users.get(student_id) and users[student_id].get("sessions"):
            continue
        students.pop(student_id, None)
        users.pop(student_id, None)


def _generate_name(tutorial):
    DESCRIPTORS = (
    )
    ANIMALS = (
        'armadillo', 'badger', 'bear', 'beaver', 'cat', 'chameleon', 'cheetah', 'chicken', 'cockatoo',
        'coyote', 'jackal', 'crow', 'dog', 'dolphin', 'duck', 'eagle', 'falcon', 'fish', 'flamingo',
        'fox', 'hawk', 'hedgehog', 'horse', 'jaguar', 'jellyfish', 'kangaroo', 'koala', 'leopard',
        'lion', 'lizard', 'meerkat', 'otter', 'owl', 'panda', 'panther', 'parrot', 'penguin', 'rabbit',
        'raccoon', 'raven', 'salamander', 'seal', 'serpent', 'shark', 'sheep', 'sloth', 'snake',
        'squirrel', 'swan', 'tiger', 'tortoise', 'turtle', 'wallaby', 'walrus', 'wolf', 'wombat', 'zebra'
    )
    names = {student["name"] for student in tutorial["students"].values()}
    while True:
        name = f"{random.choice(DESCRIPTORS).title()}-{random.choice(ANIMALS).title()}"
        if name not in names:
            return name


def _close_tutorial(code):
    from .timer import timer

    if not (tutorial := tutorials.get(code)):
        return

    staff_id = tutorial.get("staff")

    timer.stop(code)

    emit("tutorial_ended", {}, room=code, namespace="/")

    student_ids = list(tutorial.get("students", {}).keys())
    for student_id in student_ids:
        if student_id in users:
            users[student_id]["tutorial"] = None
            emit("session_cleared", {}, room=student_id, namespace="/")

    if staff_id and staff_id in users:
        users[staff_id]["tutorial"] = None
        staff_sessions = users[staff_id].get("sessions", set())
        if staff_sessions:
            staff_sid = sessions.get(list(staff_sessions)[0])
            if staff_sid:
                socketio.emit("tutorial_deleted", {}, to=staff_sid, namespace="/staff")

    tutorials.pop(code, None)
    disconnected_students.pop(code, None)
    disconnected_staff.pop(code, None)

    logger.info(f"Tutorial {code} closed")


def _emit_tutorial_update(code):
    tutorial = tutorials.get(code)
    if not tutorial:
        return

    _cleanup_stale_users(code)

    staff_payload = {
        "tutorial_code": code,
        "name": tutorial["name"],
        "state": tutorial["state"],
        "students": tutorial["students"],
        "groups": tutorial["groups"],
        "questions": tutorial["questions"],
        "timer": tutorial.get("timer"),
    }
    emit("tutorial_update", staff_payload, room=code, namespace="/staff")

    for student_id, data in tutorial["students"].items():
        group_number = data.get("group")
        group = tutorial["groups"].get(group_number)
        members = [tutorial["students"][sid].get("name") for sid in group if sid in tutorial["students"]] if group else None
        members = (
            [
                {
                    "name": tutorial["students"][sid].get("name"),
                    "availability": tutorial["students"][sid].get("availability", []),
                }
                for sid in group
                if sid in tutorial["students"]
            ]
            if group
            else None
        )
        payload = {
            "username": data["name"],
            "name": tutorial["name"],
            "state": tutorial["state"],
            "group_number": group_number,
            "group_members": members,
            "questions": tutorial["questions"],
            "timer": tutorial.get("timer"),
        }
        emit("student_update", payload, room=student_id, namespace="/")


def _join_tutorial(user_id, code, namespace):
    join_room(user_id, namespace=namespace)

        emit("error", ERR_TUTORIAL_NOT_FOUND, to=request.sid, namespace=namespace)
        return

    if user := users.get(user_id):
        user["disconnected_at"] = None
        if code and user.get("role") == "student":
            disconnected_students.get(code, {}).pop(user_id, None)
        if code:
            if user.get("role") == "student":
                disconnected_students.get(code, {}).pop(user_id, None)
            elif user.get("role") == "staff":
                disconnected_staff.pop(code, None)

    if code:
        users[user_id]["tutorial"] = code

    if users[user_id]["role"] == "student":
        if user_id not in tutorial["students"]:
            tutorial["students"][user_id] = {
                "name": _generate_name(tutorial),
                "currentGPA": session.get("currentGPA", 4.5),
                "goalGPA": session.get("goalGPA", 4.0),
                "availability": session.get("availability", []),
            }
            session.pop("student_details", None)
            session.pop("currentGPA", None)
            session.pop("goalGPA", None)
            session.pop("availability", None)
        join_room(code, namespace=namespace)
    elif users[user_id]["role"] == "staff":
        join_room(code, namespace=namespace)

    _emit_tutorial_update(code)


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
        if user := users.get(user_id):
            user["sessions"].discard(request.sid)

            if not user["sessions"]:
                user["disconnected_at"] = time.time()
                if (code := user.get("tutorial")) and user.get("role") == "student":
                    if code not in disconnected_students:
                        disconnected_students[code] = {}
                    disconnected_students[code][user_id] = user["disconnected_at"]
                if code := user.get("tutorial"):
                    if user.get("role") == "student":
                        if code not in disconnected_students:
                            disconnected_students[code] = {}
                        disconnected_students[code][user_id] = user["disconnected_at"]
                    elif user.get("role") == "staff":
                        disconnected_staff[code] = user["disconnected_at"]
