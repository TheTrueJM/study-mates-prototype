from flask import session, request
from sqlalchemy import func
import jwt, time, math

from . import tutorials, users
from .utils import generate_tutorial_code
from ..enums import TutorialState
from ..database.models import DiscussionQuestion


def register_staff_events(socketio):
    @socketio.on("connect")
    def handle_staff_connect():
        # Check if JWT is provided in auth parameter
        auth = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not auth: # No token, disconnect
            socketio.disconnect()
            return
        
        try: # Verify JWT
            payload = jwt.decode(auth, app.config["JWT_SECRET_KEY"], algorithms=[app.config["JWT_ALGORITHM"]])
            
            # Store staff ID in session and join global staff room
            session["staff_id"] = payload["user_id"]
            socketio.enter_room("staff_global")
        except jwt.ExpiredSignatureError: # Expired token, disconnect
            socketio.disconnect()
            return
        except jwt.InvalidTokenError: # Invalid token, disconnect
            socketio.disconnect()
            return
    

    @socketio.on("create_tutorial")
    def handle_create_tutorial(data):
        staff_id = session.get("staff_id")
        
        if not staff_id:
            socketio.emit("error", {"message": "Not authenticated"})
            return
        
        if not isinstance(data, dict):
            socketio.emit("error", {"message": "Invalid data"})
            return
        
        tutorial_code = generate_unique_code()
        tutorial_name = data.get("name", "")
        group_size = data.get("group_size")
        available_attributes = data.get("available_attributes")

        try:
            discussion_time = math.ceil(float(data.get("time")) * 60)
        except Exception:
            discussion_time = 5 * 60

        if not isinstance(group_size, int) or group_size < 2:
            # TODO Update all Errors
            # socketio.emit("error", ERR_INVALID_GROUP_SIZE, to=request.sid, namespace="/staff")
            socketio.emit("error", {"message": "Invalid group size"})
            return
        
        if not isinstance(available_attributes, list):
            socketio.emit("error", {"message": "Invalid attributes available"})
            return

        # Create in-memory tutorial structure
        tutorials[tutorial_code] = {
            "staff_id": staff_id,
            "staff_uuid": None,  # Will be set when staff connects via socket
            "name": tutorial_name,
            "state": TutorialState.LOBBY,
            "group_size": group_size,
            "available_attributes": available_attributes,
            "students": {},
            "groups": {},
            # "previous_matches": {}, # TODO verify if necessary
            "questions": [],
            "timer": {
                "duration": 0,
                "remaining": 0,
                "running": False,
                "phase": None
            },
            "intro_duration": 30,
            "discussion_duration": discussion_time,
            "created_at": int(time.time()),
            "last_activity": int(time.time())
        }
        
        # Join room for this tutorial
        socketio.enter_room(f"tutorial_{tutorial_code}")
        socketio.enter_room(f"staff_{tutorial_code}")
        
        # Emit created event to staff
        socketio.emit("tutorial_created", {"code": tutorial_code})
    

    @socketio.on("start_round")
    def handle_start_round():
        staff_id = session.get("staff_id")
        
        if not staff_id:
            socketio.emit("error", {"message": "Not authenticated"})
            return
        
        # Find tutorial
        tutorial_code = None
        for code, tutorial in tutorials.items():
            if tutorial["staff_id"] == staff_id:
                tutorial_code = code
                break
        
        if not tutorial_code or tutorials[tutorial_code]["ended"]:
            socketio.emit("error", {"message": "Tutorial ended"})
            return
        
        # Run matching algorithm
        from .matching import form_groups
        groups = form_groups(tutorial_code, tutorials[tutorial_code]["group_size"])
        
        if "error" in groups:
            socketio.emit("error", {"message": groups["error"]})
            return
        
        for group_id, members in groups.items():
            for member_uuid in members:
                if member_uuid not in tutorials[tutorial_code]["previous_matches"]:
                    tutorials[tutorial_code]["previous_matches"][member_uuid] = set()
                # Add all other members of this group to previous matches
                for other_member_uuid in members:
                    if other_member_uuid != member_uuid:
                        tutorials[tutorial_code]["previous_matches"][member_uuid].add(other_member_uuid)
        
        # Clear discussion questions
        tutorials[tutorial_code]["questions"].clear()

        # Emit groups formed event
        socketio.emit("groups_formed", {"groups": groups}, room=f"tutorial_{tutorial_code}")
    

    @socketio.on("start_discussion")
    def handle_start_discussion():
        """Handle staff starting discussion phase"""
        staff_id = session.get("staff_id")
        
        if not staff_id:
            socketio.emit("error", {"message": "Not authenticated"})
            return
        
        # Find tutorial
        tutorial_code = None
        for code, tutorial in tutorials.items():
            if tutorial["staff_id"] == staff_id:
                tutorial_code = code
                break
        
        if not tutorial_code:
            socketio.emit("error", {"message": "Tutorial not found"})
            return
        
        if tutorials[tutorial_code]["state"] == TutorialState.ENDED:
            socketio.emit("error", {"message": "Tutorial ended"})
            return
        
        # Set state to discussion
        tutorials[tutorial_code]["state"] = TutorialState.DISCUSSION
        
        # Start intro timer (auto)
        from .timer import TutorialTimer
        timer = TutorialTimer(tutorial_code, socketio)
        timer.start_intro()
        
        academic = DiscussionQuestion.query.filter_by(category_name="academic").order_by(func.random()).first()
        casual = DiscussionQuestion.query.filter_by(category_name="casual").order_by(func.random()).first()
        study = DiscussionQuestion.query.filter_by(category_name="study").order_by(func.random()).first()

        questions = [academic.question, casual.question, study.question]
        tutorials[tutorial_code]["questions"] = questions

        # Emit discussion started event
        socketio.emit("discussion_started", {
            "intro_duration": tutorials[tutorial_code]["intro_duration"],
            "discussion_duration": tutorials[tutorial_code]["discussion_duration"],
            "questions": tutorials[tutorial_code]["questions"]
        }, room=f"tutorial_{tutorial_code}")
    

    @socketio.on("back_to_lobby")
    def handle_back_to_lobby():
        staff_id = session.get("staff_id")
        
        if not staff_id:
            socketio.emit("error", {"message": "Not authenticated"})
            return
        
        # Find tutorial
        tutorial_code = None
        for code, tutorial in tutorials.items():
            if tutorial["staff_id"] == staff_id:
                tutorial_code = code
                break
        
        if not tutorial_code:
            socketio.emit("error", {"message": "Tutorial not found"})
            return
        
        if tutorials[tutorial_code]["state"] == TutorialState.ENDED:
            socketio.emit("error", {"message": "Tutorial ended"})
            return
        
        # Set state to lobby
        tutorials[tutorial_code]["state"] = TutorialState.LOBBY
        
        # Emit updated state
        socketio.emit("tutorial_state", {
            "state": tutorials[tutorial_code]["state"],
            "students": list(tutorials[tutorial_code]["students"].values()),
            "groups": tutorials[tutorial_code]["groups"],
            "timer": tutorials[tutorial_code]["timer"],
            "round": tutorials[tutorial_code]["round"]
        }, room=f"tutorial_{tutorial_code}")
    

    @socketio.on("end_tutorial")
    def handle_end_tutorial():
        staff_id = session.get("staff_id")
        
        if not staff_id:
            socketio.emit("error", {"message": "Not authenticated"})
            return
        
        # Find tutorial
        tutorial_code = None
        for code, tutorial in tutorials.items():
            if tutorial["staff_id"] == staff_id:
                tutorial_code = code
                break
        
        if not tutorial_code:
            socketio.emit("error", {"message": "Tutorial not found"})
            return
        
        if tutorials[tutorial_code]["state"] == TutorialState.ENDED:
            socketio.emit("error", {"message": "Tutorial ended"})
            return
        
        # Set state to ended
        tutorials[tutorial_code]["state"] = TutorialState.ENDED
        
        # Clear all student data
        tutorials[tutorial_code]["students"].clear()
        
        # Emit tutorial ended event
        socketio.emit("tutorial_ended", {}, room=f"tutorial_{tutorial_code}")
        
        # Remove from memory after a delay (or immediately)
        # For now, we'll remove it right away
        del tutorials[tutorial_code]


def generate_unique_code(length = 6):
    code = generate_tutorial_code()
    while code in tutorials:
        code = generate_tutorial_code()
    return code