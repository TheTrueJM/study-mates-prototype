from flask import request
from flask_socketio import emit, join_room, close_room, ConnectionRefusedError
from sqlalchemy import func
from functools import wraps
import time, math

from .utils import tutorials, users, sessions, generate_unique_tutorial_code, emit_tutorial_update
from .timer import timer
from .matching import form_groups
from ..auth import verify_staff_token
from ..enums import TutorialState, DEFAULT_AVAILABLE_ATTRIBUTES, parse_available_attributes
from ..database import DiscussionQuestion


MIN_GROUP_SIZE, MAX_GROUP_SIZE = 2, 10
MIN_DISCUSSION_MINUTES, MAX_DISCUSSION_MINUTES = 1, 60
DEFAULT_DISCUSSION_MINUTES = 5
MAX_TUTORIAL_NAME_LENGTH = 60


def _error(message, **extra):
    """Emits an error to the requesting client, returning a failed acknowledgement"""
    emit("error", {"message": message, **extra}, to=request.sid, namespace="/staff")
    return {"ok": False, "message": message, **extra}


def with_tutorial_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not (user_id := sessions.get(request.sid)):
            return _error("Your session could not be found. Please refresh the page.")

        if not (code := users.get(user_id, {}).get("tutorial")):
            return _error("You are not currently running a tutorial session.")

        if not (tutorial := tutorials.get(code)):
            return _error("This tutorial session could not be found.")

        if tutorial.get("staff") != user_id:
            return _error("This tutorial session is managed by another staff member.")

        tutorial["last_activity"] = int(time.time())
        return f(user_id, code, *args, **kwargs)
    return wrapper


