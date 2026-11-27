from flask_socketio import emit, leave_room, close_room
import random, string, uuid, time

from .timer import timer
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
#       locked: bool,
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
#       round: int,
#       round_discussed: bool,
#       formation: int,
#       questions: [question, ...],
#       discussion_time: int (seconds),
#       timer: { duration: int, remaining: float, ends_at: float | None }, (of the current Introduction or Discussion)
#       last_activity: int
#   },
#   ...
# }


MAX_STUDENTS = 300 # Students in a Tutorial

IDLE_LIMIT = 60 * 60 # Seconds without activity until a Tutorial is closed
CLEANUP_INTERVAL = 60 # Seconds


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


def emit_staff_update(code):
    if not (tutorial := tutorials.get(code)):
        return

    payload = {
        "tutorial_code": code,
        "tutorial_name": tutorial.get("name"),
        "state": str(tutorial.get("state")),
        "locked": tutorial.get("locked"),
        "group_size": tutorial.get("group_size"),
        "max_groups": tutorial.get("max_groups"),
        "available_attributes": tutorial.get("available_attributes", []),
        "students": {
            student_id: {
                "name": student.get("name"),
                "attributes_complete": student.get("attributes_complete"),
                "connected": is_connected(student_id),
            }
            for student_id, student in tutorial.get("students", {}).items()
        },
        "groups": tutorial.get("groups", {}),
        "round": tutorial.get("round"),
        "questions": tutorial.get("questions", []),
        "discussion_time": tutorial.get("discussion_time"),
        "timer": timer.get_state(tutorial["timer"]),
    }
    emit("tutorial_update", payload, room=code, namespace="/staff")


def emit_tutorial_update(code):
    tutorial = tutorials.get(code)
    if not tutorial:
        for ns in ["/", "/staff"]:
            emit("error", {"message": "This tutorial session could not be found."}, room=code, namespace=ns)
        return

    emit_staff_update(code)

    students = tutorial.get("students", {})
    groups = tutorial.get("groups", {})

    tutorial_name = tutorial.get("name")
    state = str(tutorial.get("state"))
    available_attributes = tutorial.get("available_attributes", [])
    questions = tutorial.get("questions", [])
    timer_state = timer.get_state(tutorial["timer"])

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
            "round": tutorial.get("round"),
            "formation": tutorial.get("formation"),
            "questions": questions,
            "discussion_time": tutorial.get("discussion_time"),
            "timer": timer_state,
        }
        emit("student_update", payload, room=student_id, namespace="/")


def is_connected(user_id):
    return bool(users.get(user_id, {}).get("sessions"))


def record_activity(code):
    if tutorial := tutorials.get(code):
        tutorial["last_activity"] = int(time.time())


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
        if not user.get("sessions") and not user.get("tutorial"):
            del users[user_id]

    return True


def begin_discussion(code):
    """Moves a tutorial from its Introductions into the Discussion, starting the full Discussion time"""
    if not (tutorial := tutorials.get(code)):
        return

    tutorial["state"] = TutorialState.DISCUSSION
    timer.reset(code, tutorial["discussion_time"])
    timer.start(code)


def close_tutorial(code, reason="ended"):
    """Ends a tutorial for everyone in it, deleting all of its data"""
    if not (tutorial := tutorials.get(code)):
        return

    timer.stop(code)
    tutorial["state"] = TutorialState.ENDED

    for namespace in ["/", "/staff"]:
        emit("tutorial_ended", {"tutorial_code": code, "reason": reason}, room=code, namespace=namespace)
        close_room(code, namespace=namespace)

    del tutorials[code]

    for user_id in [tutorial["staff"], *tutorial["students"]]:
        if not (user := users.get(user_id)):
            continue
        if user.get("tutorial") == code:
            user["tutorial"] = None
        if not user["sessions"] and not user.get("tutorial"):
            del users[user_id]


def cleanup_expired_tutorials():
    """Closes tutorials which have been idle for too long (a running Discussion Timer is never idle)"""
    current_time = time.time()

    for code, tutorial in list(tutorials.items()):
        if timer.is_running(tutorial["timer"]):
            continue
        if current_time - tutorial["last_activity"] > IDLE_LIMIT:
            close_tutorial(code, reason="idle")

def run_cleanup(app, socketio):
    """Periodically cleans up tutorials (never returns, so should be started as a Background Task)"""
    while True:
        socketio.sleep(CLEANUP_INTERVAL)
        try:
            with app.app_context():
                cleanup_expired_tutorials()
        except Exception:
            app.logger.exception("Tutorials could not be cleaned up")


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

    # Number the Name if another can't be found (e.g. if most names are already taken)
    attempts, number = 0, 2
    while student_name in student_names:
        attempts += 1
        if attempts <= 50:
            student_name = _generate_student_name()
        else:
            student_name = f"{_generate_student_name()}-{number}"
            number += 1
    return student_name
