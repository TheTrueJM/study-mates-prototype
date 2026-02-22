import pytest
import time
import logging

from app.sockets import utils
from tests.helpers import set_session, get_last_received

logger = logging.getLogger(__name__)


def test_delete_tutorial(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(
        namespace=namespace, test_client=client, disconnect=False
    )
    response = get_last_received(staff_sio, namespace=namespace)
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit(
        "create_tutorial", {"name": "DeleteTest", "group_size": 2}, namespace=namespace
    )
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")
    assert code is not None

    student_client = client.application.test_client()
    set_session(
        student_client, name="Student1", currentGPA=5.0, goalGPA=6.0, availability="Mon"
    )
    student_sio = socketio_client(test_client=student_client, disconnect=False)

    response = get_last_received(student_sio, name="session")
    student_uuid = response.get("uuid")

    student_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    assert student_uuid in utils.tutorials[code]["students"]

    staff_sio.emit("delete_tutorial", namespace=namespace)
    time.sleep(0.5)

    assert code not in utils.tutorials
    assert utils.users[student_uuid].get("tutorial") is None
    assert utils.users[staff_uuid].get("tutorial") is None

    received = get_last_received(student_sio, all=True)
    event_names = [m["name"] for m in received]
    assert "tutorial_ended" in event_names
    assert "session_cleared" in event_names

    tutorial_deleted = get_last_received(
        staff_sio, name="tutorial_deleted", namespace=namespace
    )
    assert tutorial_deleted is not None

    staff_sio.disconnect(namespace=namespace)
    student_sio.disconnect()


def test_staff_disconnect_grace_period(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(
        namespace=namespace, test_client=client, disconnect=False
    )
    response = get_last_received(staff_sio, namespace=namespace)
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit(
        "create_tutorial", {"name": "GraceTest", "group_size": 2}, namespace=namespace
    )
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")
    assert code is not None

    student_client = client.application.test_client()
    set_session(
        student_client, name="Student1", currentGPA=5.0, goalGPA=6.0, availability="Mon"
    )
    student_sio = socketio_client(test_client=student_client, disconnect=False)

    response = get_last_received(student_sio, name="session")
    student_uuid = response.get("uuid")

    student_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    staff_sio.disconnect(namespace=namespace)
    time.sleep(0.5)

    assert code in utils.tutorials
    assert code in utils.disconnected_staff
    assert utils.disconnected_staff[code] is not None

    utils._cleanup_stale_users(code)

    assert code in utils.tutorials

    utils.disconnected_staff[code] = (
        time.time() - utils.STAFF_RECONNECT_GRACE_PERIOD - 1
    )
    with client.application.test_request_context():
        utils._cleanup_stale_users(code)

    assert code not in utils.tutorials
    assert utils.users[student_uuid].get("tutorial") is None

    student_sio.disconnect()


def test_staff_reconnect_within_grace_period(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(
        namespace=namespace, test_client=client, disconnect=False
    )
    response = get_last_received(staff_sio, namespace=namespace)
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit(
        "create_tutorial",
        {"name": "ReconnectTest", "group_size": 2},
        namespace=namespace,
    )
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")
    assert code is not None

    staff_sio.disconnect(namespace=namespace)
    time.sleep(0.5)

    assert code in utils.disconnected_staff

    staff_client2 = client.application.test_client()
    set_session(
        staff_client2, name="Staff", currentGPA=0.0, goalGPA=0.0, availability=""
    )

    staff_sio2 = socketio_client(
        namespace=namespace,
        test_client=staff_client2,
        disconnect=False,
        auth={"uuid": staff_uuid},
    )
    time.sleep(0.5)

    assert code not in utils.disconnected_staff
    assert utils.users[staff_uuid].get("tutorial") == code

    staff_sio2.disconnect(namespace=namespace)


def test_reset_session(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(
        namespace=namespace, test_client=client, disconnect=False
    )
    response = get_last_received(staff_sio, namespace=namespace)
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit(
        "create_tutorial", {"name": "ResetTest", "group_size": 2}, namespace=namespace
    )
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")

    student_client = client.application.test_client()
    set_session(
        student_client, name="Student1", currentGPA=5.0, goalGPA=6.0, availability="Mon"
    )
    student_sio = socketio_client(test_client=student_client, disconnect=False)

    response = get_last_received(student_sio, name="session")
    student_uuid = response.get("uuid")

    student_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    assert student_uuid in utils.tutorials[code]["students"]

    student_sio.emit("reset_session")
    time.sleep(0.5)

    assert student_uuid not in utils.tutorials[code]["students"]
    assert utils.users[student_uuid].get("tutorial") is None

    received = get_last_received(student_sio, all=True)
    event_names = [m["name"] for m in received]
    assert "session_cleared" in event_names

    staff_sio.disconnect(namespace=namespace)
    student_sio.disconnect()


def test_session_clear_endpoint(client):
    with client.session_transaction() as s:
        s["tutorial_code"] = "ABC123"
        s["role"] = "student"

    response = client.post("/session/clear")

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Session cleared"

    with client.session_transaction() as s:
        assert "tutorial_code" not in s
        assert "role" not in s


def test_student_update_group_members_with_availability(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(
        namespace=namespace, test_client=client, disconnect=False
    )
    response = get_last_received(staff_sio, namespace=namespace)
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit(
        "create_tutorial",
        {"name": "AvailabilityTest", "group_size": 2},
        namespace=namespace,
    )
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")

    student1_client = client.application.test_client()
    set_session(
        student1_client,
        name="Student1",
        currentGPA=5.0,
        goalGPA=6.0,
        availability=["MONM", "TUEA"],
    )
    student1_sio = socketio_client(test_client=student1_client, disconnect=False)
    response = get_last_received(student1_sio, name="session")
    student1_uuid = response.get("uuid")
    student1_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.3)

    student2_client = client.application.test_client()
    set_session(
        student2_client,
        name="Student2",
        currentGPA=5.5,
        goalGPA=6.5,
        availability=["WEDN", "THUA"],
    )
    student2_sio = socketio_client(test_client=student2_client, disconnect=False)
    response = get_last_received(student2_sio, name="session")
    student2_uuid = response.get("uuid")
    student2_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    staff_sio.emit("start_grouping", namespace=namespace)
    time.sleep(0.5)

    student_update = get_last_received(student1_sio, name="student_update")

    assert student_update is not None
    assert "group_members" in student_update

    group_members = student_update["group_members"]
    assert group_members is not None
    assert isinstance(group_members, list)

    for member in group_members:
        assert "name" in member
        assert "availability" in member
        assert isinstance(member["availability"], list)

    staff_sio.disconnect(namespace=namespace)
    student1_sio.disconnect()
    student2_sio.disconnect()