def register_staff_events(socketio):
    @socketio.on("connect", namespace="/staff")
    def connect(auth: dict = None):
        # Staff (guests and accounts) must provide a valid Access Token, which also identifies them, so the
        # same Staff Member resumes their Tutorial across page refreshes, tabs, and reconnections
        identity = verify_staff_token(auth.get("token") if isinstance(auth, dict) else None)
        if not identity:
            raise ConnectionRefusedError("unauthorized")

        user_id = identity["id"]
        user = users.setdefault(user_id, {"sessions": set(), "tutorial": None})
        user.update(role="staff", staff_type=identity["type"], username=identity["username"])
        user["sessions"].add(request.sid)
        sessions[request.sid] = user_id

        join_room(user_id, namespace="/staff")

        # Resume the Staff Member's running Tutorial
        code = user.get("tutorial")
        if code and tutorials.get(code, {}).get("staff") == user_id:
            join_room(code, namespace="/staff")
        else:
            user["tutorial"] = code = None

        emit("session", {"role": "staff", "code": code})

        if code:
            emit_tutorial_update(code)


    @socketio.on("disconnect", namespace="/staff")
    def disconnect(reason=None):
        user_id = sessions.pop(request.sid, None)
        if user := users.get(user_id):
            user["sessions"].discard(request.sid)
            if not user["sessions"] and not user.get("tutorial"):
                del users[user_id]


    @socketio.on("create_tutorial", namespace="/staff")
    def create_tutorial(data=None):
        user_id = sessions.get(request.sid)
        user = users.get(user_id, {})

        if user.get("role") != "staff":
            return _error("You are not authorised to create a tutorial session.")
        elif (tutorial_code := user.get("tutorial")) is not None:
            return _error("You already have a tutorial session running.", tutorial_code=tutorial_code)

        if not isinstance(data, dict):
            return _error("Invalid tutorial settings.")

        settings, error = _validate_settings(data)
        if error:
            return _error(error)

        code = generate_unique_tutorial_code()
        discussion_time = settings["discussion_time"]
        name = str(data.get("tutorial_name") or "").strip()[:MAX_TUTORIAL_NAME_LENGTH]

        tutorials[code] = {
            "staff": user_id,
            "name": name or f"Tutorial {code}",
            "state": TutorialState.LOBBY,
            "group_size": settings["group_size"],
            "max_groups": settings["max_groups"],
            "available_attributes": settings["available_attributes"],
            "students": dict(),
            "groups": dict(),
            "previous_matches": dict(),
            "questions": list(),
            "timer": {
                "duration": discussion_time,
                "remaining": discussion_time,
                "running": False
            },
            "last_activity": int(time.time())
        }

        join_tutorial(user_id, code)

        emit("tutorial_created", {"tutorial_code": code}, to=request.sid, namespace="/staff")
        return {"ok": True, "tutorial_code": code}

    @socketio.on("update_settings", namespace="/staff")
    @with_tutorial_auth
    def update_settings(user_id, code, data=None):
        if not isinstance(data, dict):
            return _error("Invalid tutorial settings.")

        tutorial = tutorials[code]
        settings, error = _validate_settings(data, current=tutorial)
        if error:
            return _error(error)

        tutorial["group_size"] = settings["group_size"]
        tutorial["max_groups"] = settings["max_groups"]
        tutorial["available_attributes"] = settings["available_attributes"]

        # Only reset the Timer when its Duration actually changes
        if settings["discussion_time"] != tutorial["timer"]["duration"]:
            tutorial["timer"]["duration"] = settings["discussion_time"]
            tutorial["timer"]["remaining"] = settings["discussion_time"]
            tutorial["timer"]["running"] = False
            timer.stop(code)

        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("return_lobby", namespace="/staff")
    @with_tutorial_auth
    def return_lobby(user_id, code, data=None):
        tutorial = tutorials[code]
        tutorial["state"] = TutorialState.LOBBY
        tutorial["groups"].clear()
        tutorial["questions"].clear()
        _reset_timer(code)

        for student in tutorial["students"].values():
            student["group"] = None

        emit_tutorial_update(code)
        return {"ok": True}

    @socketio.on("start_grouping", namespace="/staff")
    @with_tutorial_auth
    def start_grouping(user_id, code, data=None):
        tutorial = tutorials[code]

        if len(tutorial["students"]) < 2:
            return _error("At least 2 students need to join before groups can be formed.")

        try:
            groups = form_groups(tutorial)
        except Exception as e:
            return _error(f"Groups could not be formed: {e}")

        tutorial["questions"].clear()
        _reset_timer(code)

        tutorial["groups"].clear()
        tutorial["state"] = TutorialState.GROUPING

        for student in tutorial["students"].values():
            student["group"] = None

        for group_id, members in groups.items():
            tutorial["groups"][group_id] = list(members)
            for member_id in members:
                tutorial["students"][member_id]["group"] = group_id

                matches = tutorial["previous_matches"].setdefault(member_id, set())
                matches.update(other_id for other_id in members if other_id != member_id)

        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("start_discussion", namespace="/staff")
    @with_tutorial_auth
    def start_discussion(user_id, code, data=None):
        tutorial = tutorials[code]
        tutorial["state"] = TutorialState.DISCUSSION

        questions = []
        for category in ["academic", "casual", "study"]:
            question = DiscussionQuestion.query.filter_by(category_name=category).order_by(func.random()).first()
            if question:
                questions.append(question.question)
        tutorial["questions"] = questions

        tutorial["timer"]["remaining"] = tutorial["timer"]["duration"]
        tutorial["timer"]["running"] = True
        timer.start(code)

        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("start_timer", namespace="/staff")
    @with_tutorial_auth
    def start_timer(user_id, code, data=None):
        tutorial_timer = tutorials[code]["timer"]
        if tutorial_timer["remaining"] <= 0:
            tutorial_timer["remaining"] = tutorial_timer["duration"]

        tutorial_timer["running"] = True
        timer.start(code)
        emit_tutorial_update(code)
        return {"ok": True}

    @socketio.on("stop_timer", namespace="/staff")
    @with_tutorial_auth
    def stop_timer(user_id, code, data=None):
        tutorials[code]["timer"]["running"] = False
        timer.stop(code)
        emit_tutorial_update(code)
        return {"ok": True}

    @socketio.on("reset_timer", namespace="/staff")
    @with_tutorial_auth
    def reset_timer(user_id, code, data=None):
        # Resets to the current duration, unless a new valid duration (in minutes) is given
        minutes = data.get("time") if isinstance(data, dict) else None
        if minutes is not None:
            new_time, error = _validate_discussion_time(minutes)
            if error:
                return _error(error)
            tutorials[code]["timer"]["duration"] = new_time

        _reset_timer(code)
        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("end_tutorial", namespace="/staff")
    @with_tutorial_auth
    def end_tutorial(user_id, code, data=None):
        tutorial = tutorials[code]
        tutorial["timer"]["running"] = False
        timer.stop(code)
        tutorial["state"] = TutorialState.ENDED

        emit("tutorial_ended", {"tutorial_code": code}, room=code, namespace="/")
        emit("tutorial_ended", {"tutorial_code": code}, room=code, namespace="/staff")

        for student_id in tutorial.get("students", {}):
            if users.get(student_id, {}).get("tutorial") == code:
                users[student_id]["tutorial"] = None

        users[user_id]["tutorial"] = None
        del tutorials[code]

        close_room(code, namespace="/")
        close_room(code, namespace="/staff")
        return {"ok": True}


