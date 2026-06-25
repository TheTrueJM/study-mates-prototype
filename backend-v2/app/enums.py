from enum import Enum


class TutorialState(Enum):
    LOBBY = "lobby"
    GROUPS = "groups"
    DISCUSSION = "discussion"
    AWAITING = "awaiting"
    ENDED = "ended"


class AttributeType(Enum):
    CURRENT_GPA = "currentGPA"
    GOAL_Grade = "goalGrade"
    AVAILABILITY = "availability"