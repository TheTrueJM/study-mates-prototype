import random
import string
import uuid

from flask import request
from flask_socketio import emit, join_room, leave_room

from .. import socketio

users = dict()
sessions = dict()
rooms = dict({
    "CAB000": {
         "students": [],
         "subrooms": {
             "CAB001": {
                 "students": [],
                 "subrooms": None
             }
         }
    },
})

def get_users_in_room(room, path=None):
    if not path:
        return [
            uid
            for uid, data in users.items()
            if data.get("room") == room
        ]

def _get_room_path(room_name):
    path = []
    if room_name in rooms:
        path.append(room_name)
        return path
    elif not room_name:
        return path

    for parent in rooms:
        if room_name in rooms[parent]["subrooms"]:
            path.extend([parent,room_name]) # parent -> subroom
            return path
    return path

def _find_user_room(user_id):
    for room_name, room_info in rooms.items():
        if user_id in room_info["students"]:
            return room_name
        subrooms = room_info.get("subrooms") or {}
        for subroom_name, subroom_info in subrooms.items():
            if user_id in subroom_info["students"]:
                return subroom_name
    return None

def _emit_list_update(room, path=None):
    uids = get_users_in_room(room, path=path)
    payload = {"students": uids}

    print(uids)

    if room:
        emit("list", payload, room=room)
    else:
        emit("list", payload, broadcast=True)

def _emit_room_list():
    payload = []
    for room_name, room_info in rooms.items():
        uids = room_info["students"]
        subrooms = room_info["subrooms"]
        room = {"room": room_name, "students": uids, "subrooms": subrooms}
        payload.append(room)
    emit("room_list", payload, broadcast=True)

def _create_room():
    while True:
        room_name  = ''.join(random.choices(string.ascii_uppercase, k=3))
        if room_name not in rooms:
            rooms[room_name] = {
                "students": [],
                "subrooms": {}
            }
            return room_name

def _leave_room(userID):
    path = _get_room_path(users[userID]["room"])

    if path:
        users[userID]["room"] = None

        if len(path)>1:
            parent = path[0]
            subroom = path[1]
            current_room = subroom
            students = rooms[parent]["subrooms"][subroom]["students"]
        else:
            current_room = path[0]
            students = rooms[path[0]]["students"]

        if userID in students:
            students.remove(userID)

        for session_id in users[userID]["sessions"]:
            leave_room(current_room, sid=session_id)
            path = _get_room_path(current_room)
            parent, subroom = path[0], path[1] if len(path) > 1 else None
            emit("room_left", {"parent": parent, "subroom": subroom}, to=session_id)
        _emit_list_update(current_room)

def _join_room(userID, room_name):
    path = _get_room_path(room_name)

    if path:
        users[userID]["room"] = room_name

        if len(path)>1:
            parent = path[0]
            subroom = path[1]
            students = rooms[parent]["subrooms"][subroom]["students"]
        else:
            students = rooms[path[0]]["students"]

        if userID not in students:
            students.append(userID)

        for session_id in users[userID]["sessions"]:
            join_room(room_name, sid=session_id)
            path = _get_room_path(room_name)

            parent = path[0]
            parent, subroom = path[0], (path[1] if len(path)>1 else None)
            emit("room_joined", {"parent": parent, "subroom": subroom}, to=session_id)
        _emit_list_update(room_name)

@socketio.on("connect")
def connect(data):
    if request.sid not in sessions:
        if data is not None:
            userID = data.get("uuid", None)
            role = data.get("role", "student")
            if userID is None:
                userID = str(uuid.uuid4())
        else:
            userID = str(uuid.uuid4())
            role = "student"

        if userID not in users:
            existing_room = _find_user_room(userID)
            users[userID] = {"sessions": [], "room": existing_room, "role": role}
        else:
            users[userID]["role"] = role

        current_room = users[userID]["room"]

        if current_room and not _get_room_path(current_room):
            users[userID]["room"] = None
            current_room = None

        users[userID]["sessions"].append(request.sid)
        sessions[request.sid] = userID
        emit("session", {"uuid": userID, "room": current_room})
    else:
        userID = sessions.get(request.sid)
        current_room = users[userID]["room"]

    if current_room:
        path = _get_room_path(current_room)
        parent = path[0]
        subroom = path[1] if len(path) > 1 else None
        join_room(current_room, sid=request.sid)
        emit("room_joined", {"parent": parent, "subroom": subroom}, sid=request.sid)

    _emit_list_update(current_room)
    _emit_room_list()

@socketio.on("disconnect")
def disconnect():
    userID = sessions.get(request.sid, None)

    if userID in users:
        current_room = users[userID]["room"]
        users[userID]["sessions"].remove(request.sid)

        if not users[userID]["sessions"]:
            del users[userID]
        del sessions[request.sid]

        _emit_list_update(current_room)

@socketio.on("create_room")
def create_room():
    room_name = _create_room()
    emit("room_created", {"room": room_name})

@socketio.on("assign_room")
def assign_room(data):
    user_ids = data.get("students", [])
    target_room = data.get("room_name")
    # is_subroom = data.get("is_subroom", False)

    for user_id in user_ids:
        _leave_room(user_id)
        _join_room(user_id, target_room)
    _emit_room_list()

@socketio.on("leave_room")
def leave_curr_room():
    userID = sessions.get(request.sid)
    if userID and userID in users:
        prev_room = users[userID]["room"]
        _leave_room(userID)
        curr_room = users[userID]["room"]

        if not curr_room:
            path = _get_room_path(prev_room)
            if len(path)>1:
                _join_room(userID, path[0])
                _emit_list_update(path[0])

        if prev_room in rooms:
            _emit_list_update(prev_room)
        _emit_room_list()

@socketio.on("get_students")
def get_students(data):
    user_list = []
    current_room = users[data["uuid"]]["room"]
    for user_id, user_data in users.items():

        if user_data["room"] == current_room:
            user_list.append({
                "id": user_id,
                "room": user_data["room"],
                "sessions": len(user_data["sessions"]),
                "role": user_data.get("role", "student")
            })
    emit("students_list", {"students": user_list})

@socketio.on("create_room")
def create_room(data):
    room_name = data.get("name")
    parent_name = data.get("parent")

    if not room_name:
        while True:
            room_name = ''.join(random.choices(string.ascii_uppercase, k=3))
            if room_name not in rooms:
                break

    if not parent_name:
        if room_name not in rooms:
            rooms[room_name] = {
                "students": [],
                "subrooms": None
            }
    else:
        if parent_name in rooms:
            parent = rooms[parent_name]
            if parent["subrooms"] is None:
                parent["subrooms"] = {}
            if room_name not in parent["subrooms"]:
                parent["subrooms"][room_name] = {
                    "students": [],
                    "subrooms": None
                }

    _emit_room_list()