def join_tutorial(user_id, code):
    if not (user := users.get(user_id)) or user.get("role") != "staff":
        return _error("Your session could not be found. Please refresh the page.")

    if tutorials.get(code, {}).get("staff") != user_id:
        return _error("This tutorial session is managed by another staff member.")

    user["tutorial"] = code
    for sid in user.get("sessions", set()):
        join_room(code, sid=sid, namespace="/staff")

    emit_tutorial_update(code)
    return {"ok": True, "tutorial_code": code}


def _reset_timer(code):
    tutorial_timer = tutorials[code]["timer"]
    tutorial_timer["remaining"] = tutorial_timer["duration"]
    tutorial_timer["running"] = False
    timer.stop(code)


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_discussion_time(minutes):
    """Returns a tuple of the discussion time in seconds and an error message"""
    try:
        minutes = float(minutes)
    except (TypeError, ValueError):
        return None, "Invalid discussion time."

    if math.isnan(minutes) or not MIN_DISCUSSION_MINUTES <= minutes <= MAX_DISCUSSION_MINUTES:
        return None, f"Discussion time must be between {MIN_DISCUSSION_MINUTES} and {MAX_DISCUSSION_MINUTES} minutes."
    return math.ceil(minutes * 60), None


def _validate_settings(data, current=None):
    """
    Validates tutorial settings, returning a tuple of the cleaned settings and an error message.
    Settings omitted from an update keep their current value; on creation they use their defaults.
    """
    group_size = data.get("group_size", current["group_size"] if current else None)
    if not _is_int(group_size) or not MIN_GROUP_SIZE <= group_size <= MAX_GROUP_SIZE:
        return None, f"Group size must be between {MIN_GROUP_SIZE} and {MAX_GROUP_SIZE} students."

    max_groups = data.get("max_groups", current["max_groups"] if current else None)
    if max_groups is not None and (not _is_int(max_groups) or max_groups < 2):
        return None, "Maximum groups must be at least 2."

    if "discussion_time" in data or "time" in data:
        discussion_time, error = _validate_discussion_time(data.get("discussion_time", data.get("time")))
        if error:
            return None, error
    elif current:
        discussion_time = current["timer"]["duration"]
    else:
        discussion_time = DEFAULT_DISCUSSION_MINUTES * 60

    if "available_attributes" in data and data["available_attributes"] is not None:
        available_attributes = parse_available_attributes(data["available_attributes"])
        if available_attributes is None:
            return None, "Invalid student details selection."
    elif current:
        available_attributes = current["available_attributes"]
    else:
        available_attributes = list(DEFAULT_AVAILABLE_ATTRIBUTES)

    return {
        "group_size": group_size,
        "max_groups": max_groups,
        "discussion_time": discussion_time,
        "available_attributes": available_attributes,
    }, None
