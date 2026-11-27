from flask import request
from flask_socketio import emit, join_room, ConnectionRefusedError
from sqlalchemy import func
from functools import wraps
import time

from .utils import (
    tutorials, users, sessions, generate_unique_tutorial_code, emit_tutorial_update, emit_staff_update,
    record_activity, remove_student as remove_tutorial_student, close_tutorial, begin_discussion,
    apply_custom_attributes, move_to_group
)
from .timer import timer
from .matching import form_groups
from .meetings import record_meetings, get_history
from .seating import get_table, seated_tables, next_group_number
from ..auth import verify_staff_token
from ..enums import TutorialState
from ..settings import MAX_DISCUSSION_MINUTES, is_int, validate_discussion_time, validate_settings
from ..database import DiscussionQuestion


INTRODUCTION_SECONDS = 30
WRAP_UP_SECONDS = 2 * 60
TIMER_ADJUSTMENT_SECONDS = 30
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

        record_activity(code)
        return f(user_id, code, *args, **kwargs)
    return wrapper


def with_state(state, message):
    """Only allows an event while the tutorial is in the given state (used after with_tutorial_auth)"""
    def decorator(f):
        @wraps(f)
        def wrapper(user_id, code, *args, **kwargs):
            if tutorials[code]["state"] != state:
                return _error(message)
            return f(user_id, code, *args, **kwargs)
        return wrapper
    return decorator

def with_timer(f):
    """Only allows an event while the tutorial's Timer is in use (used after with_tutorial_auth)"""
    @wraps(f)
    def wrapper(user_id, code, *args, **kwargs):
        if tutorials[code]["state"] not in TIMED_STATES:
            return _error("The Timer can only be used during Introductions, a Discussion, or the Wrap-Up.")
        return f(user_id, code, *args, **kwargs)
    return wrapper

