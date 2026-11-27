"""Students who need to stay at their Table (see app/sockets/seating.py)"""
import itertools, random, statistics
import numpy as np
import pytest

from app.sockets.utils import tutorials
from app.sockets.matching import form_groups, improve_groups, number_groups, build_matrix, build_availability, score_group

from test_matching import random_student, make_tutorial, record_matches


@pytest.fixture(autouse=True)
def seed():
    random.seed(1)


def seated_tutorial(total, group_size, tables, max_groups=None, seating=True):
    """A Tutorial of Random Students, where the First Students stay at the given Tables"""
    tutorial = make_tutorial([random_student() for _ in range(total)], group_size, max_groups)
    tutorial["seating"] = seating
    for i, table in enumerate(tables):
        tutorial["students"][f"s{i}"].update(stay_seated=True, table=table)
    return tutorial

def every_student_once(tutorial, groups):
    members = list(itertools.chain(*groups.values()))
    return sorted(members) == sorted(tutorial["students"])


# ===== Matching ===== #

@pytest.mark.parametrize("total, group_size, tables", [(12, 4, [5]), (20, 4, [1, 3]), (9, 2, [7, 2, 4]), (30, 5, [6] * 3)])
def test_seated_students_are_grouped_at_their_table(total, group_size, tables):
    for _ in range(5):
        tutorial = seated_tutorial(total, group_size, tables)
        groups = form_groups(tutorial)
        assert every_student_once(tutorial, groups)
        for i, table in enumerate(tables):
            assert f"s{i}" in groups[table]

def test_other_groups_take_the_lowest_free_numbers():
    groups = form_groups(seated_tutorial(12, 4, [5]))
    assert sorted(groups) == [1, 2, 5]

    groups = form_groups(seated_tutorial(16, 4, [2, 4]))
    assert sorted(groups) == [1, 2, 3, 4]
    assert number_groups([None, 3, None, None, 1]) == [2, 3, 4, 5, 1]

def test_group_sizes_are_unchanged_by_seating():
    groups = form_groups(seated_tutorial(17, 4, [8, 3]))
    assert sorted(len(members) for members in groups.values()) == [4, 4, 4, 5]

def test_seated_students_at_the_same_table_are_together():
    groups = form_groups(seated_tutorial(12, 4, [3, 3]))
    assert {"s0", "s1"} <= set(groups[3])

def test_seated_students_at_different_tables_are_apart():
    # Only one Group would usually be Formed
    groups = form_groups(seated_tutorial(5, 5, [2, 7]))
    assert sorted(groups) == [2, 7] and every_student_once(seated_tutorial(5, 5, [2, 7]), groups)
    assert sorted(len(members) for members in groups.values()) == [2, 3]

def test_every_seated_table_has_a_group_beyond_the_group_limit():
    tutorial = seated_tutorial(12, 4, [1, 2, 3, 4], max_groups=2)
    groups = form_groups(tutorial)
    assert sorted(groups) == [1, 2, 3, 4] and every_student_once(tutorial, groups)

def test_a_large_seated_table_keeps_every_student():
    tutorial = seated_tutorial(8, 2, [4, 4, 4])
    groups = form_groups(tutorial)
    assert {"s0", "s1", "s2"} <= set(groups[4]) and every_student_once(tutorial, groups)

def test_seating_is_ignored_when_turned_off_or_without_a_table():
    groups = form_groups(seated_tutorial(12, 4, [5], seating=False))
    assert sorted(groups) == [1, 2, 3]

    tutorial = seated_tutorial(12, 4, [None])
    assert sorted(form_groups(tutorial)) == [1, 2, 3]

def test_fixed_students_are_never_swapped():
    weights = np.random.default_rng(1).random((12, 12))
    score = lambda group: weights[np.ix_(group, group)].sum()
    groups = [list(range(0, 4)), list(range(4, 8)), list(range(8, 12))]

    improve_groups(groups, score, fixed={0, 5})
    assert 0 in groups[0] and 5 in groups[1]
    assert sorted(itertools.chain(*groups)) == list(range(12))

def test_seated_students_still_meet_new_classmates():
    """As many as anyone else (see test_rematches_are_avoided)"""
    met = []
    for _ in range(10):
        tutorial = seated_tutorial(16, 4, [2])
        others = set()
        for _ in range(3):
            groups = form_groups(tutorial)
            record_matches(tutorial, groups)
            others |= set(groups[2]) - {"s0"}
        met.append(len(others))
    assert statistics.mean(met) > 7.5 # Out of 9

