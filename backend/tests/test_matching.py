import itertools, random
import numpy as np
import pytest

from app.enums import DEFAULT_AVAILABLE_ATTRIBUTES, VALID_AVAILABILITY_CODES
from app.sockets.matching import form_groups, get_group_sizes, improve_groups, score_common_times


CODES = sorted(VALID_AVAILABILITY_CODES)


def make_student(**attributes):
    return {"attributes": attributes}

def random_student():
    return make_student(
        goal_grade=random.choice([4, 5, 6, 7]),
        current_gpa=random.choice([4, 5, 6, 7, None]),
        availability=random.sample(CODES, random.randint(0, 8)),
        communication=random.sample(["email", "teams", "discord"], random.randint(0, 3)),
        meeting_mode=random.choice(["physical", "virtual", "either", None]),
    )

def make_tutorial(students, group_size, max_groups=None, available_attributes=DEFAULT_AVAILABLE_ATTRIBUTES):
    return {
        "group_size": group_size, "max_groups": max_groups, "available_attributes": available_attributes,
        "students": {f"s{i}": student for i, student in enumerate(students)}, "previous_matches": {},
    }

def record_matches(tutorial, groups):
    for members in groups.values():
        for member in members:
            tutorial["previous_matches"].setdefault(member, set()).update(set(members) - {member})

def group_sizes(groups):
    return sorted((len(members) for members in groups.values()), reverse=True)

@pytest.fixture(autouse=True)
def seed():
    random.seed(1)


@pytest.mark.parametrize("total", [2, 3, 5, 7, 16, 31])
@pytest.mark.parametrize("group_size", [2, 3, 5, 10])
@pytest.mark.parametrize("max_groups", [None, 2, 4])
def test_every_student_is_in_one_group(total, group_size, max_groups):
    tutorial = make_tutorial([random_student() for _ in range(total)], group_size, max_groups)
    groups = form_groups(tutorial)

    assert sorted(itertools.chain(*groups.values())) == sorted(tutorial["students"])
    assert list(groups) == list(range(1, len(groups) + 1))
    assert max_groups is None or len(groups) <= max_groups
    assert group_sizes(groups) == get_group_sizes(total, group_size, max_groups)
    assert min(group_sizes(groups)) >= 2


@pytest.mark.parametrize("total, group_size, expected", [
    (6, 5, [6]), (7, 5, [5, 2]), (8, 5, [5, 3]), (10, 5, [5, 5]), (16, 5, [6, 5, 5]), (3, 5, [3]), (1, 5, [1]),
    (3, 2, [3]), (5, 2, [3, 2]), (6, 2, [2, 2, 2]), (11, 10, [11]),
])
def test_group_sizes(total, group_size, expected):
    assert get_group_sizes(total, group_size) == expected

@pytest.mark.parametrize("total, group_size, max_groups, expected", [
    (7, 5, 2, [5, 2]), (12, 5, 2, [6, 6]), (30, 5, 4, [8, 8, 7, 7]), (11, 5, 2, [6, 5]),
])
def test_group_sizes_with_maximum_groups(total, group_size, max_groups, expected):
    assert get_group_sizes(total, group_size, max_groups) == expected


def test_no_students():
    assert form_groups(make_tutorial([], 4)) == {}

def test_no_attributes():
    tutorial = make_tutorial([random_student() for _ in range(9)], 3, available_attributes=[])
    assert group_sizes(form_groups(tutorial)) == [3, 3, 3]


def test_students_with_the_same_goal_are_matched():
    students = [make_student(goal_grade=goal) for goal in (4, 7) * 4]
    tutorial = make_tutorial(students, 4, available_attributes=["goal_grade"])

    for members in form_groups(tutorial).values():
        assert len({tutorial["students"][member]["attributes"]["goal_grade"] for member in members}) == 1


def test_groups_share_a_common_time():
    # Each pair of Students shares a time with someone, but only one way of grouping suits Entire Groups
    students = [make_student(availability=[code, "SUNE"] if i % 2 else [code]) for i, code in enumerate(["MONM", "TUEA", "WEDE"] * 4)]
    tutorial = make_tutorial(students, 4, available_attributes=["availability"])

    for members in form_groups(tutorial).values():
        times = [set(tutorial["students"][member]["attributes"]["availability"]) for member in members]
        assert set.intersection(*times)


def test_common_times_score():
    everyone = np.array([[1, 1, 0], [1, 1, 0], [1, 1, 1]])
    some = np.array([[1, 1, 0], [1, 1, 0], [0, 0, 1]])
    assert score_common_times(everyone) == pytest.approx(1)
    assert 0 < score_common_times(some) < 0.5
    assert score_common_times(np.zeros((3, 3))) == 0
    assert score_common_times(np.vstack([everyone, np.zeros((1, 3))])) == pytest.approx(1) # Not provided


def test_rematches_are_avoided():
    tutorial = make_tutorial([random_student() for _ in range(16)], 4)
    met = {student: set() for student in tutorial["students"]}

    for _ in range(3):
        groups = form_groups(tutorial)
        record_matches(tutorial, groups)
        for members in groups.values():
            for member in members:
                met[member].update(set(members) - {member})

    assert sum(len(others) for others in met.values()) / len(met) > 7.5 # Out of 9


def test_improving_groups_never_lowers_the_score():
    weights = np.random.default_rng(1).random((12, 12))
    score = lambda group: weights[np.ix_(group, group)].sum()

    groups = [list(range(0, 4)), list(range(4, 8)), list(range(8, 12))]
    before = sum(score(group) for group in groups)
    improve_groups(groups, score)

    assert sum(score(group) for group in groups) >= before
    assert sorted(itertools.chain(*groups)) == list(range(12))
