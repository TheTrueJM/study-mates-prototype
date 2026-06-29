from flask_socketio import emit
import random, string, uuid, time

from ..enums import TutorialState, AttributeType, VALID_ATTRIBUTES


users = dict() # { UUID: {sessions: {sID, ...}, role: student|staff|None, tutorial: code|None}, ... }
sessions = dict() # { sID: UUID }
tutorials = dict()
# {
#   code: {
#       staff: UUID,
#       name: str,
#       state: TutorialState,
#       group_size: int,
#       max_groups: int,
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

DESCRIPTORS = {
    'agile', 'anonymous', 'blazing', 'blissful', 'bold', 'brave', 'bright', 'calm', 'cheerful',
    'clever', 'colorful', 'cosmic',  'curious', 'daring', 'dazzling', 'energetic', 'epic',
    'friendly', 'frosty', 'gentle', 'glowing', 'golden', 'graceful', 'happy', 'hasty', 'heroic',
    'hidden', 'jolly', 'joyful', 'kind', 'legendary', 'lively', 'lunar', 'midnight', 'mighty',
    'mysterious', 'mythic', 'nimble', 'noble', 'peaceful', 'playful', 'powerful', 'quick',
    'radiant', 'rapid', 'resilient', 'royal', 'shiny', 'silent', 'silver', 'smart', 'sneaky',
    'stealthy', 'stellar', 'strong', 'swift', 'valiant', 'vibrant', 'wild', 'wise', 'witty'
}
ANIMALS = {
    'armadillo', 'badger', 'bear', 'beaver', 'cat', 'chameleon', 'cheetah', 'chicken', 'cockatoo',
    'coyote', 'jackal', 'crow', 'dog', 'dolphin', 'duck', 'eagle', 'falcon', 'fish', 'flamingo',
    'fox', 'hawk', 'hedgehog', 'horse', 'jaguar', 'jellyfish', 'kangaroo', 'koala', 'leopard',
    'lion', 'lizard', 'meerkat', 'otter', 'owl', 'panda', 'panther', 'parrot', 'penguin', 'rabbit',
    'raccoon', 'raven', 'salamander', 'seal', 'serpent', 'shark', 'sheep', 'sloth', 'snake',
    'squirrel', 'swan', 'tiger', 'tortoise', 'turtle', 'wallaby', 'walrus', 'wolf', 'wombat', 'zebra'
}


day_index = {k: i for i, k in enumerate(DAYS.keys())}
time_index = {k: i for i, k in enumerate(TIMES.keys())}

format_availability = lambda code: (
    f"{DAYS.get(code[:3], code[:3])}-{TIMES.get(code[3:], code[3:])}" if len(code) == 4 else code
)
sort_availability = lambda codes: sorted(
    codes, key=lambda code: (day_index.get(code[:3], 99), time_index.get(code[3:], 99))
)


def emit_tutorial_update(code):
    tutorial = tutorials.get(code)
    if not tutorial:
        # TODO Update Error Messages
        for ns in ["/", "/staff"]:
            emit("error", {"message": "Tutorial Not Found"}, room=code, namespace=ns)
        return
                    
    students = tutorial.get("students", {})
    groups = tutorial.get("groups", {})

    staff_payload = {
        "tutorial_code": code,
        "tutorial_name": tutorial.get("name"),
        "state": tutorial.get("state"),
        "group_size": tutorial.get("group_size"),
        "max_groups": tutorial.get("max_groups"),
        "available_attributes": tutorial.get("available_attributes", []),
        "students": students,
        "groups": groups,
        "questions": tutorial.get("questions", []),
        "timer": tutorial.get("timer", {}),
    }
    emit("tutorial_update", staff_payload, room=code, namespace="/staff")

    formatted_students = dict()
    formatted_groups = dict()
    for student_id, student_data in tutorial.get("students", {}).items():
        group_number = student_data.get("group")
        group = tutorial.get("groups", {}).get(group_number)
        students = tutorial.get("students", {})

        members = None
        if group:
            if group_number in formatted_groups:
                members = formatted_groups[group_number]
            else:
                members = []
                for sid in group:
                    if sid and sid not in formatted_students:
                        student = students.get(sid, {})
                        student_details = dict()
                        student_details["name"] = student.get("name")
                        student_details["attributes"] = get_public_attributes()
                        formatted_students[sid] = student_details
                    members.append(formatted_students[sid])
                formatted_groups[group_number] = members

        payload = {
            "username": student_data.get("name"),
            "attributes": student_data.get("attributes", {}),
            "shared_attributes": student_data.get("shared_attributes", []),
            "attributes_complete": student_data.get("attributes_complete"),
            "tutorial_code": code,
            "tutorial_name": tutorial.get("name"),
            "state": tutorial.get("state"),
            "available_attributes": tutorial.get("available_attributes", []),
            "group_number": group_number,
            "group_members": members,
            "questions": tutorial.get("questions", []),
            "timer": tutorial.get("timer", {})
        }
        emit("student_update", payload, room=student_id, namespace="/")


def cleanup_expired_tutorials(): # TODO Run this Periodically in Application
    current_time = time.time()
    
    for code, tutorial in tutorials.items():
        if tutorial["state"] == TutorialState.ENDED:
            del tutorials[code]
            continue
        
        # Auto-expire if idle for 60 minutes
        if current_time - tutorial.get("last_activity", 0) > 3600:
            tutorial["state"] = TutorialState.ENDED
            del tutorials[code]


def get_public_attributes(student):
    public_attributes = {}
    if all_attributes := student.get("attributes"):
        for attribute in student.get("shared_attributes", []):
            match attribute:
                case AttributeType.AVAILABILITY:
                    public_attributes[attribute] = [
                        format_availability(code)
                        for code in sort_availability(all_attributes.get(attribute, []))
                    ]
                case _:
                    if attribute in VALID_ATTRIBUTES:
                        public_attributes[attribute] = all_attributes.get(attribute)
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
    return f"{random.choice(DESCRIPTORS)}-{random.choice(ANIMALS)}"

def generate_unique_student_name(tutorial_code):
    student_names = {student.get("name") for student in tutorials[tutorial_code].get("students", [])}
    student_name = _generate_student_name()
    while student_name in student_names:
        student_name = _generate_student_name()
    return student_name