def test_seated_students_are_matched_as_well_as_everyone_else():
    """Across many Classes, a Seated Student's Group is about as Compatible as anyone else's"""
    seated, others = [], []
    for _ in range(20):
        tutorial = seated_tutorial(20, 4, [3])
        groups = form_groups(tutorial)
        ids = list(tutorial["students"])
        connections = build_matrix(ids, tutorial["students"], tutorial["available_attributes"])
        availability = build_availability(ids, tutorial["students"], tutorial["available_attributes"])
        rematches = np.zeros((len(ids), len(ids)))
        for members in groups.values():
            group = [ids.index(member) for member in members]
            score = score_group(group, connections, availability, rematches) / len(group)
            (seated if "s0" in members else others).append(score)

    assert statistics.mean(seated) >= 0.9 * statistics.mean(others)


# ===== Students ===== #

def latest(client, event="tutorial_update"):
    return client.received(event)[-1]

def seat(client, stay_seated=True, table=None):
    return client.emit("update_seating", {"stay_seated": stay_seated, "table": table})

def staff_view(staff, client):
    return latest(staff)["students"][client.id]

def test_seating_is_on_by_default(staff, connect_student):
    student = connect_student(staff.code)
    assert tutorials[staff.code]["seating"] is True
    assert latest(student, "student_update")["seating"] is True
    assert latest(staff)["seating"] is True

def test_staying_seated_without_a_table_asks_for_the_table_numbers(staff, connect_student):
    student = connect_student(staff.code)
    assert seat(student)["ok"]
    view = staff_view(staff, student)
    assert (view["stay_seated"], view["table"], view["needs_table"]) == (True, None, True)

    assert seat(student, table=5)["ok"]
    view = staff_view(staff, student)
    assert view["table"] == 5 and not view["needs_table"]
    update = latest(student, "student_update")
    assert update["stay_seated"] and update["table"] == 5

    # Resetting the Table asks for the Table Numbers again
    assert seat(student, table=None)["ok"]
    assert staff_view(staff, student)["needs_table"]

    # No longer Staying Seated forgets the Table
    assert seat(student, False, 5)["ok"]
    assert tutorials[staff.code]["students"][student.id]["table"] is None
    assert not staff_view(staff, student)["needs_table"]

@pytest.mark.parametrize("data", [
    {"stay_seated": True, "table": 0}, {"stay_seated": True, "table": 100}, {"stay_seated": True, "table": "abc"},
    {"stay_seated": True, "table": True}, {"stay_seated": True, "table": 2.5}, {"stay_seated": "yes"}, {}, "5",
])
def test_invalid_seating(staff, connect_student, data):
    student = connect_student(staff.code)
    assert not student.emit("update_seating", data)["ok"]
    assert not tutorials[staff.code]["students"][student.id]["stay_seated"]

@pytest.mark.parametrize("table, expected", [("7", 7), (7.0, 7), (99, 99), ("", None)])
def test_table_numbers(staff, connect_student, table, expected):
    student = connect_student(staff.code)
    assert seat(student, table=table)["ok"]
    assert tutorials[staff.code]["students"][student.id]["table"] == expected

def test_seating_can_be_turned_off(staff, connect_student):
    student = connect_student(staff.code)
    seat(student, table=4)
    assert staff.emit("update_settings", {"seating": False})["ok"]
    assert not seat(student, table=4)["ok"]
    assert not latest(staff)["students"][student.id]["needs_table"]

    # Students staying at a Table are Grouped like everyone else while it's off
    connect_student(staff.code)
    staff.emit("start_grouping")
    assert list(tutorials[staff.code]["groups"]) == [1] and not tutorials[staff.code]["table_numbering"]

    assert not staff.emit("update_settings", {"seating": "no"})["ok"]

def test_classmates_never_see_who_is_seated(staff, connect_student):
    clients = [connect_student(staff.code) for _ in range(2)]
    seat(clients[0], table=3)
    staff.emit("start_grouping")
    members = latest(clients[1], "student_update")["group_members"]
    assert members and all(set(member) == {"id", "name", "attributes", "met", "shortlisted"} for member in members)


# ===== Grouping ===== #

def grouped(staff, connect_student, students=6, tables=(), **settings):
    staff.emit("update_settings", {"group_size": 2, **settings})
    clients = [connect_student(staff.code) for _ in range(students)]
    for client, table in zip(clients, tables):
        seat(client, table=table)
    assert staff.emit("start_grouping")["ok"]
    return clients

def group_of(staff, client):
    return tutorials[staff.code]["students"][client.id]["group"]

