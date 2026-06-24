# In backend-v2/app/sockets/__init__.py
from .staff import register_staff_events
from .student import register_student_events

__all__ = ["register_staff_events", "register_student_events"]

import time
from app.enums import TutorialState

# Global in-memory store for tutorials
tutorials = {}

def cleanup_expired_tutorials():
    """Run periodically to clean up idle tutorials"""
    current_time = time.time()
    expired = []
    
    for code, tutorial in tutorials.items():
        if tutorial["ended"]:
            expired.append(code)
            continue
        
        # Auto-expire if idle for 60 minutes
        if current_time - tutorial["last_activity"] > 3600:
            tutorial["ended"] = True
            expired.append(code)
    
    for code in expired:
        del tutorials[code]