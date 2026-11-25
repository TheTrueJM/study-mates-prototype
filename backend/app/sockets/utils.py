from flask_socketio import emit, leave_room
import random, string, uuid, time

from ..enums import TutorialState, AttributeType, SHAREABLE_ATTRIBUTES, PUBLIC_ATTRIBUTES


# Students are identified by a Random UUID, and Staff by their Access Token
users = dict() # { ID: {sessions: {sID, ...}, role: student|staff, tutorial: code|None, [staff_type, username]}, ... }
sessions = dict() # { sID: UUID }
tutorials = dict()
# {
#   code: {
#       staff: UUID,
#       name: str,
#       state: TutorialState,
#       group_size: int,
#       max_groups: int | None,
#       available_attributes: [ ... ],
#       students: {
#           UUID: {
#               name: str,
#               attributes: { ... },
#               shared_attributes: [ ... ],
#               attributes_complete: bool,
#               group: int
#           },
#           ...
#       },
#       groups: { number: [ UUID, ... ], ... },
#       previous_matches: { UUID: ? },
#       questions: [question, ...],
#       timer: { duration: int, remaining: int, running: bool }
#   },
#   ...
# }


DAYS = {
    "MON": "Monday",
    "TUE": "Tuesday",
    "WED": "Wednesday",
    "THU": "Thursday",
    "FRI": "Friday",
    "SAT": "Saturday",
    "SUN": "Sunday",
}
TIMES = {
    "M": "Morning",
    "A": "Afternoon",
    "E": "Evening"
}

DESCRIPTORS = (
    'agile', 'anonymous', 'blazing', 'blissful', 'bold', 'brave', 'bright', 'calm', 'cheerful',
    'clever', 'colorful', 'cosmic',  'curious', 'daring', 'dazzling', 'energetic', 'epic',
    'friendly', 'frosty', 'gentle', 'glowing', 'golden', 'graceful', 'happy', 'hasty', 'heroic',
    'hidden', 'jolly', 'joyful', 'kind', 'legendary', 'lively', 'lunar', 'midnight', 'mighty',
    'mysterious', 'mythic', 'nimble', 'noble', 'peaceful', 'playful', 'powerful', 'quick',
    'radiant', 'rapid', 'resilient', 'royal', 'shiny', 'silent', 'silver', 'smart', 'sneaky',
    'stealthy', 'stellar', 'strong', 'swift', 'valiant', 'vibrant', 'wild', 'wise', 'witty'
)
ANIMALS = (
    'armadillo', 'badger', 'bear', 'beaver', 'cat', 'chameleon', 'cheetah', 'chicken', 'cockatoo',
    'coyote', 'jackal', 'crow', 'dog', 'dolphin', 'duck', 'eagle', 'falcon', 'fish', 'flamingo',
    'fox', 'hawk', 'hedgehog', 'horse', 'jaguar', 'jellyfish', 'kangaroo', 'koala', 'leopard',
    'lion', 'lizard', 'meerkat', 'otter', 'owl', 'panda', 'panther', 'parrot', 'penguin', 'rabbit',
    'raccoon', 'raven', 'salamander', 'seal', 'serpent', 'shark', 'sheep', 'sloth', 'snake',
    'squirrel', 'swan', 'tiger', 'tortoise', 'turtle', 'wallaby', 'walrus', 'wolf', 'wombat', 'zebra'
)


day_index = {k: i for i, k in enumerate(DAYS.keys())}
time_index = {k: i for i, k in enumerate(TIMES.keys())}

sort_availability = lambda codes: sorted(
    codes, key=lambda code: (day_index.get(code[:3], 99), time_index.get(code[3:], 99))
)


