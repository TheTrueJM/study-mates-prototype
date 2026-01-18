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

def _create_room():
    while True:
        room_name  = ''.join(random.choices(string.ascii_uppercase, k=3))
        if room_name not in rooms:
            rooms[room_name] = []
            return room_name

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
            users[userID] = {"sessions": [], "room": None}

        users[userID]["sessions"].append(request.sid)
        sessions[request.sid] = userID
        emit("session", {"uuid": userID})
    else:
        userID = sessions.get(request.sid)

    current_room = users[userID]["room"]

    if current_room:
        join_room(current_room, sid=request.sid)
        room_users = len(get_users_in_room(current_room))
        emit("list", {"students": room_users}, room=current_room, broadcast=True)
    else:
        room_users = len(get_users_in_room(None))
        emit("list", {"students": room_users}, broadcast=True)

@socketio.on("disconnect")
def disconnect():
    userID = sessions.get(request.sid, None)

    if userID in users:
        current_room = users[userID]["room"]
        if current_room:
            leave_room(current_room, sid=request.sid)

        users[userID]["sessions"].remove(request.sid)

        if not users[userID]["sessions"]:
            del users[userID]
        del sessions[request.sid]

        if current_room:
            room_users = len(get_users_in_room(current_room))
            emit("list", {"students": room_users}, room=current_room, broadcast=True)
        else:
            room_users = len(get_users_in_room(None))
            emit("list", {"students": room_users}, broadcast=True)

@socketio.on("create_room")
def create_room():
    room_name = _create_room()
    emit("room_created", {"room": room_name})

@socketio.on("assign_room")
def assign_room(data):
    user_ids = data.get("users", [])
    new_room = data.get("room", None)

    if not new_room:
        return

    for user_id in user_ids:
        if user_id in users:
            current_room = users[user_id]["room"]
            if current_room:
                # todo: restrict to x maximum number of sessions allowed
                for session_id in users[user_id]["sessions"]:
                    leave_room(current_room, sid=session_id)

            users[user_id]["room"] = new_room
            for session_id in users[user_id]["sessions"]:
                join_room(new_room, sid=session_id)
                emit("room_joined", {"room": new_room}, to=session_id)

        old_room_users = get_users_in_room(current_room)
        lobby_users = get_users_in_room(None)
        emit("list", {"users": len(old_room_users)}, room=current_room, broadcast=True)
        emit("list", {"users": len(lobby_users)}, broadcast=True)

@socketio.on("leave_room")
def leave_curr_room():
    userID = sessions.get(request.sid)
    if userID and userID in users:
        current_room = users[userID]["room"]
        if current_room:
            users[userID]["room"] = None
            for session_id in users[userID]["sessions"]:
                leave_room(current_room, sid=session_id)

            emit("room_left")

            old_room_users = get_users_in_room(current_room)
            lobby_users = get_users_in_room(None)
            emit("list", {"users": len(old_room_users)}, room=current_room, broadcast=True)
            emit("list", {"users": len(lobby_users)}, broadcast=True)

@socketio.on("get_users")
def get_users():
    user_list = []
    for user_id, user_data in users.items():
        user_list.append({
            "id": user_id,
            "room": user_data["room"],
            "sessions": len(user_data["sessions"])
        })
    emit("users_list", {"users": user_list})
