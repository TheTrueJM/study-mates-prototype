"""
Seating Needs: Students who need to stay at their Table for the activity (e.g. due to a disability, injury,
health condition, or another access need). No reason is asked for.

Each Group meets at the Table with its Number, so a Seated Student's Group is always given the Number of their
Table and the rest of the Class moves around them. They're Matched exactly like everyone else (only their Group's
Number is decided by their Table). The only difference is that Seated Students at Different Tables can't be
Grouped together, as neither can move.

Whether a Student is staying Seated, and at which Table, is only ever shown to them and their Staff Member.
"""
from ..enums import TutorialState


MIN_TABLE, MAX_TABLE = 1, 99

GROUPED_STATES = {TutorialState.GROUPING, TutorialState.INTRODUCTION, TutorialState.DISCUSSION}


def get_table(tutorial, student):
    """The Table a Student is staying at (None if they aren't Seated, haven't set it yet, or Seating is turned off)"""
    if not tutorial.get("seating") or not student.get("stay_seated"):
        return None
    return student.get("table")


def seated_tables(tutorial):
    """The Tables of every Seated Student"""
    tables = (get_table(tutorial, student) for student in tutorial["students"].values())
    return {table for table in tables if table is not None}


def needs_table(tutorial, student):
    """Whether a Student is staying Seated, but doesn't know their Table Number yet"""
    return bool(tutorial.get("seating") and student.get("stay_seated") and student.get("table") is None)


def next_group_number(tutorial):
    """The Lowest Group Number not in use, skipping the Tables of Seated Students (as their Groups meet there)"""
    used = set(tutorial["groups"]) | seated_tables(tutorial)
    number = 1
    while number in used:
        number += 1
    return number


def validate_table(value):
    """Returns a tuple of the Table Number (None if not yet known) and an error message"""
    if value in (None, ""):
        return None, None

    if isinstance(value, str) and value.strip().isdigit():
        value = int(value.strip())
    elif isinstance(value, float) and value.is_integer():
        value = int(value)

    if not isinstance(value, int) or isinstance(value, bool) or not MIN_TABLE <= value <= MAX_TABLE:
        return None, f"Table Numbers are between {MIN_TABLE} and {MAX_TABLE}."
    return value, None
