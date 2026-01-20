import random
import string
import uuid

from flask import request
from flask_socketio import emit, join_room, leave_room

from .. import socketio

users = dict()
sessions = dict()
rooms = dict()

def get_users_in_room(room):
    return [uid for uid, data in users.items() if data["room"] == room]

def _emit_list_update(room):
    uids = get_users_in_room(room)
    payload = {"students": uids}
    if room:
        emit("list", payload, room=room)
    else:
        emit("list", payload, broadcast=True)

def _emit_room_list():
    payload = []
    print(rooms)
    for room_name, uids in rooms.items():
        room = {"room": room_name, "students": uids}
        payload.append(room)
    emit("room_list", payload, broadcast=True)

def _create_room():
    while True:
        room_name  = ''.join(random.choices(string.ascii_uppercase, k=3))
        if room_name not in rooms:
            rooms[room_name] = []
            return room_name

def _leave_room(userID):
    current_room = users[userID]["room"]
    if current_room:
        users[userID]["room"] = None
        rooms[current_room].remove(userID)

        for session_id in users[userID]["sessions"]:
            leave_room(current_room, sid=session_id)

        if not rooms[current_room]:
            del rooms[current_room]

@socketio.on("connect")
def connect(data):
    if request.sid not in sessions:
        if data is not None:
            userID = data.get("uuid", None)
            if userID is None:
                userID = str(uuid.uuid4())
        else:
            userID = str(uuid.uuid4())

        if userID not in users:
            users[userID] = {"sessions": [], "room": data.get("room", None)}

        current_room = users[userID]["room"]

        if current_room not in rooms:
            users[userID]["room"] = None
            current_room = None

        users[userID]["sessions"].append(request.sid)
        sessions[request.sid] = userID
        emit("session", {"uuid": userID, "room": current_room})
    else:
        userID = sessions.get(request.sid)
        current_room = users[userID]["room"]

    if current_room:
        join_room(current_room, sid=request.sid)

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
    new_room = _create_room()

    affected_rooms = set()
    affected_rooms.add(None)
    affected_rooms.add(new_room)

    for user_id in user_ids:
        if user_id in users:
            _leave_room(user_id)
            users[user_id]["room"] = new_room
            for session_id in users[user_id]["sessions"]:
                join_room(new_room, sid=session_id)
                rooms[new_room].append(user_id)
                emit("room_joined", {"room": new_room}, to=session_id)

    for room in affected_rooms:
        _emit_list_update(room)
    _emit_room_list()

@socketio.on("leave_room")
def leave_curr_room():
    userID = sessions.get(request.sid)
    if userID and userID in users:
        prev_room = users[userID]["room"]
        _leave_room(userID)
        emit("room_left")

        if prev_room in rooms:
            _emit_list_update(prev_room)
        _emit_list_update(None)
        _emit_room_list()

@socketio.on("get_students")
def get_students():
    user_list = []
    for user_id, user_data in users.items():
        user_list.append({
            "id": user_id,
            "room": user_data["room"],
            "sessions": len(user_data["sessions"])
        })
    emit("students_list", {"students": user_list})