GROUPED_STATES = {TutorialState.GROUPING, TutorialState.INTRODUCTION, TutorialState.DISCUSSION}
TIMED_STATES = {TutorialState.INTRODUCTION, TutorialState.DISCUSSION, TutorialState.WRAP_UP}


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

        settings, error = validate_settings(data)
        if error:
            return _error(error)

        code = generate_unique_tutorial_code()
        discussion_time = settings["discussion_time"]
        name = str(data.get("tutorial_name") or "").strip()[:MAX_TUTORIAL_NAME_LENGTH]

        tutorials[code] = {
            "staff": user_id,
            "name": name or f"Tutorial {code}",
            "state": TutorialState.LOBBY,
            "locked": False,
            "group_size": settings["group_size"],
            "max_groups": settings["max_groups"],
            "available_attributes": settings["available_attributes"],
            "custom_attributes": settings["custom_attributes"],
            "shortlisting": settings["shortlisting"],
            "seating": settings["seating"],
            "table_numbering": False,
            "students": dict(),
            "groups": dict(),
            "previous_matches": dict(),
            "history": dict(),
            "shortlists": dict(),
            "round": 0,
            "round_discussed": False,
            "formation": 0,
            "questions": list(),
            "discussion_time": discussion_time,
            "timer": timer.create(discussion_time),
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
        settings, error = validate_settings(data, current=tutorial)
        if error:
            return _error(error)

        tutorial["group_size"] = settings["group_size"]
        tutorial["max_groups"] = settings["max_groups"]
        tutorial["available_attributes"] = settings["available_attributes"]
        apply_custom_attributes(tutorial, settings["custom_attributes"])
        tutorial["shortlisting"] = settings["shortlisting"]
        tutorial["seating"] = settings["seating"]

        # A running Discussion is only reset when its Duration actually changes
        # (Introductions keep counting down, and roll into a Discussion of the new duration)
        changed = settings["discussion_time"] != tutorial["discussion_time"]
        tutorial["discussion_time"] = settings["discussion_time"]
        if changed and tutorial["state"] == TutorialState.DISCUSSION:
            timer.reset(code, settings["discussion_time"])

        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("lock_tutorial", namespace="/staff")
    @with_tutorial_auth
    def lock_tutorial(user_id, code, data=None):
        locked = data.get("locked") if isinstance(data, dict) else None
        if not isinstance(locked, bool):
            return _error("Invalid lock setting.")

        tutorials[code]["locked"] = locked
        emit_staff_update(code)
        return {"ok": True}

    @socketio.on("remove_student", namespace="/staff")
    @with_tutorial_auth
    def remove_student(user_id, code, data=None):
        student_id = data.get("student_id") if isinstance(data, dict) else None
        if not isinstance(student_id, str) or not remove_tutorial_student(student_id, code):
            return _error("This Student is no longer in the Session.")

        emit("left_tutorial", {"tutorial_code": code, "removed": True}, room=student_id, namespace="/")
        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("move_student", namespace="/staff")
    @with_tutorial_auth
    def move_student(user_id, code, data=None):
        """
        Moves a Student into another Group, or alone into a New Group (for the Staff Member to fill).
        Students staying at their Table are only Moved once the Staff Member confirms (with `force`), such as when
        their Table Number was wrong, and then stay at the Table of their New Group.
        """
        tutorial = tutorials[code]
        if tutorial["state"] not in GROUPED_STATES or not tutorial["groups"]:
            return _error("Students can only be Moved once Groups have been Formed.")

        data = data if isinstance(data, dict) else {}
        student_id, target = data.get("student_id"), data.get("group")
        if not isinstance(student_id, str) or not (student := tutorial["students"].get(student_id)):
            return _error("This Student is no longer in the Session.")

        groups = tutorial["groups"]
        current = student.get("group")
        seated = get_table(tutorial, student) is not None

        if seated and data.get("force") is not True:
            return _error("This Student is staying at their Table, so Move the Other Students instead.", seated=True)

        if target == "new":
            if current in groups and groups[current] == [student_id]:
                return _error("This Student is already in a Group by themselves.")
            if tutorial["max_groups"] and len(groups) >= tutorial["max_groups"]:
                return _error(f"The Limit of {tutorial['max_groups']} Groups has been Reached.")
            target = next_group_number(tutorial)
        elif not is_int(target) or target not in groups:
            return _error("This Group no longer exists.")
        elif target == current:
            return _error("This Student is already in that Group.")

        move_to_group(tutorial, student_id, target)
        if seated:
            student["table"] = target

        emit("moved_group", {"group_number": target, "table": student["table"] if seated else None}, room=student_id, namespace="/")
        emit_tutorial_update(code)
        return {"ok": True, "group_number": target}


    @socketio.on("return_lobby", namespace="/staff")
    @with_tutorial_auth
    def return_lobby(user_id, code, data=None):
        tutorial = tutorials[code]
        record_meetings(tutorial) # As they were when the Groups left
        tutorial["state"] = TutorialState.LOBBY
        tutorial["table_numbering"] = False
        tutorial["groups"].clear()
        tutorial["questions"].clear()
        timer.reset(code, tutorial["discussion_time"])

        for student in tutorial["students"].values():
            student["group"] = None

        emit_tutorial_update(code)
        return {"ok": True}

    @socketio.on("start_grouping", namespace="/staff")
    @with_tutorial_auth
    def start_grouping(user_id, code, data=None):
        tutorial = tutorials[code]

        if len(tutorial["students"]) < 2:
            return _error("At least 2 Students need to join before Groups can be Formed.")

        try:
            groups = form_groups(tutorial)
        except Exception as e:
            return _error(f"Groups could not be formed: {e}")

        tutorial["questions"].clear()
        timer.reset(code, tutorial["discussion_time"])

        record_meetings(tutorial) # As they were when the Groups left
        tutorial["groups"].clear()
        tutorial["state"] = TutorialState.GROUPING
        tutorial["table_numbering"] = bool(seated_tables(tutorial)) # Groups are numbered by their Table

        # Reforming Groups before their Discussion doesn't count as another Round
        if not tutorial["round"] or tutorial["round_discussed"]:
            tutorial["round"] += 1
            tutorial["round_discussed"] = False
        tutorial["formation"] += 1

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
    @with_state(TutorialState.GROUPING, "Groups need to be Formed before a Discussion can begin.")
    def start_discussion(user_id, code, data=None):
        tutorial = tutorials[code]
        if not tutorial["groups"]:
            return _error("Groups need to be Formed before a Discussion can begin.")

        # Students first Introduce themselves, then the Discussion begins automatically (with its full time)
        tutorial["state"] = TutorialState.INTRODUCTION
        tutorial["round_discussed"] = True
        record_meetings(tutorial)

        questions = []
        for category in ["academic", "casual", "study"]:
            question = DiscussionQuestion.query.filter_by(category_name=category).order_by(func.random()).first()
            if question:
                questions.append(question.question)
        tutorial["questions"] = questions

        timer.reset(code, INTRODUCTION_SECONDS)
        timer.start(code)

        emit_tutorial_update(code)
        return {"ok": True}

    @socketio.on("skip_introduction", namespace="/staff")
    @with_tutorial_auth
    @with_state(TutorialState.INTRODUCTION, "Introductions have already finished.")
    def skip_introduction(user_id, code, data=None):
        begin_discussion(code)
        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("start_timer", namespace="/staff")
    @with_tutorial_auth
    @with_timer
    def start_timer(user_id, code, data=None):
        if timer.get_remaining(tutorials[code]["timer"]) <= 0:
            timer.reset(code)

        timer.start(code)
        emit_tutorial_update(code)
        return {"ok": True}

    @socketio.on("stop_timer", namespace="/staff")
    @with_tutorial_auth
    @with_timer
    def stop_timer(user_id, code, data=None):
        timer.stop(code)
        emit_tutorial_update(code)
        return {"ok": True}

    @socketio.on("reset_timer", namespace="/staff")
    @with_tutorial_auth
    @with_timer
    def reset_timer(user_id, code, data=None):
        # Resets to the current duration, unless a new valid Discussion duration (in minutes) is given
        tutorial = tutorials[code]
        new_time = None
        minutes = data.get("time") if isinstance(data, dict) else None
        if minutes is not None:
            if tutorial["state"] != TutorialState.DISCUSSION:
                return _error("The Discussion time can only be changed during a Discussion.")
            new_time, error = validate_discussion_time(minutes)
            if error:
                return _error(error)
            tutorial["discussion_time"] = new_time

        timer.reset(code, new_time)
        emit_tutorial_update(code)
        return {"ok": True}

    @socketio.on("adjust_timer", namespace="/staff")
    @with_tutorial_auth
    @with_timer
    def adjust_timer(user_id, code, data=None):
        # Only the current Discussion is adjusted (the next one returns to the tutorial's duration)
        seconds = data.get("seconds") if isinstance(data, dict) else None
        if seconds not in (TIMER_ADJUSTMENT_SECONDS, -TIMER_ADJUSTMENT_SECONDS) or isinstance(seconds, bool):
            return _error("Invalid timer adjustment.")

        remaining = timer.get_remaining(tutorials[code]["timer"])
        if seconds > 0 and remaining + seconds > MAX_DISCUSSION_MINUTES * 60:
            return _error(f"Discussion time can't be more than {MAX_DISCUSSION_MINUTES} minutes.")
        if seconds < 0 and remaining <= 0:
            return _error("The Timer has already finished.")

        timer.adjust(code, seconds)
        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("wrap_up", namespace="/staff")
    @with_tutorial_auth
    def wrap_up(user_id, code, data=None):
        """
        Ends the tutorial's activities, giving everyone time to return to their seats and swap details.
        The countdown is only a guide, as the Session stays open until the Staff Member closes it.
        """
        tutorial = tutorials[code]
        if tutorial["state"] == TutorialState.WRAP_UP:
            return _error("The Session is already Wrapping Up.")

        record_meetings(tutorial) # As they were when the Groups left
        tutorial["state"] = TutorialState.WRAP_UP
        tutorial["questions"].clear()
        timer.reset(code, WRAP_UP_SECONDS)
        timer.start(code)

        emit_tutorial_update(code)

        # Mutual Shortlists are revealed now
        if tutorial["shortlisting"]:
            for student_id in tutorial["students"]:
                mutuals = sum(entry["mutual"] for entry in get_history(tutorial, student_id))
                if mutuals:
                    emit("mutual_shortlist", {"count": mutuals}, room=student_id, namespace="/")
        return {"ok": True}

    @socketio.on("end_tutorial", namespace="/staff")
    @with_tutorial_auth
    def end_tutorial(user_id, code, data=None):
        close_tutorial(code)
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
