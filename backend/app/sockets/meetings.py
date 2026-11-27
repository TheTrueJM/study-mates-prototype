"""
Who each Student has Met (their Groups once Introductions began), and the Classmates they've Shortlisted
as potential Teammates. Shortlists are private until the Wrap-Up, where Students who Shortlisted
each other (Mutual Shortlists) are revealed to both of them.

Students are referred to by their Public ID here (never their UUID, which identifies their connection).
"""
from ..enums import TutorialState, AttributeType
from ..custom_attributes import is_custom
from . import utils


MEETING_STATES = {TutorialState.INTRODUCTION, TutorialState.DISCUSSION}

EQUAL_ATTRIBUTES = {
    str(AttributeType.GOAL_GRADE), str(AttributeType.CURRENT_GPA), str(AttributeType.YEAR), str(AttributeType.SEMESTER)
}
OVERLAPPING_ATTRIBUTES = {str(AttributeType.AVAILABILITY), str(AttributeType.COMMUNICATION)}


def count_common(tutorial, viewer, other) -> int:
    """
    How many Details a Student has in Common with Another, from what the Other Student shares
    (mirrors compareAttributes in frontend/src/constants/attributes.js)
    """
    own = viewer.get("attributes") or {}
    shared = utils.get_public_attributes(other, tutorial["available_attributes"], tutorial.get("custom_attributes", []))
    common = 0

    for attribute, value in shared.items():
        mine = own.get(attribute)
        if mine is None or mine == [] or mine == "":
            continue

        if attribute == str(AttributeType.MEETING_MODE):
            common += mine == value or "either" in (mine, value)
        elif attribute in OVERLAPPING_ATTRIBUTES or (is_custom(attribute) and isinstance(value, list)):
            common += bool(set(mine if isinstance(mine, list) else [mine]) & set(value))
        elif attribute in EQUAL_ATTRIBUTES or is_custom(attribute):
            common += mine == value

    return common


def record_group(tutorial, group_number):
    """
    Records that the Members of a Group have Met (once per Round), along with how many
    Details they have in Common (updated each time, so it reflects when they last Met)
    """
    students = tutorial["students"]
    members = [member for member in tutorial["groups"].get(group_number, []) if member in students]

    for member_id in members:
        history = tutorial["history"].setdefault(member_id, {})
        for other_id in members:
            if other_id == member_id:
                continue

            other = students[other_id]
            entry = history.setdefault(other["public_id"], {"times": 0, "round": None})
            if entry["round"] != tutorial["round"]:
                entry["times"] += 1
            entry.update(
                name=other["name"],
                round=tutorial["round"],
                group=group_number,
                common=count_common(tutorial, students[member_id], other),
            )


def record_meetings(tutorial):
    """Records every Group as having Met, while their Introductions or Discussion is running"""
    if tutorial["state"] not in MEETING_STATES:
        return
    for group_number in tutorial["groups"]:
        record_group(tutorial, group_number)


def find_student(tutorial, public_id):
    """Returns the UUID of the Student with a Public ID (None if they aren't in the tutorial)"""
    for student_id, student in tutorial["students"].items():
        if student.get("public_id") == public_id:
            return student_id
    return None


def is_mutual(tutorial, student_id, public_id) -> bool:
    other_id = find_student(tutorial, public_id)
    own_id = tutorial["students"].get(student_id, {}).get("public_id")
    return (
        other_id is not None
        and public_id in tutorial["shortlists"].get(student_id, ())
        and own_id in tutorial["shortlists"].get(other_id, ())
    )


def can_shortlist(tutorial, student_id, public_id) -> bool:
    """Students can Shortlist anyone they've Met, or anyone in their Current Group"""
    if public_id in tutorial["history"].get(student_id, {}):
        return True

    group = tutorial["groups"].get(tutorial["students"][student_id].get("group"), [])
    return any(tutorial["students"][member].get("public_id") == public_id for member in group if member != student_id)


def mutual_pairs(tutorial) -> int:
    """How many Pairs of Students have Shortlisted each other"""
    pairs = 0
    for student_id, shortlist in tutorial["shortlists"].items():
        own_id = tutorial["students"].get(student_id, {}).get("public_id")
        for public_id in shortlist:
            other_id = find_student(tutorial, public_id)
            if other_id and own_id in tutorial["shortlists"].get(other_id, ()):
                pairs += 1
    return pairs // 2


def get_history(tutorial, student_id):
    """The Classmates a Student has Met, most recently first (Mutual Shortlists are only revealed at the Wrap-Up)"""
    shortlisting = tutorial.get("shortlisting")
    revealed = shortlisting and tutorial["state"] == TutorialState.WRAP_UP
    shortlist = tutorial["shortlists"].get(student_id, set())
    present = {student.get("public_id") for student in tutorial["students"].values()}

    history = [
        {
            "id": public_id,
            "name": entry["name"],
            "times": entry["times"],
            "common": entry["common"],
            "round": entry["round"],
            "group": entry["group"],
            "left": public_id not in present,
            "shortlisted": bool(shortlisting) and public_id in shortlist,
            "mutual": bool(revealed) and is_mutual(tutorial, student_id, public_id),
        }
        for public_id, entry in tutorial["history"].get(student_id, {}).items()
    ]
    history.sort(key=lambda entry: (-(entry["round"] or 0), entry["name"]))
    return history


def previously_met(tutorial, student_id, public_id) -> int:
    """How many times a Student Met another before their Current Round"""
    entry = tutorial["history"].get(student_id, {}).get(public_id)
    if not entry:
        return 0
    current = entry["round"] == tutorial["round"] and tutorial["state"] in MEETING_STATES | {TutorialState.WRAP_UP}
    return entry["times"] - (1 if current else 0)


def forget_student(tutorial, student_id):
    """Deletes a Student's own History and Shortlist (other Students still remember Meeting them)"""
    tutorial["history"].pop(student_id, None)
    tutorial["shortlists"].pop(student_id, None)
