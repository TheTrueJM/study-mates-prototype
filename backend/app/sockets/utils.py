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

users = dict()  # { UUID: {sessions: {sID, ...}, role: student|staff, tutorial: code, disconnected_at: float|None}, ... }
sessions = dict()  # { sID: UUID }
tutorials = dict()
disconnected_students = dict()  # { code: { user_id: disconnected_at, ... } }
disconnected_staff = dict()  # { code: disconnected_at, ... }

RECONNECT_GRACE_PERIOD = 5.0  # seconds
STAFF_RECONNECT_GRACE_PERIOD = 30.0  # seconds

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
        code = "".join(random.choices(string.ascii_uppercase, k=length))
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

        students = tutorial["students"]
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
        "agile",
        "anonymous",
        "blazing",
        "blissful",
        "bold",
        "brave",
        "bright",
        "calm",
        "cheerful",
        "clever",
        "colorful",
        "cosmic",
        "curious",
        "daring",
        "dazzling",
        "energetic",
        "epic",
        "friendly",
        "frosty",
        "gentle",
        "glowing",
        "golden",
        "graceful",
        "happy",
        "hasty",
        "heroic",
        "hidden",
        "jolly",
        "joyful",
        "kind",
        "legendary",
        "lively",
        "lunar",
        "midnight",
        "mighty",
        "mysterious",
        "mythic",
        "nimble",
        "noble",
        "peaceful",
        "playful",
        "powerful",
        "quick",
        "radiant",
        "rapid",
        "resilient",
        "royal",
        "shiny",
        "silent",
        "silver",
        "smart",
        "sneaky",
        "stealthy",
        "stellar",
        "strong",
        "swift",
        "valiant",
        "vibrant",
        "wild",
        "wise",
        "witty",
    )
    ANIMALS = (
        "armadillo",
        "badger",
        "bear",
        "beaver",
        "cat",
        "chameleon",
        "cheetah",
        "chicken",
        "cockatoo",
        "coyote",
        "jackal",
        "crow",
        "dog",
        "dolphin",
        "duck",
        "eagle",
        "falcon",
        "fish",
        "flamingo",
        "fox",
        "hawk",
        "hedgehog",
        "horse",
        "jaguar",
        "jellyfish",
        "kangaroo",
        "koala",
        "leopard",
        "lion",
        "lizard",
        "meerkat",
        "otter",
        "owl",
        "panda",
        "panther",
        "parrot",
        "penguin",
        "rabbit",
        "raccoon",
        "raven",
        "salamander",
        "seal",
        "serpent",
        "shark",
        "sheep",
        "sloth",
        "snake",
        "squirrel",
        "swan",
        "tiger",
        "tortoise",
        "turtle",
        "wallaby",
        "walrus",
        "wolf",
        "wombat",
        "zebra",
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
            "tutorial_code": code,
        }
        emit("student_update", payload, room=student_id, namespace="/")


def _join_tutorial(user_id, code, namespace):
    join_room(user_id, namespace=namespace)

    if not (tutorial := tutorials.get(code)) and namespace != "/staff":
        emit("error", ERR_TUTORIAL_NOT_FOUND, to=request.sid, namespace=namespace)
        return

    if user := users.get(user_id):
        user["disconnected_at"] = None
        if code and user.get("role") == "student":
            disconnected_students.get(code, {}).pop(user_id, None)
        elif code and user.get("role") == "staff":
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
                "group": None,
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
                elif (code := user.get("tutorial")) and user.get("role") == "staff":
                    disconnected_staff[code] = user["disconnected_at"]
