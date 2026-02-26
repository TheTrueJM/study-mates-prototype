import pytest
import time

from app.sockets import utils
from tests.helpers import set_session, get_last_received


def test_late_joiner_during_groups_state(app, socketio_client):
    """Test that a student joining late during 'groups' state is auto-assigned to best group."""
    staff_client = app.test_client()
    set_session(
        staff_client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability=""
    )

    staff_sio = socketio_client(
        namespace="/staff", test_client=staff_client, disconnect=False
    )
    response = get_last_received(staff_sio, namespace="/staff")
    assert response is not None
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit(
        "create_tutorial",
        {"name": "LateJoinerTest", "group_size": 3},
        namespace="/staff",
    )
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")

    students = []
    student_uuids = []

    for i in range(6):
        student_client = app.test_client()
        set_session(
            student_client,
            name=f"Student{i + 1}",
            currentGPA=5.0,
            goalGPA=6.0,
            availability="Mon",
        )
        student_sio = socketio_client(test_client=student_client, disconnect=False)
        response = get_last_received(student_sio, name="session")
        uuid = response.get("uuid")
        student_uuids.append(uuid)

        student_sio.emit("join_tutorial", {"code": code})
        time.sleep(0.1)
        students.append(student_sio)

    time.sleep(0.5)

    staff_sio.emit("start_grouping", namespace="/staff")
    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)
    assert tutorial["state"] == "groups"

    existing_groups_before = {
        gid: list(members) for gid, members in tutorial["groups"].items()
    }
    original_students = set(student_uuids)

    time.sleep(0.5)
    new_student_client = app.test_client()
    set_session(
        new_student_client,
        name="LateJoiner",
        currentGPA=4.8,
        goalGPA=6.2,
        availability="Mon,Tue",
    )
    new_sio = socketio_client(test_client=new_student_client, disconnect=False)

    response = get_last_received(new_sio, name="session")
    late_uuid = response.get("uuid")
    assert late_uuid

    time.sleep(0.5)
    new_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)

    # Late joiner should be in students with a group assigned (not None)
    assert late_uuid in tutorial["students"]
    assert tutorial["students"][late_uuid]["group"] is not None

    # Group exists and contains the late joiner
    group_id = tutorial["students"][late_uuid]["group"]
    assert group_id in tutorial["groups"]
    assert late_uuid in tutorial["groups"][group_id]

    staff_sio.disconnect(namespace="/staff")
    for sio in students:
        sio.disconnect()
    new_sio.disconnect()


def test_late_joiner_joins_existing_group_not_created_new(app, socketio_client):
    """Test that late joiner joins an existing group rather than creating a new one."""
    staff_client = app.test_client()
    set_session(
        staff_client, name="Staff", currentGPA=0.0, goalGPO=0.0, availability=""
    )

    staff_sio = socketio_client(
        namespace="/staff", test_client=staff_client, disconnect=False
    )
    response = get_last_received(staff_sio, namespace="/staff")
    assert response is not None
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit(
        "create_tutorial",
        {"name": "SingleGroupTest", "group_size": 5},
        namespace="/staff",
    )
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")

    student_client = app.test_client()
    set_session(
        student_client,
        name="ExistingStudent",
        currentGPA=5.0,
        goalGPA=6.0,
        availability="Mon",
    )
    sio = socketio_client(test_client=student_client, disconnect=False)

    response = get_last_received(sio, name="session")
    existing_uuid = response.get("uuid")

    sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    staff_sio.emit("start_grouping", namespace="/staff")
    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)

    assert tutorial["state"] == "groups"
    initial_groups_count = len(tutorial["groups"])

    time.sleep(0.5)
    late_client = app.test_client()
    set_session(
        late_client, name="LateJoiner", currentGPA=4.9, goalGPA=6.1, availability="Mon"
    )
    late_sio = socketio_client(test_client=late_client, disconnect=False)

    response = get_last_received(late_sio, name="session")
    late_uuid = response.get("uuid")

    time.sleep(0.5)
    late_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)

    # Group count should not increase (no new group created)
    assert len(tutorial["groups"]) == initial_groups_count

    # Late joiner assigned to one of the existing groups
    late_group_id = tutorial["students"][late_uuid]["group"]
    assert late_group_id in tutorial["groups"]


