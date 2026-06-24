# In backend-v2/app/sockets/staff.py

import jwt
from flask import session, request
from app.sockets import tutorials
from app.enums import TutorialState

def register_staff_events(socketio):
    @socketio.on("connect")
    def handle_staff_connect():
        """Handle staff socket connection"""
        # Check if JWT is provided in auth parameter
        auth = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
        
        if not auth:
            # No token, disconnect
            socketio.disconnect()
            return
        
        try:
            # Verify JWT
            payload = jwt.decode(auth, app.config["JWT_SECRET_KEY"], algorithms=[app.config["JWT_ALGORITHM"]])
            
            # Store staff ID in session
            session["staff_id"] = payload["user_id"]
            
            # Join global room for staff
            socketio.enter_room("staff_global")
            
        except jwt.ExpiredSignatureError:
            # Expired token, disconnect
            socketio.disconnect()
            return
        except jwt.InvalidTokenError:
            # Invalid token, disconnect
            socketio.disconnect()
            return
    
    @socketio.on("create_tutorial")
    def handle_create_tutorial(data):
        """Handle staff creating a new tutorial"""
        staff_id = session.get("staff_id")
        
        if not staff_id:
            socketio.emit("error", {"message": "Not authenticated"})
            return
        
        # Generate unique tutorial code (6 random uppercase chars)
        import random
        import string
        tutorial_code = ''.join(random.choices(string.ascii_uppercase, k=6))
        
        # Create tutorial structure
        tutorial = {
            "staff_id": staff_id,
            "staff_uuid": None,  # Will be set when staff connects via socket
            "name": data.get("name", ""),
            "state": "lobby",
            "group_size": data.get("group_size", 4),
            "available_attributes": data.get("available_attributes", ["currentGPA", "goalGPA", "availability"]),
            "students": {},
            "groups": {},
            "questions": {
                "academic": [
                    "What are your career goals after graduation?",
                    "What study techniques work best for you?"
                ],
                "casual": [
                    "What is your favourite video game?",
                    "How do you like to unwind after a long day?"
                ],
                "smart": [
                    "What unit did you enjoy the most?",
                    "When did you realise you wanted to study your course?"
                ]
            },
            "timer": {
                "duration": 0,
                "remaining": 0,
                "running": False,
                "phase": None
            },
            "intro_duration": 30,
            "discussion_duration": data.get("discussion_duration", 600),
            "round": 0,
            "created_at": int(time.time()),
            "last_activity": int(time.time()),
            "ended": False
        }
        
        # Store tutorial in memory
        tutorials[tutorial_code] = tutorial
        
        # Join room for this tutorial
        socketio.enter_room(f"tutorial_{tutorial_code}")
        socketio.enter_room(f"staff_{tutorial_code}")
        
        # Emit created event to staff
        socketio.emit("tutorial_created", {
            "code": tutorial_code,
            "name": tutorial["name"]
        })
    
    @socketio.on("start_round")
    def handle_start_round():
        """Handle staff starting a new group formation round"""
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
        from app.sockets.matching import form_groups
        groups = form_groups(tutorial_code, tutorials[tutorial_code]["group_size"])
        
        if "error" in groups:
            socketio.emit("error", {"message": groups["error"]})
            return
        
        # Emit groups formed event
        socketio.emit("groups_formed", {
            "groups": groups,
            "round": tutorials[tutorial_code]["round"]
        }, room=f"tutorial_{tutorial_code}")
    
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
        
        if not tutorial_code or tutorials[tutorial_code]["ended"]:
            socketio.emit("error", {"message": "Tutorial ended"})
            return
        
        # Set state to discussion
        tutorials[tutorial_code]["state"] = "discussion"
        
        # Start intro timer (auto)
        from app.sockets.timer import TutorialTimer
        timer = TutorialTimer(tutorial_code, socketio)
        timer.start_intro()
        
        # Emit discussion started event
        socketio.emit("discussion_started", {
            "intro_duration": tutorials[tutorial_code]["intro_duration"],
            "discussion_duration": tutorials[tutorial_code]["discussion_duration"],
            "questions": tutorials[tutorial_code]["questions"]
        }, room=f"tutorial_{tutorial_code}")
    
    @socketio.on("next_round")
    def handle_next_round():
        """Handle staff starting next round"""
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
        
        # Run matching algorithm (with previous matches)
        from app.sockets.matching import form_groups
        groups = form_groups(tutorial_code, tutorials[tutorial_code]["group_size"], 
                            tutorials[tutorial_code].get("previous_matches", {}))
        
        if "error" in groups:
            socketio.emit("error", {"message": groups["error"]})
            return
        
        # Store previous matches for next round
        tutorials[tutorial_code]["previous_matches"] = {}
        for group_id, members in groups.items():
            for member_uuid in members:
                if member_uuid not in tutorials[tutorial_code]["previous_matches"]:
                    tutorials[tutorial_code]["previous_matches"][member_uuid] = set()
                # Add all other members of this group to previous matches
                for other_member_uuid in members:
                    if other_member_uuid != member_uuid:
                        tutorials[tutorial_code]["previous_matches"][member_uuid].add(other_member_uuid)
        
        # Emit groups formed event
        socketio.emit("groups_formed", {
            "groups": groups,
            "round": tutorials[tutorial_code]["round"]
        }, room=f"tutorial_{tutorial_code}")
    
    @socketio.on("back_to_lobby")
    def handle_back_to_lobby():
        """Handle staff returning to lobby"""
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
        
        # Set state to lobby
        tutorials[tutorial_code]["state"] = "lobby"
        
        # Emit updated state
        socketio.emit("tutorial_state", {
            "state": tutorial["state"],
            "students": list(tutorial["students"].values()),
            "groups": tutorial["groups"],
            "timer": tutorial["timer"],
            "round": tutorial["round"]
        }, room=f"tutorial_{tutorial_code}")
    
    @socketio.on("end_tutorial")
    def handle_end_tutorial():
        """Handle staff ending tutorial"""
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
        
        # Set state to ended
        tutorials[tutorial_code]["ended"] = True
        
        # Clear all student data
        tutorials[tutorial_code]["students"] = {}
        
        # Emit tutorial ended event
        socketio.emit("tutorial_ended", {}, room=f"tutorial_{tutorial_code}")
        
        # Remove from memory after a delay (or immediately)
        # For now, we'll remove it right away
        del tutorials[tutorial_code]