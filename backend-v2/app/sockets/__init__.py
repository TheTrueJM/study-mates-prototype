from .staff import register_staff_events
from .student import register_student_events

__all__ = ["register_staff_events", "register_student_events"]


import time

from ..enums import TutorialState

# Global in-memory store for tutorials and users
tutorials = {}
users = {}

def cleanup_expired_tutorials():
    current_time = time.time()
    expired = []
    
    for code, tutorial in tutorials.items():
        if tutorial["state"] == TutorialState.ENDED:
            expired.append(code)
            continue
        
        # Auto-expire if idle for 60 minutes
        if current_time - tutorial["last_activity"] > 3600:
            tutorial["state"] = TutorialState.ENDED
            expired.append(code)
    
    for code in expired:
        del tutorials[code]