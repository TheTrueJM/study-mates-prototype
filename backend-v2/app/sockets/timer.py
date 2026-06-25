import time
import threading

from sockets import tutorials
from ..enums import TutorialState

class TutorialTimer:
    def __init__(self, tutorial_code, socketio):
        self.tutorial_code = tutorial_code
        self.socketio = socketio
        self.thread = None
        self.running = False
    
    def start_intro(self, duration=30):
        self.running = True
        self.remaining = duration
        self.phase = "intro"
        tutorials[self.tutorial_code]["timer"] = {
            "duration": duration,
            "remaining": duration,
            "running": True,
            "phase": "intro"
        }
        tutorials[self.tutorial_code]["timer"]["discussion_remaining"] = tutorials[self.tutorial_code]["discussion_duration"]
        
        self.thread = threading.Thread(target=self._tick, daemon=True)
        self.thread.start()
    
    def start_discussion(self, duration):
        self.running = True
        self.remaining = duration
        self.phase = "discussion"
        tutorials[self.tutorial_code]["timer"] = {
            "duration": duration,
            "remaining": duration,
            "running": True,
            "phase": "discussion"
        }
        
        self.thread = threading.Thread(target=self._tick, daemon=True)
        self.thread.start()
    
    def _tick(self):
        while self.running:
            time.sleep(1)
            if not self.running:
                break
            
            self.remaining -= 1
            tutorials[self.tutorial_code]["timer"]["remaining"] = self.remaining
            
            self.socketio.emit(
                "timer_update",
                {"remaining": self.remaining, "phase": self.phase},
                room=f"tutorial_{self.tutorial_code}"
            )
            
            if self.remaining <= 0:
                self.running = False
                tutorials[self.tutorial_code]["timer"]["running"] = False
                
                if self.phase == "intro":
                    # Auto-switch to discussion
                    tutorials[self.tutorial_code]["timer"]["phase"] = "discussion"
                    tutorials[self.tutorial_code]["timer"]["remaining"] = tutorials[self.tutorial_code]["discussion_duration"]
                    tutorials[self.tutorial_code]["timer"]["running"] = True
                    self.remaining = tutorials[self.tutorial_code]["discussion_duration"]
                    self.phase = "discussion"
                    
                    self.socketio.emit(
                        "timer_expired",
                        {"phase": "intro"},
                        room=f"tutorial_{self.tutorial_code}"
                    )
                    
                    # Start discussion timer
                    self.start_discussion(tutorials[self.tutorial_code]["discussion_duration"])
                    
                else:
                    # Discussion ended
                    self.socketio.emit(
                        "timer_expired",
                        {"phase": "discussion"},
                        room=f"tutorial_{self.tutorial_code}"
                    )
                    tutorials[self.tutorial_code]["state"] = TutorialState.AWAITING
    
    def stop(self):
        self.running = False