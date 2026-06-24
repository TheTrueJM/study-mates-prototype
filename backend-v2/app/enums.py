from enum import Enum

class TutorialState(Enum):
    LOBBY = "lobby"
    GROUPS = "groups"
    DISCUSSION = "discussion"
    ENDED = "ended"

class AttributeType(Enum):
    CURRENT_GPA = "currentGPA"
    GOAL_GPA = "goalGPA"
    AVAILABILITY = "availability"