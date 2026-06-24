# In backend-v2/app/sockets/student.py

import uuid
from flask import session
from app.sockets import tutorials
from app.sockets.utils import generate_student_uuid, generate_student_name
from app.enums import TutorialState

def register_student_events(socketio):
    @socketio.on("authenticate_student")
    def handle_authenticate_student(data):
        """Handle student authentication via Socket.IO"""
        tutorial_code = data.get("tutorial_code")
        
        if not tutorial_code:
            socketio.emit("authentication_failed", {"reason": "No tutorial code provided"})
            return
        
        # Check if tutorial exists and is active
        if tutorial_code not in tutorials or tutorials[tutorial_code]["ended"]:
            socketio.emit("authentication_failed", {"reason": "Tutorial not found or has ended"})
            return
        
        # Generate UUID and name
        student_uuid = generate_student_uuid()
        student_name = generate_student_name()
        
        # Create student record
        tutorial = tutorials[tutorial_code]
        tutorial["students"][student_uuid] = {
            "name": student_name,
            "currentGPA": None,
            "goalGPA": None,
            "availability": {},
            "shared_attributes": [],
            "group": None,
            "joined_at": int(time.time()),
            "last_updated": int(time.time()),
            "details_complete": False
        }
        
        # Store in session (first-party signed cookie)
        session["student_uuid"] = student_uuid
        
        # Join room
        socketio.enter_room(f"tutorial_{tutorial_code}")
        
        # Emit authenticated event
        socketio.emit("authenticated", {
            "uuid": student_uuid,
            "name": student_name,
            "tutorial_code": tutorial_code
        })
    
    @socketio.on("reauthenticate_student")
    def handle_reauthenticate_student(data):
        """Handle student reauthentication"""
        session_id = data.get("session_id")
        
        # Look up UUID from session (first-party signed cookie)
        student_uuid = session.get("student_uuid")
        
        if not student_uuid:
            socketio.emit("reauthentication_failed", {"reason": "No session found"})
            return
        
        # Find tutorial
        tutorial_code = None
        for code, tutorial in tutorials.items():
            if student_uuid in tutorial["students"]:
                tutorial_code = code
                break
        
        if not tutorial_code or tutorials[tutorial_code]["ended"]:
            socketio.emit("reauthentication_failed", {"reason": "Session expired or tutorial ended"})
            return
        
        # Restore to same room
        socketio.enter_room(f"tutorial_{tutorial_code}")
        
        # Emit reauthenticated event
        student_record = tutorials[tutorial_code]["students"][student_uuid]
        socketio.emit("reauthenticated", {
            "uuid": student_uuid,
            "name": student_record["name"],
            "tutorial_code": tutorial_code
        })
    
    @socketio.on("join_tutorial")
    def handle_join_tutorial(data):
        """Handle student joining a tutorial"""
        code = data.get("code")
        
        if not code:
            socketio.emit("join_failed", {"reason": "No tutorial code provided"})
            return
        
        # Check if tutorial exists and is active
        if code not in tutorials or tutorials[code]["ended"]:
            socketio.emit("join_failed", {"reason": "Tutorial not found or has ended"})
            return
        
        # Emit current state to student
        tutorial = tutorials[code]
        socketio.emit("tutorial_state", {
            "state": tutorial["state"],
            "students": list(tutorial["students"].values()),
            "groups": tutorial["groups"],
            "timer": tutorial["timer"],
            "round": tutorial["round"]
        })
    
    @socketio.on("update_details")
    def handle_update_details(data):
        """Handle student updating their details"""
        student_uuid = session.get("student_uuid")
        
        if not student_uuid:
            socketio.emit("error", {"message": "Not authenticated"})
            return
        
        # Find tutorial
        tutorial_code = None
        for code, tutorial in tutorials.items():
            if student_uuid in tutorial["students"]:
                tutorial_code = code
                break
        
        if not tutorial_code or tutorials[tutorial_code]["ended"]:
            socketio.emit("error", {"message": "Tutorial ended"})
            return
        
        # Update student record
        tutorial = tutorials[tutorial_code]
        student_record = tutorial["students"][student_uuid]
        
        # Update attributes
        if "currentGPA" in data:
            student_record["currentGPA"] = data["currentGPA"]
        if "goalGPA" in data:
            student_record["goalGPA"] = data["goalGPA"]
        if "availability" in data:
            student_record["availability"] = data["availability"]
        if "sharedAttributes" in data:
            student_record["shared_attributes"] = data["sharedAttributes"]
        
        # Mark as complete if all required fields are filled
        details_complete = True
        available_attrs = tutorial["available_attributes"]
        
        if "currentGPA" in available_attrs and not student_record["currentGPA"]:
            details_complete = False
        if "goalGPA" in available_attrs and not student_record["goalGPA"]:
            details_complete = False
        
        student_record["details_complete"] = details_complete
        student_record["last_updated"] = int(time.time())
        
        # Broadcast updated students list to all clients
        socketio.emit("students_updated", {
            "students": list(tutorial["students"].values())
        }, room=f"tutorial_{tutorial_code}")
    
    @socketio.on("enter_tutorial")
    def handle_enter_tutorial():
        """Handle student entering tutorial lobby"""
        student_uuid = session.get("student_uuid")
        
        if not student_uuid:
            socketio.emit("error", {"message": "Not authenticated"})
            return
        
        # Find tutorial
        tutorial_code = None
        for code, tutorial in tutorials.items():
            if student_uuid in tutorial["students"]:
                tutorial_code = code
                break
        
        if not tutorial_code or tutorials[tutorial_code]["ended"]:
            socketio.emit("error", {"message": "Tutorial ended"})
            return
        
        # Update last activity
        tutorials[tutorial_code]["last_activity"] = int(time.time())
        
        # Emit current state to student
        tutorial = tutorials[tutorial_code]
        socketio.emit("tutorial_state", {
            "state": tutorial["state"],
            "students": list(tutorial["students"].values()),
            "groups": tutorial["groups"],
            "timer": tutorial["timer"],
            "round": tutorial["round"]
        })
    
    @socketio.on("rejoin_tutorial")
    def handle_rejoin_tutorial():
        """Handle student rejoining after tutorial ended"""
        # This is a placeholder - actual implementation would be handled by
        # the authenticate_student event which will start from scratch
        pass