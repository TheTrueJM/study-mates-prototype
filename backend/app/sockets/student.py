from flask import request
from flask_socketio import emit, join_room
from functools import wraps
import secrets

from .utils import (
    tutorials, users, sessions, MAX_STUDENTS, generate_unique_user_uuid, generate_unique_student_name,
    emit_tutorial_update, emit_staff_update, record_activity, remove_student, get_shareable_attributes
)
from ..custom_attributes import validate_custom_value
from . import meetings
from ..enums import (
    TutorialState, AttributeType, VALID_GRADES, VALID_MEETING_MODE, SHAREABLE_ATTRIBUTES, DEFAULT_SHARED_ATTRIBUTES,
    MIN_STUDY_YEAR, MAX_STUDY_YEAR, MIN_STUDY_SEMESTER, MAX_STUDY_SEMESTER, parse_availability, parse_communication
)


def _error(message):
    """Emits an error to the requesting client, returning a failed acknowledgement"""
    emit("error", {"message": message}, to=request.sid, namespace="/")
    return {"ok": False, "message": message}


def with_tutorial_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not (user_id := sessions.get(request.sid)):
            return _error("Your session could not be found. Please refresh the page.")

        if not (code := users.get(user_id, {}).get("tutorial")):
            return _error("You are not currently in a tutorial session.")

        if not (tutorial := tutorials.get(code)):
            return _error("This tutorial session could not be found.")

        if user_id not in tutorial.get("students", {}):
            return _error("You are not a member of this tutorial session.")

        return f(user_id, code, *args, **kwargs)
    return wrapper