def test_late_joiner_auto_assigned_to_most_compatible(app, socketio_client):
    """Test that late joiner is assigned to the most compatible group based on GPA/availability."""
    staff_client = app.test_client()
    set_session(
        staff_client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability=""
    )

    staff_sio = socketio_client(
        namespace="/staff", test_client=staff_client, disconnect=False
    )
    response = get_last_received(staff_sio, namespace="/staff")
    assert response is not None
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    # Create tutorial with smaller group size to ensure 2 groups
    staff_sio.emit(
        "create_tutorial",
        {"name": "CompatibilityTest", "group_size": 2},
        namespace="/staff",
    )
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")

    # Create 4 students - should form 2 groups of 2
    student1_client = app.test_client()
    set_session(
        student1_client,
        name="SimilarGPA",
        currentGPA=5.0,
        goalGPA=6.0,
        availability="Mon,Tue,Wed",
    )
    sio1 = socketio_client(test_client=student1_client, disconnect=False)

    response = get_last_received(sio1, name="session")
    uuid1 = response.get("uuid")

    student2_client = app.test_client()
    set_session(
        student2_client,
        name="DifferentGPA",
        currentGPA=3.5,
        goalGPA=4.0,
        availability="Thu,Fri",
    )
    sio2 = socketio_client(test_client=student2_client, disconnect=False)

    response = get_last_received(sio2, name="session")
    uuid2 = response.get("uuid")

    student3_client = app.test_client()
    set_session(
        student3_client,
        name="SimilarTo1",
        currentGPA=5.2,
        goalGPA=6.1,
        availability="Mon,Tue",
    )
    sio3 = socketio_client(test_client=student3_client, disconnect=False)

    response = get_last_received(sio3, name="session")
    uuid3 = response.get("uuid")

    student4_client = app.test_client()
    set_session(
        student4_client,
        name="DifferentToAll",
        currentGPA=3.6,
        goalGPA=4.2,
        availability="Fri,Sat",
    )
    sio4 = socketio_client(test_client=student4_client, disconnect=False)

    response = get_last_received(sio4, name="session")
    uuid4 = response.get("uuid")

    # All students join tutorial
    for sio in [sio1, sio2, sio3, sio4]:
        sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    staff_sio.emit("start_grouping", namespace="/staff")
    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)

    # uuid1 and uuid2 should be in different groups (they have very different profiles)
    group1_id = tutorial["students"][uuid1]["group"]
    group2_id = tutorial["students"][uuid2]["group"]

    assert group1_id != group2_id

    time.sleep(0.5)
    late_client = app.test_client()
    # Late joiner has GPA and availability similar to Student 1 (uuid1) - should go to same group as uuid1
    set_session(
        late_client,
        name="LateJoiner",
        currentGPA=4.9,
        goalGPA=5.8,
        availability="Mon,Tue,Wed",
    )
    late_sio = socketio_client(test_client=late_client, disconnect=False)

    response = get_last_received(late_sio, name="session")
    late_uuid = response.get("uuid")

    time.sleep(0.5)
    late_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)

    # Late joiner should be assigned to same group as uuid1 (similar profile: high GPA, Mon/Tue/Wed availability)
    assert tutorial["students"][late_uuid]["group"] == group1_id

    staff_sio.disconnect(namespace="/staff")
    sio1.disconnect()
    sio2.disconnect()
    sio3.disconnect()
    sio4.disconnect()
    late_sio.disconnect()


def test_late_joiner_before_grouping_no_autoassign(app, socketio_client):
    """Test that joining during lobby state does NOT auto-assign groups."""
    staff_client = app.test_client()
    set_session(
        staff_client, name="Staff", currentGPA=0.0, goalGPO=0.0, availability=""
    )

    staff_sio = socketio_client(
        namespace="/staff", test_client=staff_client, disconnect=False
    )
    response = get_last_received(staff_sio, namespace="/staff")
    assert response is not None
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit(
        "create_tutorial",
        {"name": "LobbyNoAutoTest", "group_size": 2},
        namespace="/staff",
    )
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")

    existing_client = app.test_client()
    set_session(
        existing_client,
        name="EarlyStudent",
        currentGPA=5.0,
        goalGPA=6.0,
        availability="Mon",
    )
    sio_existing = socketio_client(test_client=existing_client, disconnect=False)

    response = get_last_received(sio_existing, name="session")
    early_uuid = response.get("uuid")

    sio_existing.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    late_client = app.test_client()
    set_session(
        late_client,
        name="LateJoinerBeforeGrouping",
        currentGPA=4.8,
        goalGPA=6.2,
        availability="Mon",
    )
    sio_late = socketio_client(test_client=late_client, disconnect=False)

    response = get_last_received(sio_late, name="session")
    late_uuid = response.get("uuid")

    time.sleep(0.5)
    sio_late.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)

    # Both students should have no group (None) in lobby state
    assert tutorial["students"][early_uuid]["group"] is None
    assert tutorial["students"][late_uuid]["group"] is None

    staff_sio.disconnect(namespace="/staff")
    sio_existing.disconnect()
    sio_late.disconnect()
