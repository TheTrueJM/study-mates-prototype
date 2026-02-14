import pytest
import time
import logging
import random

from app.sockets import utils
from tests.helpers import set_session, get_last_received

logger = logging.getLogger(__name__)

def test_create_tutorial(client, socketio_client):
    namespace = "/staff"
    set_session(
       client,
       name="test",
       currentGPA=0.0,
       goalGPA=6.7,
       availability=""
    )
    sio = socketio_client(namespace=namespace, test_client=client, disconnect=False)
    logger.info(f"Connection: {sio.is_connected(namespace)}")

    assert sio.is_connected(namespace)
    response = get_last_received(sio, namespace=namespace)
    assert response is not None, "Timeout"
    uuid = response.get("uuid", False)
    assert uuid

    utils.users[uuid]["role"] = "staff"

    sio.emit("create_tutorial",
        {
            "name": "CAB202",
            "group_size": 2
        },
        namespace=namespace
    )

    time.sleep(0.5)

    code = utils.users[uuid].get("tutorial", None)
    assert code is not None

    tutorial = utils.tutorials.get(code)
    assert tutorial is not None

    assert tutorial["name"] == "CAB202"
    assert tutorial["group_size"] == 2
    assert tutorial["staff"] == uuid
    assert tutorial["state"] == "lobby"
    assert tutorial["students"] == dict()
    assert tutorial["groups"] == dict()
    assert tutorial["questions"] == list()

    response = get_last_received(sio, namespace=namespace)
    assert response is not None, "Timeout"
    assert response.get("code", None) == code

def test_create_tutorial_duplicate(client, socketio_client):
    namespace = "/staff"
    set_session(
       client,
       name="test",
       currentGPA=0.0,
       goalGPA=6.7,
       availability=""
    )
    sio = socketio_client(namespace=namespace, test_client=client, disconnect=False)


    response = get_last_received(sio, namespace=namespace)
    uuid = response.get("uuid")
    utils.users[uuid]["role"] = "staff"

    sio.emit("create_tutorial", {"name": "Tut1", "group_size": 2}, namespace=namespace)
    time.sleep(0.5)

    code = utils.users[uuid].get("tutorial")
    assert code is not None

    sio.emit("create_tutorial", {"name": "Tut2", "group_size": 2}, namespace=namespace)

    error_response = get_last_received(sio, namespace=namespace, name="error")
    assert error_response is not None
    assert error_response.get("message") == "Already in a tutorial"

def test_staff_creates_student_joins(app, client, socketio_client):
    staff_client = app.test_client()
    set_session(staff_client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(namespace="/staff", test_client=staff_client, disconnect=False)
    response = get_last_received(staff_sio, namespace="/staff")
    assert response is not None, "Staff connection timeout"
    staff_uuid = response.get("uuid")
    assert staff_uuid
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit("create_tutorial", {"name": "Jointest", "group_size": 3}, namespace="/staff")
    time.sleep(0.5)

    code = utils.users[staff_uuid].get("tutorial")
    assert code is not None

    student_client = app.test_client()
    set_session(student_client, name="Student1", currentGPA=5.0, goalGPA=6.0, availability="Mon")

    student_sio = socketio_client(test_client=student_client, disconnect=False)

    response = get_last_received(student_sio, name="session")
    assert response.get("uuid", False)
    student_uuid = response.get("uuid")

    student_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)
    assert student_uuid in tutorial["students"]
    assert tutorial["students"][student_uuid]["currentGPA"] == 5.0

    

    staff_sio.disconnect(namespace="/staff")
    student_sio.disconnect()

