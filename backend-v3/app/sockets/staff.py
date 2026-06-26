from flask import request
from flask_socketio import emit, join_room, leave_room
# from flask_jwt_extended import jwt_required
from functools import wraps
import math

from .utils import tutorials, users, sessions, generate_unique_user_uuid, generate_unique_tutorial_code, emit_tutorial_update
from .timer import timer
from .matching import form_groups
from ..enums import TutorialState


def _with_tutorial_auth(f):
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

        if tutorial["staff"] != user_id:
            emit("error", {"message": "Not Authorised"}, to=request.sid, namespace="/staff")
            return

        return f(user_id, code, tutorial, *args, **kwargs)
    return wrapper


def register_staff_events(socketio):
    @socketio.on("connect", namespace="/staff")
    def connect(auth: dict = None):
        # TODO Validate JWT (for all requests or maybe just this?)

        user_id = auth.get("uuid") if isinstance(auth, dict) else None

        if user_id not in users:
            user_id = generate_unique_user_uuid()
            users[user_id] = {
                "sessions": set(),
                "tutorial": None
            }

        tutorial_code = auth.get("code") if isinstance(auth, dict) else None
        if tutorial_code:
            previous_tutorial = users[user_id]["tutorial"]
            if previous_tutorial and previous_tutorial in tutorials:
                pass # TODO End Previous Tutorial
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


    @socketio.on("create_tutorial", namespace="/staff")
    def create_tutorial(data):
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

        tutorial_name = data.get("name")
        group_size = data.get("group_size")
        max_groups = data.get("max_groups")
        available_attributes = data.get("available_attributes")

        try:
            discussion_time = math.ceil(float(data.get("time")) * 60)
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
            }
        }

        users[user_id]["tutorial"] = code
        join_room(code, namespace="/staff")

        emit("tutorial_created", {"tutorial_code": code}, namespace="/staff")

    @socketio.on("update_settings", namespace="/staff")
    @_with_tutorial_auth
    def update_settings(user_id, code, data):
        # TODO Improve Validation Modularity of with Tutorial Creation
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
    @_with_tutorial_auth
    def return_lobby(user_id, code):
        tutorial = tutorials[code]
        tutorial["state"] = TutorialState.LOBBY
        tutorial["groups"].clear()
        tutorial["questions"].clear()
        tutorial["timer"]["running"] = False
        timer.stop(code)

        for student_id in tutorial["students"]:
            tutorial["students"][student_id]["group"] = None

        emit_tutorial_update(code)

    @socketio.on("start_grouping")
    def start_grouping(user_id, code):
        tutorials[code]["questions"].clear()
        tutorials[code]["timer"]["running"] = False
        timer.stop(code)
        
        tutorials[code]["groups"].clear()
        tutorials[code]["state"] = TutorialState.GROUPING

        try:
            groups = form_groups(tutorials[code])
        
            # for group_id, members in groups.items():
            #     for member_uuid in members:
            #         if member_uuid not in tutorials[tutorial_code]["previous_matches"]:
            #             tutorials[tutorial_code]["previous_matches"][member_uuid] = set()
            #         # Add all other members of this group to previous matches
            #         for other_member_uuid in members:
            #             if other_member_uuid != member_uuid:
            #                 tutorials[tutorial_code]["previous_matches"][member_uuid].add(other_member_uuid)
        
        except Exception as e:
            socketio.emit("error", {"message": e.message}, to=request.sid, namespace="/staff")
            return

        # Emit groups formed event
        # socketio.emit("groups_formed", {"groups": groups}, room=f"tutorial_{tutorial_code}")


def join_tutorial(user_id, code):
    join_room(user_id, namespace="/staff")

    if not (user := users.get(user_id)) or not isinstance(user, dict):
        emit("error", {"message": "User Session Not Found"}, to=request.sid, namespace="/staff")
        return

    if user.get("role") != "staff":
        emit("error", {"message": "Invalid User Role"}, to=request.sid, namespace="/staff")
        return

    user["tutorial"] = code
    join_room(code, namespace="/staff")

    emit_tutorial_update(code)