def register_student_events(socketio):
    @socketio.on("connect", namespace="/")
    def connect(auth: dict = None):
        user_id = auth.get("uuid") if isinstance(auth, dict) else None

        # Only an Existing Student's Identity can be resumed (never a Staff Member's)
        if not isinstance(user_id, str) or users.get(user_id, {}).get("role") != "student":
            user_id = generate_unique_user_uuid()
            users[user_id] = {
                "sessions": set(),
                "tutorial": None
            }

        user = users[user_id]
        user["role"] = "student"
        user["sessions"].add(request.sid)
        sessions[request.sid] = user_id

        join_room(user_id, namespace="/")

        # Resume the Student's existing Tutorial (e.g. after a page refresh or network reconnection)
        code = user.get("tutorial")
        if code and user_id in tutorials.get(code, {}).get("students", {}):
            join_room(code, namespace="/")
        else:
            user["tutorial"] = code = None

        emit("session", {"uuid": user_id, "role": "student", "code": code})

        if code:
            emit_tutorial_update(code)


    @socketio.on("disconnect", namespace="/")
    def disconnect(reason=None):
        user_id = _remove_session(request.sid)
        if code := users.get(user_id, {}).get("tutorial"):
            emit_staff_update(code)


    @socketio.on("enter_tutorial", namespace="/")
    def enter_tutorial(data=None):
        user_id = sessions.get(request.sid)
        if users.get(user_id, {}).get("role") != "student":
            return {"ok": False, "message": "Your session could not be found. Please refresh the page."}

        code = data.get("code") if isinstance(data, dict) else None
        code = code.strip().upper() if isinstance(code, str) else ""
        if not code:
            return {"ok": False, "message": "Please enter a tutorial code."}

        return join_tutorial(user_id, code)


    @socketio.on("update_details", namespace="/")
    @with_tutorial_auth
    def update_details(user_id, code, data=None):
        """Updates any provided details (a null or empty value clears the detail) and the shared details"""
        if not isinstance(data, dict):
            return _error("Invalid details format.")

        tutorial = tutorials[code]
        student = tutorial["students"][user_id]
        available_attributes = set(tutorial["available_attributes"])
        custom_attributes = {definition["id"]: definition for definition in tutorial["custom_attributes"]}
        attributes = student["attributes"]
        errors = []

        for attribute in available_attributes:
            if attribute not in data:
                continue

            if attribute in custom_attributes:
                value, error = validate_custom_value(custom_attributes[attribute], data[attribute])
            else:
                value, error = _validate_attribute(attribute, data[attribute])
            if error:
                errors.append(error)
            else:
                attributes[attribute] = value

        if "shared_attributes" in data:
            if isinstance(data["shared_attributes"], list):
                shared_attributes = {attribute for attribute in data["shared_attributes"] if isinstance(attribute, str)}
                student["shared_attributes"] = sorted(shared_attributes & get_shareable_attributes(tutorial))
            else:
                errors.append("Invalid shared details.")

        record_activity(code)
        emit_tutorial_update(code)

        if errors:
            message = " ".join(errors)
            emit("error", {"message": message}, to=request.sid, namespace="/")
            return {"ok": False, "message": message}
        return {"ok": True}


    @socketio.on("confirm_details", namespace="/")
    @with_tutorial_auth
    def confirm_details(user_id, code, data=None):
        tutorials[code]["students"][user_id]["attributes_complete"] = True
        record_activity(code)
        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("shortlist", namespace="/")
    @with_tutorial_auth
    def shortlist(user_id, code, data=None):
        """Adds (or Removes) a Classmate the Student has Met to their Shortlist of potential Teammates"""
        tutorial = tutorials[code]
        if not tutorial.get("shortlisting"):
            return _error("Shortlisting isn't turned on for this Session.")

        data = data if isinstance(data, dict) else {}
        public_id, shortlisted = data.get("id"), data.get("shortlisted")
        if not isinstance(public_id, str) or not isinstance(shortlisted, bool):
            return _error("Invalid shortlist change.")
        if not meetings.can_shortlist(tutorial, user_id, public_id):
            return _error("You can only Shortlist Classmates you've Met.")

        wrapping_up = tutorial["state"] == TutorialState.WRAP_UP
        shortlist = tutorial["shortlists"].setdefault(user_id, set())

        if shortlisted:
            shortlist.add(public_id)
        else:
            # Once revealed, a Mutual Shortlist stays (the other Student has already been told)
            if wrapping_up and meetings.is_mutual(tutorial, user_id, public_id):
                return _error("You've both Shortlisted each other, so they've already been told.")
            shortlist.discard(public_id)

        # Students who Shortlist each other during the Wrap-Up are both told straight away
        other_id = meetings.find_student(tutorial, public_id)
        if shortlisted and wrapping_up and meetings.is_mutual(tutorial, user_id, public_id):
            students = tutorial["students"]
            for student_id, other in ((user_id, other_id), (other_id, user_id)):
                emit("mutual_shortlist", {"name": students[other]["name"]}, room=student_id, namespace="/")

        record_activity(code)
        emit_tutorial_update(code)
        return {"ok": True}


    @socketio.on("leave_tutorial", namespace="/")
    @with_tutorial_auth
    def leave_tutorial(user_id, code, data=None):
        remove_student(user_id, code)
        emit("left_tutorial", {"tutorial_code": code}, room=user_id, namespace="/")
        emit_tutorial_update(code)
        return {"ok": True}


