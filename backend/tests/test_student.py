import pytest
import time
import logging

from app.sockets import utils
from tests.helpers import set_session, get_last_received

logger = logging.getLogger(__name__)

def test_no_uuid(client, socketio_client):
    sio = socketio_client(test_client=client, disconnect=False)
    assert sio.is_connected()

    response = get_last_received(sio, name="session")

    logger.info(response)

    assert response.get("uuid", False)
    assert response.get("role", False) == "student"
    assert response.get("tutorial", False) == None

def test_student_auto_join(app, client, socketio_client):
    staff_client = app.test_client()
    set_session(staff_client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(namespace="/staff", test_client=staff_client, disconnect=False)
    response = get_last_received(staff_sio, name="session", namespace="/staff")
    assert response.get("uuid", False)
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit("create_tutorial", {"name": "AutoJoinTest", "group_size": 2}, namespace="/staff")
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")

    student_client = app.test_client()
    set_session(student_client,
                name="AutoStudent",
                currentGPA=5.0,
                goalGPA=6.0,
                availability="Mon",
                tutorial_code=code)

    student_sio = socketio_client(test_client=student_client, disconnect=False)

    response = get_last_received(student_sio, all=True)

    # Filter events by name to avoid fragile indexing
    session_event = next((r for r in response if r["name"] == "session"), None)
    update_event = next((r for r in response if r["name"] == "student_update"), None)

    assert session_event is not None
    assert update_event is not None

    student_uuid = session_event["args"][0].get("uuid")
    tutorial_code = update_event["args"][0].get("tutorial_code")

    assert tutorial_code == code

    tutorial = utils.tutorials.get(code)
    assert student_uuid in tutorial["students"]
    assert tutorial["students"][student_uuid]["name"] == "AutoStudent"

    staff_sio.disconnect(namespace="/staff")
    student_sio.disconnect()

def test_join_invalid_code(app, client, socketio_client):
    student_client = app.test_client()
    set_session(student_client, name="BadJoiner", currentGPA=1.0, goalGPA=2.0, availability="Tue")

    student_sio = socketio_client(test_client=student_client, disconnect=False)
    response = get_last_received(student_sio, name="session")
    student_uuid = response.get("uuid")
    assert student_uuid

    student_sio.emit("join_tutorial", {"code": "FAKECODE"})

    error_response = get_last_received(student_sio, name="error")
    assert error_response.get("message", False) == "Tutorial not found"

    assert student_uuid not in utils.users or utils.users[student_uuid].get("tutorial") is None

    found = False
    for t in utils.tutorials.values():
        if student_uuid in t["students"]:
            found = True
            break

    assert found is False

@pytest.mark.skip("Not implemented yet")
def test_student_unauthorised_staff_access(app, socketio_client):
    namespace = "/staff"

    student_client = app.test_client()
    set_session(student_client, name="NotStaff", currentGPA=0.0, goalGPA=0.0, availability="")

    student_sio = socketio_client(namespace=namespace, test_client=student_client, disconnect=False)

    response = get_last_received(student_sio, namespace=namespace)

    from pudb import set_trace; set_trace()

    assert response.get("uuid", False)
    uuid = response.get("uuid")
    utils.users[uuid]["role"] = "student"

    time.sleep(0.5)

    assert not student_sio.is_connected(namespace)