def emit_tutorial_update(code):
    tutorial = tutorials.get(code)
    if not tutorial:
        for ns in ["/", "/staff"]:
            emit("error", {"message": "This tutorial session could not be found."}, room=code, namespace=ns)
        return

    students = tutorial.get("students", {})
    groups = tutorial.get("groups", {})

    tutorial_name = tutorial.get("name")
    state = str(tutorial.get("state"))
    available_attributes = tutorial.get("available_attributes", [])
    questions = tutorial.get("questions", [])
    timer = tutorial.get("timer", {})

    staff_payload = {
        "tutorial_code": code,
        "tutorial_name": tutorial_name,
        "state": state,
        "group_size": tutorial.get("group_size"),
        "max_groups": tutorial.get("max_groups"),
        "available_attributes": available_attributes,
        "students": {
            student_id: {"name": student.get("name"), "attributes_complete": student.get("attributes_complete")}
            for student_id, student in students.items()
        },
        "groups": groups,
        "questions": questions,
        "timer": timer,
    }
    emit("tutorial_update", staff_payload, room=code, namespace="/staff")

    # Public Details of each Grouped Student, as seen by Other Students
    formatted_groups = dict()
    for group_number, member_ids in groups.items():
        formatted_groups[group_number] = [
            {
                "name": students[member_id].get("name"),
                "attributes": get_public_attributes(students[member_id], available_attributes),
            }
            for member_id in member_ids if member_id in students
        ]

    for student_id, student_data in students.items():
        group_number = student_data.get("group")

        payload = {
            "username": student_data.get("name"),
            "attributes": student_data.get("attributes", {}),
            "shared_attributes": student_data.get("shared_attributes", []),
            "attributes_complete": student_data.get("attributes_complete"),
            "tutorial_code": code,
            "tutorial_name": tutorial_name,
            "state": state,
            "available_attributes": available_attributes,
            "student_count": len(students),
            "group_number": group_number,
            "group_members": formatted_groups.get(group_number),
            "questions": questions,
            "timer": timer,
        }
        emit("student_update", payload, room=student_id, namespace="/")


def remove_student(user_id, code):
    """Removes a student (and their connections) from a tutorial, including any groups"""
    tutorial = tutorials.get(code)
    if not tutorial or user_id not in tutorial.get("students", {}):
        return False

    del tutorial["students"][user_id]

    for group_number in list(tutorial.get("groups", {}).keys()):
        members = tutorial["groups"][group_number]
        if user_id in members:
            members.remove(user_id)
        if not members:
            del tutorial["groups"][group_number]

    previous_matches = tutorial.get("previous_matches", {})
    previous_matches.pop(user_id, None)
    for matches in previous_matches.values():
        matches.discard(user_id)

    if user := users.get(user_id):
        if user.get("tutorial") == code:
            user["tutorial"] = None
        for sid in user.get("sessions", set()):
            leave_room(code, sid=sid, namespace="/")

    return True


def cleanup_expired_tutorials(): # TODO Run this Periodically in Application
    current_time = time.time()

    # TODO Emit Closure to Users
    for code, tutorial in list(tutorials.items()):
        if tutorial["state"] == TutorialState.ENDED:
            del tutorials[code]
            continue

        # Auto-expire if idle for 60 minutes
        if current_time - tutorial.get("last_activity", 0) > 3600:
            tutorial["state"] = TutorialState.ENDED
            del tutorials[code]


def get_public_attributes(student, available_attributes):
    """Details of a student that other students may see: provided details that are enabled and shared"""
    public_attributes = {}
    all_attributes = student.get("attributes") or {}
    shared_attributes = set(student.get("shared_attributes", []))

    for attribute in available_attributes:
        value = all_attributes.get(attribute)
        if value is None or value == []:
            continue

        if attribute in PUBLIC_ATTRIBUTES or (attribute in SHAREABLE_ATTRIBUTES and attribute in shared_attributes):
            if attribute == str(AttributeType.AVAILABILITY):
                value = sort_availability(value)
            public_attributes[attribute] = value

    return public_attributes


def _generate_tutorial_code(length = 6):
    return ''.join(random.choices(string.ascii_uppercase, k=length))

def generate_unique_tutorial_code(length = 6):
    tutorial_code = _generate_tutorial_code(length)
    while tutorial_code in tutorials:
        tutorial_code = _generate_tutorial_code(length)
    return tutorial_code

def _generate_user_uuid():
    return str(uuid.uuid4())

def generate_unique_user_uuid():
    user_uuid = _generate_user_uuid()
    while user_uuid in users:
        user_uuid = _generate_user_uuid()
    return user_uuid

def _generate_student_name():
    return f"{random.choice(DESCRIPTORS).capitalize()}-{random.choice(ANIMALS).capitalize()}"

def generate_unique_student_name(tutorial_code):
    student_names = {student.get("name") for student in tutorials[tutorial_code].get("students", {}).values()}
    student_name = _generate_student_name()
    while student_name in student_names:
        student_name = _generate_student_name()
    return student_name