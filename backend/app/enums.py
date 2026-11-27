from enum import Enum


class TutorialState(Enum):
    LOBBY = "lobby"
    GROUPING = "grouping"
    INTRODUCTION = "introduction"
    DISCUSSION = "discussion"
    WRAP_UP = "wrap_up"
    ENDED = "ended"

    def __str__(self):
        return self.value


class GradeType(Enum):
    P = 4
    C = 5
    D = 6
    HD = 7

    def __int__(self):
        return self.value

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

class CommunicationMethod(Enum):
    EMAIL = "email"
    TEAMS = "teams"
    SLACK = "slack"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    MESSENGER = "messenger"
    INSTAGRAM = "instagram"
    SNAPCHAT = "snapchat"
    SIGNAL = "signal"
    TELEGRAM = "telegram"
    LINKEDIN = "linkedin"
    SMS = "sms"
    OTHERS = "others"

class MeetingMode(Enum):
    PHYSICAL = "physical"
    VIRTUAL = "virtual"
    EITHER = "either"

    def __str__(self):
        return self.value


class AttributeType(Enum):
    CURRENT_GPA = "current_gpa"
    GOAL_GRADE = "goal_grade"
    AVAILABILITY = "availability"
    COMMUNICATION = "communication"
    MEETING_MODE = "meeting_mode"
    YEAR = "year"
    SEMESTER = "semester"
    ACCESSIBILITY = "accessibility"

    def __str__(self):
        return self.value


VALID_GRADES = {grade.value for grade in GradeType}
VALID_AVAILABILITY_CODES = {day.value + time.value for day in Day for time in TimePeriod}
VALID_COMMUNICATION_METHODS = {method.value for method in CommunicationMethod}
VALID_MEETING_MODE = {mode.value for mode in MeetingMode}

VALID_ATTRIBUTES = {attribute.value for attribute in AttributeType}

MIN_STUDY_YEAR, MAX_STUDY_YEAR = 1, 10
MIN_STUDY_SEMESTER, MAX_STUDY_SEMESTER = 1, 2

# Attributes a Staff Member can enable for a Tutorial, in display order
# NOTE Accessibility is not yet implemented into the Student Form or Matching
SELECTABLE_ATTRIBUTES = [
    str(AttributeType.GOAL_GRADE),
    str(AttributeType.CURRENT_GPA),
    str(AttributeType.AVAILABILITY),
    str(AttributeType.MEETING_MODE),
    str(AttributeType.COMMUNICATION),
    str(AttributeType.YEAR),
    str(AttributeType.SEMESTER),
]

# Attributes used by the Matching Algorithm, which Students may choose to hide from Other Students
SHAREABLE_ATTRIBUTES = {
    str(AttributeType.CURRENT_GPA),
    str(AttributeType.GOAL_GRADE),
    str(AttributeType.AVAILABILITY),
    str(AttributeType.COMMUNICATION),
    str(AttributeType.MEETING_MODE),
}

# Display-Only Attributes (not used for Matching), always visible to other students when provided
PUBLIC_ATTRIBUTES = {
    str(AttributeType.YEAR),
    str(AttributeType.SEMESTER),
}

# Attributes enabled for a Tutorial when the Staff Member does not specify any
DEFAULT_AVAILABLE_ATTRIBUTES = [
    str(AttributeType.GOAL_GRADE),
    str(AttributeType.CURRENT_GPA),
    str(AttributeType.AVAILABILITY),
    str(AttributeType.MEETING_MODE),
    str(AttributeType.COMMUNICATION),
]

# Attributes a new Student shares with their group by default
DEFAULT_SHARED_ATTRIBUTES = [
    str(AttributeType.GOAL_GRADE),
    str(AttributeType.AVAILABILITY),
    str(AttributeType.MEETING_MODE),
    str(AttributeType.COMMUNICATION),
]


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

def parse_communication(communication_raw) -> list[str]:
    if isinstance(communication_raw, list):
        methods = {method.strip().lower() for method in communication_raw if isinstance(method, str) and method.strip()}
    elif isinstance(communication_raw, str) and communication_raw.strip():
        methods = {method.strip().lower() for method in communication_raw.split(",") if method.strip()}
    else:
        return list()

    order = [method.value for method in CommunicationMethod]
    return sorted(methods & VALID_COMMUNICATION_METHODS, key=order.index)

def parse_available_attributes(attributes_raw) -> list[str] | None:
    """Filters a list of attribute names to those selectable, in display order (None if not a list)"""
    if not isinstance(attributes_raw, list):
        return None

    requested = {attribute for attribute in attributes_raw if isinstance(attribute, str)}
    return [attribute for attribute in SELECTABLE_ATTRIBUTES if attribute in requested]
