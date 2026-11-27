import pytest

from app.sockets.utils import tutorials


def latest(client, event="student_update"):
    """The latest payload of an event (kept, so it can be checked more than once)"""
    cache = client.__dict__.setdefault("latest", {})
    if events := client.received(event):
        cache[event] = events[-1]
    return cache[event]

def setup(connect_staff, connect_student, students=4, **settings):
    staff = connect_staff()
    staff.code = staff.emit("create_tutorial", {"group_size": 2, "shortlisting": True, **settings})["tutorial_code"]
    clients = [connect_student(staff.code) for _ in range(students)]
    return staff, clients

def public_id(staff, client):
    return tutorials[staff.code]["students"][client.id]["public_id"]

def partner(staff, clients, client):
    group = tutorials[staff.code]["students"][client.id]["group"]
    return next(c for c in clients if c is not client and tutorials[staff.code]["students"][c.id]["group"] == group)

def discuss(staff):
    assert staff.emit("start_grouping")["ok"]
    assert staff.emit("start_discussion")["ok"]


def test_students_have_a_public_id_shown_to_their_group(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student)
    staff.emit("start_grouping")
    members = latest(clients[0])["group_members"]
    assert {m["id"] for m in members} == {public_id(staff, c) for c in clients if c is clients[0] or c is partner(staff, clients, clients[0])}
    assert all(c.id not in str(latest(clients[1])) for c in clients if c is not clients[1]) # UUIDs are never shared

def test_meetings_are_recorded_once_introductions_begin(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student)
    staff.emit("start_grouping")
    assert latest(clients[0])["history"] == [] # Grouped, but haven't Met yet

    staff.emit("start_discussion")
    other = partner(staff, clients, clients[0])
    history = latest(clients[0])["history"]
    assert [(h["id"], h["times"], h["round"]) for h in history] == [(public_id(staff, other), 1, 1)]
    assert latest(clients[0])["group_members"][0]["met"] == 0 # Not before this Round

    staff.emit("start_grouping") # The next Round doesn't count the same meeting again
    assert latest(clients[0])["history"][0]["times"] == 1

def test_meeting_again_is_counted(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student, students=2)
    discuss(staff)
    discuss(staff)
    update = latest(clients[0])
    assert update["history"][0]["times"] == 2
    assert sorted(member["met"] for member in update["group_members"]) == [0, 1] # Themselves, and their Partner

def test_details_in_common_are_counted(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student, students=2, available_attributes=["goal_grade", "availability", "year"])
    a, b = clients
    a.emit("update_details", {"goal_grade": 6, "availability": ["MONM", "TUEA"], "year": 2})
    b.emit("update_details", {"goal_grade": 6, "availability": ["TUEA"], "year": 3, "shared_attributes": ["availability"]})
    discuss(staff)
    assert latest(a)["history"][0]["common"] == 1 # Only what B shares (their goal grade is hidden)
    assert latest(b)["history"][0]["common"] == 2

    b.emit("update_details", {"shared_attributes": ["availability", "goal_grade"]})
    staff.emit("wrap_up") # Updated when they leave their Group
    assert latest(a)["history"][0]["common"] == 2

def test_late_joiners_and_moved_students_meet_their_group(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student)
    discuss(staff)
    late = connect_student(staff.code)
    assert latest(late)["history"] and all(h["round"] == 1 for h in latest(late)["history"])

    student = clients[0]
    target = next(g for g, m in tutorials[staff.code]["groups"].items() if student.id not in m)
    staff.emit("move_student", {"student_id": student.id, "group": target})
    met = {h["id"] for h in latest(student)["history"]}
    assert {public_id(staff, c) for c in clients + [late] if c.id in tutorials[staff.code]["groups"][target] and c is not student} <= met


def test_shortlisting(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student)
    discuss(staff)
    a = clients[0]
    b = partner(staff, clients, a)

    assert a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": True})["ok"]
    assert latest(a)["history"][0]["shortlisted"] and not latest(a)["history"][0]["mutual"]
    assert b.emit("shortlist", {"id": public_id(staff, a), "shortlisted": True})["ok"]
    assert not latest(a)["history"][0]["mutual"] # Hidden until the Wrap-Up
    assert not a.received("mutual_shortlist")

    # Can still be removed before the Wrap-Up (it isn't known to be Mutual yet)
    assert a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": False})["ok"]
    a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": True})

    staff.emit("wrap_up")
    assert latest(a)["history"][0]["mutual"] and latest(b)["history"][0]["mutual"]
    assert latest(a, "mutual_shortlist")["count"] == 1
    assert latest(staff, "tutorial_update")["mutual_pairs"] == 1

    # Revealed Mutual Shortlists stay
    assert not a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": False})["ok"]

def test_shortlisting_each_other_during_the_wrap_up(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student)
    discuss(staff)
    staff.emit("wrap_up")
    a = clients[0]
    b = partner(staff, clients, a)

    a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": True})
    assert a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": False})["ok"] # Not Mutual
    a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": True})
    b.emit("shortlist", {"id": public_id(staff, a), "shortlisted": True})
    assert latest(a, "mutual_shortlist")["name"] == tutorials[staff.code]["students"][b.id]["name"]
    assert latest(b, "mutual_shortlist")["name"] == tutorials[staff.code]["students"][a.id]["name"]

def test_only_classmates_you_have_met_can_be_shortlisted(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student)
    staff.emit("start_grouping")
    a = clients[0]
    b = partner(staff, clients, a)
    stranger = next(c for c in clients if c not in (a, b))

    assert a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": True})["ok"] # In their Group
    assert not a.emit("shortlist", {"id": public_id(staff, stranger), "shortlisted": True})["ok"]
    assert not a.emit("shortlist", {"id": "made-up", "shortlisted": True})["ok"]
    assert not a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": "yes"})["ok"]

def test_shortlisting_is_off_by_default(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student, shortlisting=False)
    discuss(staff)
    a = clients[0]
    assert latest(a)["shortlisting"] is False
    assert not a.emit("shortlist", {"id": public_id(staff, partner(staff, clients, a)), "shortlisted": True})["ok"]
    assert latest(a)["history"] # History is still shown

    staff_default = connect_staff()
    code = staff_default.emit("create_tutorial", {"group_size": 2})["tutorial_code"]
    assert tutorials[code]["shortlisting"] is False
    assert not staff_default.emit("update_settings", {"shortlisting": "on"})["ok"]

def test_leaving_deletes_the_students_history_and_shortlist(connect_staff, connect_student):
    staff, clients = setup(connect_staff, connect_student)
    discuss(staff)
    a = clients[0]
    b = partner(staff, clients, a)
    a.emit("shortlist", {"id": public_id(staff, b), "shortlisted": True})
    b.emit("shortlist", {"id": public_id(staff, a), "shortlisted": True})
    a.emit("leave_tutorial")

    tutorial = tutorials[staff.code]
    assert a.id not in tutorial["history"] and a.id not in tutorial["shortlists"]
    staff.emit("wrap_up")
    entry = latest(b)["history"][0]
    assert entry["left"] and not entry["mutual"] # B still remembers Meeting them
