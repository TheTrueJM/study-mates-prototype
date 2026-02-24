import random
import string
import uuid
import threading
import logging
import time

from flask import session, request
from flask_socketio import emit, join_room
from .. import socketio
from .errors import ERR_TUTORIAL_NOT_FOUND, ERR_SESSION_NOT_FOUND, ERR_UNAUTHORISED

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

users = dict() # { UUID: {sessions: {sID, ...}, role: student|staff, tutorial: code, disconnected_at: float|None}, ... }
sessions = dict() # { sID: UUID }
tutorials = dict()
disconnected_students = dict()  # { code: { user_id: disconnected_at, ... } }
disconnected_staff = dict()  # { code: disconnected_at, ... }

RECONNECT_GRACE_PERIOD = 5.0  # seconds
STAFF_RECONNECT_GRACE_PERIOD = 30.0  # seconds

_DAY = {
    "MON": "Monday",
    "TUE": "Tuesday",
    "WED": "Wednesday",
    "THU": "Thursday",
    "FRI": "Friday",
    "SAT": "Saturday",
    "SUN": "Sunday",
}
_TIME = {"M": "Morning", "A": "Afternoon", "E": "Evening"}
_day_idx = {k: i for i, k in enumerate(_DAY.keys())}
_time_idx = {k: i for i, k in enumerate(_TIME.keys())}
_fmt_avail = lambda c: (
    f"{_DAY.get(c[:3], c[:3])}-{_TIME.get(c[3:], c[3:])}" if len(c) == 4 else c
)
_fmt_to_code = {v: k for k, v in _DAY.items()}
_time_to_code = {v: k for k, v in _TIME.items()}


def _sort_avail(codes):
    return sorted(
        codes, key=lambda c: (_day_idx.get(c[:3], 9), _time_idx.get(c[3:], 9))
    )


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
        disconnected_staff.pop(code, None)
        return

    now = time.time()
    student_threshold = now - RECONNECT_GRACE_PERIOD
    staff_threshold = now - STAFF_RECONNECT_GRACE_PERIOD

    if disconnected := disconnected_students.get(code):
        stale_ids = [sid for sid, ts in disconnected.items() if ts <= student_threshold]
        disconnected_students[code] = {
            sid: ts for sid, ts in disconnected.items() if ts > student_threshold
        }

        students = tutorial.get("students", {})
        for student_id in stale_ids:
            if users.get(student_id) and users[student_id].get("sessions"):
                continue
            students.pop(student_id, None)
            users.pop(student_id, None)

    staff_disconnect_time = disconnected_staff.get(code)
    if staff_disconnect_time and staff_disconnect_time <= staff_threshold:
        staff_id = tutorial.get("staff")
        emit("tutorial_ended", room=code, namespace="/")
        for student_id in list(tutorial.get("students", {}).keys()):
            if student_id in users:
                users[student_id]["tutorial"] = None
        tutorials.pop(code, None)
        disconnected_students.pop(code, None)
        disconnected_staff.pop(code, None)
        if staff_id and staff_id in users:
            users[staff_id]["tutorial"] = None


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
    names = {student["name"] for student in tutorial.get("students", {}).values()}
    while True:
        name = f"{random.choice(DESCRIPTORS).title()}-{random.choice(ANIMALS).title()}"
        if name not in names:
            return name


def _emit_tutorial_update(code):
    tutorial = tutorials.get(code)
    if not tutorial:
        emit("error", ERR_TUTORIAL_NOT_FOUND, room=code, namespace="/")
        return

    _cleanup_stale_users(code)

    staff_payload = {
        "tutorial_code": code,
        "name": tutorial.get("name"),
        "state": tutorial.get("state"),
        "students": tutorial.get("students", {}),
        "groups": tutorial.get("groups", {}),
        "questions": tutorial.get("questions", []),
        "timer": tutorial.get("timer"),
    }
    emit("tutorial_update", staff_payload, room=code, namespace="/staff")

    for student_id, data in tutorial.get("students", {}).items():
        group_number = data.get("group")
        group = tutorial.get("groups", {}).get(group_number)
        students = tutorial.get("students", {})
        members = (
            [
                {
                    "name": students.get(sid, {}).get("name"),
                    "availability": [
                        _fmt_avail(a)
                        for a in _sort_avail(
                            students.get(sid, {}).get("availability", [])
                        )
                    ],
                }
                for sid in group
                if sid in students
            ]
            if group
            else None
        )
        payload = {
            "username": data.get("name"),
            "name": tutorial.get("name"),
            "state": tutorial.get("state"),
            "group_number": group_number,
            "group_members": members,
            "questions": tutorial.get("questions", []),
            "timer": tutorial.get("timer"),
            "tutorial_code": code
        }
        emit("student_update", payload, room=student_id, namespace="/")


def _join_tutorial(user_id, code, namespace):
    join_room(user_id, namespace=namespace)

    if not (tutorial := tutorials.get(code)) and namespace!="/staff":
        emit("error", ERR_TUTORIAL_NOT_FOUND, to=request.sid, namespace=namespace)
        return

    if user := users.get(user_id):
        user["disconnected_at"] = None
        if code and user.get("role") == "student":
            disconnected_students.get(code, {}).pop(user_id, None)
        elif code and user.get("role") == "staff":
            disconnected_staff.pop(code, None)
    else:
        emit("error", ERR_SESSION_NOT_FOUND, to=request.sid, namespace=namespace)
        return

    if code and user:
        user["tutorial"] = code

    if user and user.get("role") == "student" and tutorial:
        tutorial.setdefault("students", {})
        if user_id not in tutorial.get("students", {}):
            tutorial["students"][user_id] = {
                "name": _generate_name(tutorial),
                "currentGPA": session.get("currentGPA", 4.5),
                "goalGPA": session.get("goalGPA", 4.0),
                "availability": session.get("availability", []),
                "group": None
            }
            #session.pop("student_details", None)
            #session.pop("currentGPA", None)
            #session.pop("goalGPA", None)
            #session.pop("availability", None)
        join_room(code, namespace=namespace)
    elif user and user.get("role") == "staff":
        join_room(code, namespace=namespace)
    else: # no tutorial
        emit("error", ERR_TUTORIAL_NOT_FOUND, to=request.sid, namespace=namespace)
        user["tutorial"] = None
        return

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
                elif (code := user.get("tutorial")) and user.get("role") == "staff":
                    disconnected_staff[code] = user["disconnected_at"]
