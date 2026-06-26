from enum import Enum


class TutorialState(Enum):
    LOBBY = "lobby"
    GROUPING = "grouping"
    INTRODUCTION = "introduction"
    DISCUSSION = "discussion"
    ENDED = "ended"


class GradeType(Enum):
    P = 4
    C = 5
    D = 6
    HD = 7

class Day(Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"

class TimePeriod(Enum):
    M = "M"
    A = "A"
    E = "E"

class CommunicationMethod(Enum): # TODO Refine this Option List
    EMAIL = "email"
    TEAMS = "teams"
    SLACK = "slack"
    DISCORD = "discord"
    INSTAGRAM = "instagram"
    SNAPCHAT = "snapchat"
    MESSENGER = "messenger"
    SIGNAL = "signal"
    TELEGRAM = "telegram"
    LINKEDIN = "linkedin"
    OTHERS = "others"

class MeetingMode(Enum):
    PHYSICAL = "physical"
    VIRTUAL = "virtual"
    EITHER = "either"


class AttributeType(Enum):
    CURRENT_GPA = "currentGPA"
    GOAL_GRADE = "goalGrade"
    AVAILABILITY = "availability"
    COMMUNICATION = "communication"
    MEETING_MODE = "meetingMode"
    YEAR = "year"
    SEMESTER = "semester"
    ACCESSIBILITY = "accessibility"


VALID_GRADES = {grade.value for grade in GradeType}
VALID_AVAILABILITY_CODES = {day.value + time.value for day in Day for time in TimePeriod}
VALID_COMMUNICATION_METHOD = {method.value for method in CommunicationMethod}
VALID_MEETING_MODE = {mode.value for mode in MeetingMode}

VALID_ATTRIBUTES = {attribute.value for attribute in AttributeType}


def get_availability_code(day: Day, period: TimePeriod) -> str:
    return f"{day.value}{period.value}"

def parse_availability(availability_raw) -> list[str]:
    if isinstance(availability_raw, list):
        codes = {code.strip().upper() for code in availability_raw if isinstance(code, str) and code.strip()}
    elif isinstance(availability_raw, str) and availability_raw.strip():
        codes = {code.strip().upper() for code in availability_raw.split(",") if code.strip()}
    else:
        return list()

    return list(codes & VALID_AVAILABILITY_CODES)