@pytest.mark.parametrize("num_students,group_size,expected_sizes", [
    (30, 5, [5, 5, 5, 5, 5, 5]),
    (30, 4, [2, 4, 4, 4, 4, 4, 4, 4]),
    (27, 3, [3, 3, 3, 3, 3, 3, 3, 3, 3]),
    (26, 3, [2, 3, 3, 3, 3, 3, 3, 3, 3]),
    (11, 4, [3, 4, 4]),
    (7, 3, [1, 3, 3]),
    (6, 3, [3, 3]),
    (5, 2, [1, 2, 2]),
    (2, 2, [2]),
    (1, 5, [1]),
])
# right now this counts odd ones out and puts them into a group instead
# of leaving them into a lobby. basically TODO
def test_grouping_logic(app, socketio_client, num_students, group_size, expected_sizes):
    staff_client = app.test_client()
    set_session(staff_client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(namespace="/staff", test_client=staff_client, disconnect=False)
    response = get_last_received(staff_sio, namespace="/staff")
    assert response is not None, "Staff connection timeout"
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit("create_tutorial", {"name": "GroupTest", "group_size": group_size}, namespace="/staff")
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")

    students = []
    student_uuids = []

    def random_gpa(level):
        if level == "high":
            return round(random.uniform(6.0, 7.0), 2)
        elif level == "mid":
            return round(random.uniform(4.5, 5.99), 2)
        elif level == "low":
            return round(random.uniform(3.5, 4.49), 2)


    def random_goal_gpa(current):
        return round(min(7.0, current + random.uniform(0.3, 1.0)), 2)


    def random_availability(level):
        days = ["MON", "TUE", "WED", "THU", "FRI"]
        times = ["M", "A", "N"]  # Morning, Afternoon, Night

        # Generate all possible slots
        all_slots = [d + t for d in days for t in times]

        if level == "high":
            return random.sample(all_slots, 8)
        elif level == "mid":
            return random.sample(all_slots, 4)
        elif level == "low":
            return random.sample(all_slots, 1)


    def random_student_profile():
        profiles = [
            ("HighGPA_LowAvail", "high", "low"),
            ("HighGPA_MidAvail", "high", "mid"),
            ("HighGPA_HighAvail", "high", "high"),
            ("MidGPA_LowAvail", "mid", "low"),
            ("MidGPA_MidAvail", "mid", "mid"),
            ("LowGPA_LowAvail", "low", "low"),
            ("LowGPA_HighAvail", "low", "high"),
        ]

        type_name, gpa_level, avail_level = random.choice(profiles)

        current = random_gpa(gpa_level)
        goal = random_goal_gpa(current)
        availability = random_availability(avail_level)

        return type_name, current, goal, availability

    for i in range(num_students):

        type_name, current_gpa, goal_gpa, availability = random_student_profile()

        student_client = app.test_client()

        set_session(
            student_client,
            name=f"{type_name}_CurrentGPA_{current_gpa}",
            currentGPA=current_gpa,
            goalGPA=goal_gpa,
            availability=availability
        )

        student_sio = socketio_client(test_client=student_client, disconnect=False)

        response = get_last_received(student_sio, name="session")
        student_uuid = response.get("uuid")
        student_uuids.append(student_uuid)

        student_sio.emit("join_tutorial", {"code": code})
        time.sleep(0.1)

        students.append(student_sio)

    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)
    assert len(tutorial["students"]) == num_students

    staff_sio.emit("start_grouping", namespace="/staff")
    time.sleep(0.5)

    assert tutorial["state"] == "groups"
    assert len(tutorial["groups"]) == len(expected_sizes)

    group_sizes = sorted([len(members) for members in tutorial["groups"].values()])
    assert group_sizes == expected_sizes

    for group_id, members in tutorial["groups"].items():
        member_names = [tutorial["students"][uid]["name"] for uid in members]
        logger.info(f"Group {group_id} assignments: {member_names}")

    for student_uuid in student_uuids:
        assert tutorial["students"][student_uuid]["group"] is not None


    assert tutorial["state"] == "groups"
    assert len(tutorial["groups"]) > 0
    for uid in student_uuids:
        assert tutorial["students"][uid]["group"] is not None

    first_groups = {
        gid: set(members)
        for gid, members in tutorial["groups"].items()
    }

    save_groups_txt("groups.txt", first_groups, tutorial["students"], round_num=1)

    staff_sio.emit("reset_lobby", namespace="/staff")
    time.sleep(0.5)

    assert tutorial["state"] == "lobby"
    assert tutorial["groups"] == {}
    assert tutorial["questions"] == []
    for uid in student_uuids:
        assert tutorial["students"][uid]["group"] is None

    staff_sio.emit("start_grouping", namespace="/staff")
    time.sleep(1)
    second_groups = {
        gid: set(members)
        for gid, members in tutorial["groups"].items()
    }
    save_groups_txt("groups.txt", second_groups, tutorial["students"], round_num=2)
    

    staff_sio.emit("reset_lobby", namespace="/staff")
    time.sleep(0.5)

    assert tutorial["state"] == "lobby"
    assert tutorial["groups"] == {}
    assert tutorial["questions"] == []
    for uid in student_uuids:
        assert tutorial["students"][uid]["group"] is None

    staff_sio.emit("start_grouping", namespace="/staff")
    time.sleep(1)
    third_groups = {
        gid: set(members)
        for gid, members in tutorial["groups"].items()
    }
    save_groups_txt("groups.txt", third_groups, tutorial["students"], round_num=3)
    

    staff_sio.disconnect(namespace="/staff")
    for sio in students:
        sio.disconnect()

def save_groups_txt(filename, groups, students, round_num):
    """
    Save groups to a text file with round number clearly indicated.
    
    :param filename: str, the file to write
    :param groups: dict, tutorial["groups"]
    :param students: dict, tutorial["students"]
    :param round_num: int, which round this is
    """
    with open(filename, "a") as f:
        f.write(f"--- Grouping Round {round_num} ---\n\n")
        for group_id, members in groups.items():
            member_names = [students[uid]["name"] for uid in members]
            f.write(f"Group {group_id}: {', '.join(member_names)}\n")
        f.write("\n")  # extra line at the end for readability


def test_reset_lobby(app, socketio_client):
    staff_client = app.test_client()
    set_session(staff_client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(namespace="/staff", test_client=staff_client, disconnect=False)
    response = get_last_received(staff_sio, namespace="/staff")
    assert response is not None, "Staff connection timeout"
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit("create_tutorial", {"name": "ResetTest", "group_size": 2}, namespace="/staff")
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")
    assert code is not None

    students = []
    student_uuids = []

    for i in range(4):
        student_client = app.test_client()
        set_session(student_client, name=f"Student{i+1}", currentGPA=5.0, goalGPA=6.0, availability="Mon")

        student_sio = socketio_client(test_client=student_client, disconnect=False)
        response = get_last_received(student_sio, name="session")
        student_uuid = response.get("uuid")
        student_uuids.append(student_uuid)

        student_sio.emit("join_tutorial", {"code": code})
        time.sleep(0.1)
        students.append(student_sio)

    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)
    assert len(tutorial["students"]) == 4

    staff_sio.emit("start_grouping", namespace="/staff")
    time.sleep(0.5)

    assert tutorial["state"] == "groups"
    assert len(tutorial["groups"]) > 0
    for uid in student_uuids:
        assert tutorial["students"][uid]["group"] is not None

    staff_sio.emit("reset_lobby", namespace="/staff")
    time.sleep(0.5)

    assert tutorial["state"] == "lobby"
    assert tutorial["groups"] == {}
    assert tutorial["questions"] == []
    for uid in student_uuids:
        assert tutorial["students"][uid]["group"] is None

    staff_sio.disconnect(namespace="/staff")
    for sio in students:
        sio.disconnect()