def join_tutorial(user_id, code):
    if not (tutorial := tutorials.get(code)):
        return {"ok": False, "message": "No session was found with that code. Check the code and try again."}

    if not (user := users.get(user_id)) or user.get("role") != "student":
        return {"ok": False, "message": "Your session could not be found. Please refresh the page."}

    # Students already in the Tutorial can always return to it
    if user_id not in tutorial["students"]:
        if tutorial["locked"]:
            return {"ok": False, "message": "This Session is Locked, so no one else can Join. Ask your Tutor to Unlock it."}
        if tutorial["state"] == TutorialState.WRAP_UP:
            return {"ok": False, "message": "This Session is Finishing Up, so no one else can Join."}
        if len(tutorial["students"]) >= MAX_STUDENTS:
            return {"ok": False, "message": "This Session is Full."}

    # Leave any Other Tutorial the Student was previously in
    previous_code = user.get("tutorial")
    if previous_code and previous_code != code and previous_code in tutorials:
        remove_student(user_id, previous_code)
        emit_tutorial_update(previous_code)

    user["tutorial"] = code

    # Joining a Tutorial the Student is already in resumes their Existing Details
    if user_id not in tutorial["students"]:
        tutorial["students"][user_id] = {
            "name": generate_unique_student_name(code),
            "attributes": dict(),
            "shared_attributes": sorted(set(DEFAULT_SHARED_ATTRIBUTES) | (
                get_shareable_attributes(tutorial) - SHAREABLE_ATTRIBUTES
            )),
            "attributes_complete": False,
            "group": None,
            "public_id": _generate_public_id(tutorial),
        }

        if tutorial.get("state") in {TutorialState.GROUPING, TutorialState.INTRODUCTION, TutorialState.DISCUSSION}:
            late_assignment_to_group(code, user_id)

    for sid in user.get("sessions", set()):
        join_room(code, sid=sid, namespace="/")

    record_activity(code)
    emit("tutorial_joined", {"tutorial_code": code}, room=user_id, namespace="/")
    emit_tutorial_update(code)

    return {"ok": True, "tutorial_code": code}


def late_assignment_to_group(tutorial_code, student_id):
    tutorial = tutorials.get(tutorial_code, {})
    students = tutorial.get("students", {})
    groups = tutorial.get("groups", {})

    if not groups or not students.get(student_id):
        return False

    best_group_id = min(groups.keys(), key=lambda group_id: len(groups[group_id]))

    groups[best_group_id].append(student_id)
    students[student_id]["group"] = best_group_id
    if tutorial["state"] in meetings.MEETING_STATES:
        meetings.record_group(tutorial, best_group_id)
    return True


def _generate_public_id(tutorial):
    used = {student.get("public_id") for student in tutorial["students"].values()}
    public_id = secrets.token_hex(6)
    while public_id in used:
        public_id = secrets.token_hex(6)
    return public_id


def _validate_attribute(attribute, value):
    """Returns a tuple of the cleaned attribute value (None or [] if cleared) and an error message"""
    match attribute:
        case AttributeType.CURRENT_GPA.value | AttributeType.GOAL_GRADE.value:
            if value in (None, ""):
                return None, None
            grade = _to_int(value)
            if grade not in VALID_GRADES:
                label = "current GPA" if attribute == str(AttributeType.CURRENT_GPA) else "goal grade"
                return None, f"Invalid {label}."
            return grade, None

        case AttributeType.AVAILABILITY.value:
            return parse_availability(value), None

        case AttributeType.COMMUNICATION.value:
            return parse_communication(value), None

        case AttributeType.MEETING_MODE.value:
            if value in (None, ""):
                return None, None
            if not isinstance(value, str) or value not in VALID_MEETING_MODE:
                return None, "Invalid meeting mode."
            return value, None

        case AttributeType.YEAR.value:
            if value in (None, ""):
                return None, None
            year = _to_int(value)
            if year is None or not MIN_STUDY_YEAR <= year <= MAX_STUDY_YEAR:
                return None, "Invalid year of study."
            return year, None

        case AttributeType.SEMESTER.value:
            if value in (None, ""):
                return None, None
            semester = _to_int(value)
            if semester is None or not MIN_STUDY_SEMESTER <= semester <= MAX_STUDY_SEMESTER:
                return None, "Invalid semester of study."
            return semester, None

    return None, None


def _to_int(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _remove_session(sid):
    """
    Forgets a closed connection, returning the ID of its User.
    The user (and their tutorial membership) remains so they can reconnect.
    """
    user_id = sessions.pop(sid, None)
    if user := users.get(user_id):
        user["sessions"].discard(sid)
        if not user["sessions"] and not user.get("tutorial"):
            del users[user_id]
    return user_id
