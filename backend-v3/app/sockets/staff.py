from flask import request
from flask_socketio import emit, join_room, leave_room
# from flask_jwt_extended import jwt_required
from sqlalchemy import func
from functools import wraps
import time, math

from .utils import tutorials, users, sessions, generate_unique_user_uuid, generate_unique_tutorial_code, emit_tutorial_update
from .timer import timer
from .matching import form_groups
from ..enums import TutorialState
from ..database import DiscussionQuestion


def with_tutorial_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not (user_id := sessions.get(request.sid)):
            emit("error", {"message": "User Session Not Found"}, to=request.sid, namespace="/staff")
            return

        if not (code := users.get(user_id, {}).get("tutorial")):
            emit("error", {"message": "Not in a Tutorial"}, to=request.sid, namespace="/staff")
            return

        if not (tutorial := tutorials.get(code)):
            emit("error", {"message": "Tutorial Not Found"}, to=request.sid, namespace="/staff")
            return

        if tutorial.get("staff") != user_id:
            emit("error", {"message": "Not Authorised"}, to=request.sid, namespace="/staff")
            return

        return f(user_id, code, *args, **kwargs)
    return wrapper


def register_staff_events(socketio):
    @socketio.on("connect", namespace="/staff")
    def connect(auth: dict = None):
        # TODO Validate JWT (for all requests as wrapper or maybe just this?)
        print(f"DEBUG: Staff socket connected with auth: {auth}")

        user_id = auth.get("uuid") if isinstance(auth, dict) else None

        if user_id not in users:
            user_id = generate_unique_user_uuid()
            users[user_id] = {
                "sessions": set(),
                "tutorial": None
            }

        join_room(user_id, namespace="/staff")

        tutorial_code = auth.get("code") if isinstance(auth, dict) else None
        if tutorial_code:
            previous_tutorial = users[user_id]["tutorial"]
            if previous_tutorial and previous_tutorial != tutorial_code and previous_tutorial in tutorials:
                end_tutorial(user_id, previous_tutorial)
            
            users[user_id]["tutorial"] = None
            if tutorial_code in tutorials:
                join_tutorial(user_id, tutorial_code)

        users[user_id]["role"] = "staff"
        users[user_id]["sessions"].add(request.sid)
        sessions[request.sid] = user_id

        emit("session",
            {
                "uuid": user_id,
                "role": users[user_id]["role"],
                "code": users[user_id]["tutorial"]
            }
        )
        print(f"DEBUG: Session emitted for user {user_id}")



    @socketio.on("create_tutorial", namespace="/staff")
    def create_tutorial(data):
        print(f"DEBUG: Create tutorial called with data: {data}")

        user_id = sessions.get(request.sid)
        user = users.get(user_id, {})

        if user.get("role") != "staff":
            emit("error", {"message": "Not Authorised"}, to=request.sid, namespace="/staff")
            return
        elif (tutorial := user.get("tutorial")) is not None:
            emit(
                "error",
                {"message": "Already in Tutorial", "tutorial_code": tutorial},
                to=request.sid, namespace="/staff",
            )
            return
        
        if not isinstance(data, dict):
            socketio.emit("error", {"message": "Invalid Data Format"}, to=request.sid, namespace="/staff")
            return

        tutorial_name = data.get("tutorial_name")
        group_size = data.get("group_size")
        max_groups = data.get("max_groups")
        available_attributes = data.get("available_attributes")

        try:
            discussion_time = math.ceil(float(data.get("discussion_time") or data.get("time")) * 60)
        except Exception:
            discussion_time = 5 * 60

        if not isinstance(group_size, int) or group_size < 2:
            socketio.emit("error", {"message": "Invalid Group Size"}, to=request.sid, namespace="/staff")
            return
        
        if max_groups and (not isinstance(max_groups, int) or max_groups < 2):
            socketio.emit("error", {"message": "Invalid Maximum Groups"}, to=request.sid, namespace="/staff")
            return
        
        if not isinstance(available_attributes, list):
            socketio.emit("error", {"message": "Invalid Attributes Available"}, to=request.sid, namespace="/staff")
            return

        code = generate_unique_tutorial_code()

        tutorials[code] = {
            "staff": user_id,
            "name": tutorial_name,
            "state": TutorialState.LOBBY,
            "group_size": group_size,
            "max_groups": max_groups,
            "available_attributes": available_attributes,
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

        users[user_id]["tutorial"] = code
        join_tutorial(user_id, code)

        emit("tutorial_created", {"tutorial_code": code}, to=request.sid, namespace="/staff")

    @socketio.on("update_settings", namespace="/staff")
    @with_tutorial_auth
    def update_settings(user_id, code, data):
        # TODO Improve Validation Modularity of with Tutorial Creation
        tutorials[code]["last_activity"] = int(time.time())

        new_group_size = data.get("group_size")
        new_max_groups = data.get("max_groups")
        new_available_attributes = data.get("available_attributes")

        try:
            new_discussion_time = math.ceil(float(data.get("time")) * 60)
        except Exception:
            new_discussion_time = 5 * 60

        if not isinstance(new_group_size, int) or new_group_size < 2:
            socketio.emit("error", {"message": "Invalid Group Size"}, to=request.sid, namespace="/staff")
            return
        
        if new_max_groups and (not isinstance(new_max_groups, int) or new_max_groups < 2):
            socketio.emit("error", {"message": "Invalid Maximum Groups"}, to=request.sid, namespace="/staff")
            return
        
        if not isinstance(new_available_attributes, list):
            socketio.emit("error", {"message": "Invalid Attributes Available"}, to=request.sid, namespace="/staff")
            return

        tutorial = tutorials[code]
        tutorial["group_size"] = new_group_size
        tutorial["max_groups"] = new_max_groups
        tutorial["available_attributes"] = new_available_attributes
        tutorial["timer"]["duration"] = new_discussion_time
        tutorial["timer"]["remaining"] = new_discussion_time
        tutorial["timer"]["running"] = False
        timer.stop(code)
        emit_tutorial_update(code)

    # TODO Verify if Necessary
    # @socketio.on("fetch_tutorial", namespace="/staff")
    # @_with_tutorial_auth
    # def fetch_tutorial(user_id, code, tutorial):
    #     emit_tutorial_update(code)


    @socketio.on("return_lobby", namespace="/staff")
    @with_tutorial_auth
    def return_lobby(user_id, code):
        tutorials[code]["last_activity"] = int(time.time())

        tutorials[code]["state"] = TutorialState.LOBBY
        tutorials[code]["groups"].clear()
        tutorials[code]["questions"].clear()
        tutorials[code]["timer"]["running"] = False
        timer.stop(code)

        for student_id in tutorials[code]["students"]:
            tutorials[code]["students"][student_id]["group"] = None

        emit_tutorial_update(code)

    @socketio.on("start_grouping")
    @with_tutorial_auth
    def start_grouping(user_id, code):
        tutorials[code]["last_activity"] = int(time.time())

        tutorials[code]["questions"].clear()
        tutorials[code]["timer"]["running"] = False
        timer.stop(code)
        
        tutorials[code]["groups"].clear()
        tutorials[code]["state"] = TutorialState.GROUPING

        try:
            groups = form_groups(tutorials[code])

            for group_id, members in groups.items():
                for member_id in members:
                    tutorials[code]["groups"][group_id].append(member_id)
                    tutorials[code]["students"][member_id]["group"] = group_id

                    tutorials[code]["previous_matches"].setdefault(member_id, set())
                    for other_member_id in members:
                        if other_member_id != member_id:
                            tutorials[code]["previous_matches"][member_id].add(other_member_id)
        
        except Exception as e:
            socketio.emit("error", {"message": e.message}, to=request.sid, namespace="/staff")
            return

        emit_tutorial_update(code)


    @socketio.on("start_discussion", namespace="/staff")
    @with_tutorial_auth
    def start_discussion(user_id, code):
        tutorials[code]["last_activity"] = int(time.time())

        tutorials[code]["state"] = TutorialState.DISCUSSION
        tutorials[code]["timer"]["remaining"] = tutorials[code]["timer"]["duration"]
        tutorials[code]["timer"]["running"] = True
        timer.start(code)

        academic = DiscussionQuestion.query.filter_by(category_name="academic").order_by(func.random()).first()
        casual = DiscussionQuestion.query.filter_by(category_name="casual").order_by(func.random()).first()
        study = DiscussionQuestion.query.filter_by(category_name="study").order_by(func.random()).first()

        questions = [academic.question, casual.question, study.question]
        tutorials[code]["questions"] = questions

        emit_tutorial_update(code)


    @socketio.on("start_timer", namespace="/staff")
    @with_tutorial_auth
    def start_timer(user_id, code):
        tutorials[code]["last_activity"] = int(time.time())

        tutorials[code]["timer"]["running"] = True
        timer.start(code)
        emit_tutorial_update(code)

    @socketio.on("stop_timer", namespace="/staff")
    @with_tutorial_auth
    def stop_timer(user_id, code):
        tutorials[code]["last_activity"] = int(time.time())

        tutorials[code]["timer"]["running"] = False
        timer.stop(code)
        emit_tutorial_update(code)

    @socketio.on("reset_timer", namespace="/staff")
    @with_tutorial_auth
    def reset_timer(user_id, code, data):
        tutorials[code]["last_activity"] = int(time.time())

        # TODO Copy Validation Strategy from Creation/Update
        try:
            new_time = math.ceil(float(data.get("time")) * 60)
        except Exception:
            new_time = 5 * 60
        
        tutorials[code]["timer"]["duration"] = new_time
        tutorials[code]["timer"]["remaining"] = new_time
        tutorials[code]["timer"]["running"] = False
        timer.stop(code)
        emit_tutorial_update(code)


    @socketio.on("end_tutorial", namespace="/staff")
    @with_tutorial_auth
    def end_tutorial(user_id, code):
        tutorials[code]["timer"]["running"] = False
        timer.stop(code)

        tutorials[code]["state"] = TutorialState.ENDED
        emit("tutorial_ended", room=code, namespace="/")
        emit("tutorial_ended", room=code, namespace="/staff")

        student_ids = list(tutorials[code].get("students", {}).keys())
        for student_id in student_ids:
            if student_id in users:
                users[student_id]["tutorial"] = None
                # TODO Leave Tutorial Rooms on Student End?
                emit("left_tutorial", room=student_id, namespace="/")

        users[user_id]["tutorial"] = None
        del tutorials[code]

        leave_room(code, namespace="/staff")
        emit("left_tutorial", to=request.sid, namespace="/staff")


def join_tutorial(user_id, code):
    if not (user := users.get(user_id)) or not isinstance(user, dict):
        emit("error", {"message": "User Session Not Found"}, to=request.sid, namespace="/staff")
        return

    if user.get("role") != "staff":
        emit("error", {"message": "Invalid User Role"}, to=request.sid, namespace="/staff")
        return
    
    if tutorials.get(code, {}).get("staff") != user_id:
        emit("error", {"message": "Tutorial Managed by Another Staff User"}, to=request.sid, namespace="/staff")
        return

    user["tutorial"] = code
    join_room(code, namespace="/staff")

    emit_tutorial_update(code)