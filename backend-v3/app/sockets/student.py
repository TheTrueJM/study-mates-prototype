from flask import request
from flask_socketio import emit, join_room, leave_room
from functools import wraps

from .utils import tutorials, users, sessions, generate_unique_user_uuid, generate_unique_student_name, emit_tutorial_update
from ..enums import TutorialState, AttributeType, VALID_ATTRIBUTES, VALID_GRADES, VALID_MEETING_MODE, parse_availability, parse_communication


def with_tutorial_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not (user_id := sessions.get(request.sid)):
            emit("error", {"message": "User Session Not Found"}, to=request.sid)
            return

        if not (code := users.get(user_id, {}).get("tutorial")):
            emit("error", {"message": "Not in a Tutorial"}, to=request.sid)
            return

        if not (tutorial := tutorials.get(code)):
            emit("error", {"message": "Tutorial Not Found"}, to=request.sid)
            return

        if user_id not in tutorial.get("students", []):
            emit("error", {"message": "Not Authorised"}, to=request.sid)
            return

        return f(user_id, code, *args, **kwargs)
    return wrapper


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

        join_room(user_id, namespace="/")

        tutorial_code = auth.get("code") if isinstance(auth, dict) else None
        if tutorial_code:
            previous_tutorial = users[user_id]["tutorial"]
            if previous_tutorial and previous_tutorial in tutorials:
               leave_tutorial(user_id, previous_tutorial)
            
            if tutorial_code in tutorials:
                join_tutorial(user_id, tutorial_code)
            else:
                users[user_id]["tutorial"] = None

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


    @socketio.on("enter_tutorial")
    def enter_tutorial(data):
        user_id = sessions.get(request.sid)
        user = users.get(user_id, {})

        if user.get("role") != "student":
            emit("error", {"message": "Not Authorised"}, to=request.sid)
            return

        if not (code := data.get("code")):
            emit("error", {"message": "Tutorial Code Required"}, to=request.sid)
            return

        join_tutorial(user_id, code)

    # TODO Verify if Necessary
    # @socketio.on("fetch_tutorial", namespace="/staff")
    # @with_tutorial_auth
    # def fetch_tutorial(user_id, code, tutorial):
    #     emit_tutorial_update(code)


    @socketio.on("update_details")
    @with_tutorial_auth
    def update_details(user_id, code, data):
        if not isinstance(data, dict):
            socketio.emit("error", {"message": "Invalid Data Format"}, to=request.sid)
            return

        current_gpa = data.get(AttributeType.CURRENT_GPA)
        goal_grade = data.get(AttributeType.GOAL_GRADE)
        availability = data.get(AttributeType.AVAILABILITY)
        communication = data.get(AttributeType.COMMUNICATION)
        meeting_mode = data.get(AttributeType.MEETING_MODE)
        year = data.get(AttributeType.YEAR)
        semester = data.get(AttributeType.SEMESTER)
        accessibility = data.get(AttributeType.ACCESSIBILITY) # TODO Implement into Matching

        tutorials[code]["students"][user_id]["attributes"].setdefault(AttributeType.CURRENT_GPA, None)

        available_attributes = tutorials[code]["available_attributes"]
        student_attributes = tutorials[code]["students"][user_id]["attributes"]

        student_attributes.setdefault(AttributeType.CURRENT_GPA)
        if AttributeType.CURRENT_GPA in available_attributes and current_gpa:
            if current_gpa not in VALID_GRADES:
                socketio.emit("error", {"message": "Invalid Current GPA"}, to=request.sid)
            else:
                student_attributes[AttributeType.CURRENT_GPA] = current_gpa

        student_attributes.setdefault(AttributeType.GOAL_GRADE)
        if AttributeType.GOAL_GRADE in available_attributes and goal_grade:
            if goal_grade not in VALID_GRADES:
                socketio.emit("error", {"message": "Invalid Goal Grade"}, to=request.sid)
            else:
                student_attributes[AttributeType.GOAL_GRADE] = goal_grade

        student_attributes.setdefault(AttributeType.AVAILABILITY, [])
        if AttributeType.AVAILABILITY in available_attributes and availability:
            if parsed_availability := parse_availability(availability):
                student_attributes[AttributeType.AVAILABILITY] = parsed_availability

        student_attributes.setdefault(AttributeType.COMMUNICATION, [])
        if AttributeType.COMMUNICATION in available_attributes and communication:
            if parsed_communication:= parse_communication(communication):
                student_attributes[AttributeType.COMMUNICATION] = parsed_communication

        student_attributes.setdefault(AttributeType.MEETING_MODE)
        if AttributeType.MEETING_MODE in available_attributes and meeting_mode:
            if meeting_mode not in VALID_MEETING_MODE:
                socketio.emit("error", {"message": "Invalid Meeting Mode"}, to=request.sid)
            else:
                student_attributes[AttributeType.MEETING_MODE] = meeting_mode
        
        student_attributes.setdefault(AttributeType.YEAR, [])
        if AttributeType.YEAR in available_attributes and year:
            if not isinstance(year, int) and year < 1 or year > 10:
                socketio.emit("error", {"message": "Invalid Study Year"}, to=request.sid)
            else:
                student_attributes[AttributeType.YEAR] = year

        student_attributes.setdefault(AttributeType.SEMESTER, [])
        if AttributeType.SEMESTER in available_attributes and semester:
            if not isinstance(semester, int) and semester < 1 or semester > 2:
                socketio.emit("error", {"message": "Invalid Study Semester"}, to=request.sid)
            else:
                student_attributes[AttributeType.SEMESTER] = semester

        tutorials[code]["students"][user_id]["attributes"] = student_attributes

        shared_attributes = set(data.get("shared_attributes")) if isinstance(data.get("shared_attributes"), list) else set()
        tutorials[code]["students"][user_id]["shared_attributes"] = list(shared_attributes & VALID_ATTRIBUTES)
                
        # TODO Move this elsewhere to a details confirmation (this regular update details can occur on each attribute input)
        tutorials[code]["students"][user_id]["attributes_complete"] = True
        
        emit(
            "details_updated",
            {
                "attributes": tutorials[code]["students"][user_id]["attributes"],
                "shared_attributes":tutorials[code]["students"][user_id]["shared_attributes"]
            },
            to=request.sid, namespace="/"
        )

        emit_tutorial_update(code)


    @socketio.on("leave_tutorial")
    @with_tutorial_auth
    def leave_tutorial(user_id, code):
        del tutorials[code]["students"][user_id]
        users[user_id]["tutorial"] = None

        leave_room(code, namespace="/")
        emit("left_tutorial", to=request.sid, namespace="/")


    # TODO Verify if Necessary
    # @socketio.on("reset_session")
    # def reset_session():
    #     if not (user_id := utils.sessions.get(request.sid)):
    #         emit("error", ERR_SESSION_NOT_FOUND, to=request.sid)
    #         return

    #     code = utils.users.get(user_id, {}).get("tutorial")
    #     if code and code in utils.tutorials:
    #         tutorial = utils.tutorials[code]
    #         if user_id in tutorial.get("students", {}):
    #             student_data = tutorial["students"].get(user_id, {})
    #             group_id = student_data.get("group")

    #             utils.users[user_id]["last_group"] = group_id

    #             tutorial["students"].pop(user_id, None)

    #             # Clean up from groups
    #             for group_id, members in tutorial.get("groups", {}).items():
    #                 if user_id in members:
    #                     members[:] = [m for m in members if m != user_id]
            
    #         utils._emit_tutorial_update(code)

    #     utils.users[user_id]["tutorial"] = None

    #     emit("session_cleared", {"message": "Session cleared"}, to=request.sid)


def join_tutorial(user_id, code):
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
        late_assignment_to_group(code, user_id)

    join_room(code, namespace="/")

    emit_tutorial_update(code)


def late_assignment_to_group(tutorial_code, student_id):
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