def test_groups_are_formed_at_seated_tables(staff, connect_student):
    clients = grouped(staff, connect_student, 6, tables=[5])
    tutorial = tutorials[staff.code]
    assert sorted(tutorial["groups"]) == [1, 2, 5] and group_of(staff, clients[0]) == 5
    assert tutorial["table_numbering"]
    assert latest(clients[1], "student_update")["table_numbering"]

    staff.emit("return_lobby")
    assert not tutorials[staff.code]["table_numbering"]

def test_groups_without_seated_students_are_not_numbered_by_table(staff, connect_student):
    grouped(staff, connect_student, 4)
    assert not tutorials[staff.code]["table_numbering"]

def test_seated_students_are_only_moved_when_confirmed(staff, connect_student):
    clients = grouped(staff, connect_student, 6, tables=[5])
    student = clients[0]

    response = staff.emit("move_student", {"student_id": student.id, "group": 1})
    assert not response["ok"] and response["seated"] and group_of(staff, student) == 5

    # e.g. their Table Number was wrong, so they stay at the Table of their New Group
    response = staff.emit("move_student", {"student_id": student.id, "group": 1, "force": True})
    assert response["ok"] and group_of(staff, student) == 1
    assert tutorials[staff.code]["students"][student.id]["table"] == 1
    assert latest(student, "moved_group") == {"group_number": 1, "table": 1}

def test_others_can_be_moved_into_a_seated_group(staff, connect_student):
    clients = grouped(staff, connect_student, 6, tables=[5])
    other = next(client for client in clients[1:] if group_of(staff, client) != 5)
    assert staff.emit("move_student", {"student_id": other.id, "group": 5})["ok"]
    assert latest(other, "moved_group") == {"group_number": 5, "table": None}

def test_new_groups_take_the_lowest_free_number(staff, connect_student):
    clients = grouped(staff, connect_student, 6, tables=[5])
    response = staff.emit("move_student", {"student_id": clients[1].id, "group": "new"})
    assert response["ok"] and response["group_number"] == 3

    # Skipping the Tables of Seated Students (even those not yet placed at it)
    tutorials[staff.code]["students"][clients[2].id].update(stay_seated=True, table=4)
    other = next(client for client in clients[3:] if len(tutorials[staff.code]["groups"][group_of(staff, client)]) > 1)
    assert staff.emit("move_student", {"student_id": other.id, "group": "new"})["group_number"] == 6


# ===== Seating once Grouped ===== #

def test_joining_the_group_at_their_table(staff, connect_student):
    clients = grouped(staff, connect_student, 6)
    student = clients[0]
    target = next(group for group in tutorials[staff.code]["groups"] if group != group_of(staff, student))

    assert seat(student, table=target)["group_number"] == target
    assert group_of(staff, student) == target and tutorials[staff.code]["table_numbering"]

def test_renumbering_their_group_to_their_table(staff, connect_student):
    clients = grouped(staff, connect_student, 6)
    student = clients[0]
    members = list(tutorials[staff.code]["groups"][group_of(staff, student)])

    assert seat(student, table=8)["group_number"] == 8
    assert tutorials[staff.code]["groups"][8] == members
    assert all(group_of(staff, client) == 8 for client in clients if client.id in members)

def test_not_renumbering_a_group_with_another_seated_student(staff, connect_student):
    clients = grouped(staff, connect_student, 6, tables=[5])
    partner = next(client for client in clients[1:] if group_of(staff, client) == 5)
    seat(partner, table=9)
    assert group_of(staff, partner) == 5 and 9 not in tutorials[staff.code]["groups"]

def test_seating_during_a_discussion(staff, connect_student):
    clients = grouped(staff, connect_student, 6)
    staff.emit("start_discussion")
    student = clients[0]
    current = group_of(staff, student)
    target = next(group for group in tutorials[staff.code]["groups"] if group != current)

    # Groups weren't sent to the Table with their Number, so it's left to the Staff Member
    seat(student, table=target)
    assert group_of(staff, student) == current

    # Groups are meeting at their Tables, so the Student is already with the Group at theirs
    tutorials[staff.code]["table_numbering"] = True
    seat(student, table=None)
    seat(student, table=target)
    assert group_of(staff, student) == target


# ===== Presets ===== #

def test_presets_keep_the_seating_setting(staff):
    from app.settings import validate_settings
    assert validate_settings({"group_size": 4})[0]["seating"] is True
    assert validate_settings({"group_size": 4, "seating": False})[0]["seating"] is False
    assert validate_settings({}, current=tutorials[staff.code])[0]["seating"] is True
