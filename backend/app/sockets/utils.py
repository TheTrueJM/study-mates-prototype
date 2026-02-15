import random
import string
import uuid
import threading
import logging
import time

from flask import session, request
from flask_socketio import emit, join_room
from .. import socketio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

users = dict() # { UUID: {sessions: {sID, ...}, role: student|staff, tutorial: code, disconnected_at: float|None}, ... }
sessions = dict() # { sID: UUID }
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
        code  = ''.join(random.choices(string.ascii_uppercase, k=length))
        if code not in tutorials:
            return code


def _cleanup_stale_users(code):
    if not (tutorial := tutorials.get(code)):
        disconnected_students.pop(code, None)
        return

    now = time.time()
    threshold = now - RECONNECT_GRACE_PERIOD

    if not (disconnected := disconnected_students.get(code)):
        return

    if not (stale_ids := [sid for sid, ts in disconnected.items() if ts <= threshold]):
        return

    disconnected_students[code] = {sid: ts for sid, ts in disconnected.items() if ts > threshold}

    students = tutorial["students"]
    for student_id in stale_ids:
        students.pop(student_id, None)
        users.pop(student_id, None)


def _generate_name(tutorial):
    DESCRIPTORS = (
        'agile', 'anonymous', 'blazing', 'blissful', 'bold', 'brave', 'bright', 'calm', 'cheerful',
        'clever', 'colorful', 'cosmic',  'curious', 'daring', 'dazzling', 'energetic', 'epic',
        'friendly', 'frosty', 'gentle', 'glowing', 'golden', 'graceful', 'happy', 'hasty', 'heroic',
        'hidden', 'jolly', 'joyful', 'kind', 'legendary', 'lively', 'lunar', 'midnight', 'mighty',
        'mysterious', 'mythic', 'nimble', 'noble', 'peaceful', 'playful', 'powerful', 'quick',
        'radiant', 'rapid', 'resilient', 'royal', 'shiny', 'silent', 'silver', 'smart', 'sneaky',
        'stealthy', 'stellar', 'strong', 'swift', 'valiant', 'vibrant', 'wild', 'wise', 'witty'
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
        members = [tutorial["students"][sid].get("name") for sid in group] if group else None
        payload = {
            "username": data["name"],
            "name": tutorial["name"],
            "state": tutorial["state"],
            "group_number": group_number,
            "group_members": members,
            "questions": tutorial["questions"],
            "timer": tutorial.get("timer"),
            "tutorial_code": code
        }
        emit("student_update", payload, room=student_id, namespace="/")


def _join_tutorial(user_id, code, namespace):
    join_room(user_id, namespace=namespace)

    if not (tutorial := tutorials.get(code)) and namespace!="/staff":
        emit("error", {"message": "Tutorial not found"}, to=request.sid, namespace=namespace)
        return

    if user := users.get(user_id):
        user["disconnected_at"] = None
        if code and user.get("role") == "student":
            disconnected_students.get(code, {}).pop(user_id, None)

    users[user_id]["tutorial"] = code

    if users[user_id]["role"] == "student":
        if user_id not in tutorial["students"]:
            tutorial["students"][user_id] = {
                "name": _generate_name(tutorial),
                "currentGPA": session.get("currentGPA"),
                "goalGPA": session.get("goalGPA"),
                "availability": session.get("availability", []),
                "group": None
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
