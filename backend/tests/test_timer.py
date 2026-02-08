import pytest
import time
import logging

from app.sockets import utils
from app import timer_threads
from tests.helpers import set_session, get_last_received

logger = logging.getLogger(__name__)

def test_create_tutorial_with_timer(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="test", currentGPA=0.0, goalGPA=6.7, availability="")
    sio = socketio_client(namespace=namespace, test_client=client, disconnect=False)

    response = get_last_received(sio, namespace=namespace)
    assert response is not None, "Timeout"
    uuid = response.get("uuid", False)
    assert uuid

    utils.users[uuid]["role"] = "staff"

    sio.emit("create_tutorial",
        {
            "name": "TimerTest",
            "group_size": 2,
            "discussion_time": 15
        },
        namespace=namespace
    )

    time.sleep(0.5)

    code = utils.users[uuid].get("tutorial", None)
    assert code is not None

    tutorial = utils.tutorials.get(code)
    assert tutorial is not None
    assert tutorial["name"] == "TimerTest"
    assert tutorial["group_size"] == 2
    assert tutorial["timer"]["duration"] == 900
    assert tutorial["timer"]["remaining"] == 900
    assert tutorial["timer"]["running"] == False

    sio.disconnect(namespace=namespace)

def test_create_tutorial_default_timer(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="test", currentGPA=0.0, goalGPA=6.7, availability="")
    sio = socketio_client(namespace=namespace, test_client=client, disconnect=False)

    response = get_last_received(sio, namespace=namespace)
    uuid = response.get("uuid")
    utils.users[uuid]["role"] = "staff"

    sio.emit("create_tutorial", {"name": "DefaultTimer", "group_size": 2}, namespace=namespace)
    time.sleep(0.5)

    code = utils.users[uuid].get("tutorial")
    tutorial = utils.tutorials.get(code)
    assert tutorial["timer"]["duration"] == 600
    assert tutorial["timer"]["remaining"] == 600
    assert tutorial["timer"]["running"] == False

    sio.disconnect(namespace=namespace)

def test_start_stop_timer(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="test", currentGPA=0.0, goalGPA=6.7, availability="")
    sio = socketio_client(namespace=namespace, test_client=client, disconnect=False)

    response = get_last_received(sio, namespace=namespace)
    uuid = response.get("uuid")
    utils.users[uuid]["role"] = "staff"

    sio.emit("create_tutorial", {"name": "StopStartTest", "group_size": 2}, namespace=namespace)
    time.sleep(0.5)

    code = utils.users[uuid].get("tutorial")
    tutorial = utils.tutorials.get(code)

    sio.emit("start_discussion", namespace=namespace)
    time.sleep(0.5)

    assert tutorial["timer"]["running"] == True

    sio.emit("stop_timer", namespace=namespace)
    time.sleep(0.5)

    assert tutorial["timer"]["running"] == False

    sio.emit("start_timer", namespace=namespace)
    time.sleep(0.5)

    assert tutorial["timer"]["running"] == True

    sio.emit("stop_timer", namespace=namespace)
    time.sleep(0.5)

    sio.disconnect(namespace=namespace)

def test_edit_timer(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="test", currentGPA=0.0, goalGPA=6.7, availability="")
    sio = socketio_client(namespace=namespace, test_client=client, disconnect=False)

    response = get_last_received(sio, namespace=namespace)
    uuid = response.get("uuid")
    utils.users[uuid]["role"] = "staff"

    sio.emit("create_tutorial", {"name": "EditTest", "group_size": 2, "discussion_time": 5}, namespace=namespace)
    time.sleep(0.5)

    code = utils.users[uuid].get("tutorial")
    tutorial = utils.tutorials.get(code)
    assert tutorial["timer"]["duration"] == 300
    assert tutorial["timer"]["remaining"] == 300

    sio.emit("start_discussion", namespace=namespace)
    time.sleep(0.5)

    sio.emit("edit_timer", {"time": 20}, namespace=namespace)
    time.sleep(0.5)

    assert tutorial["timer"]["duration"] == 1200
    assert tutorial["timer"]["remaining"] == 1200

    sio.emit("stop_timer", namespace=namespace)
    time.sleep(0.5)

    sio.disconnect(namespace=namespace)

def test_timer_included_in_update(app, socketio_client):
    staff_client = app.test_client()
    set_session(staff_client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(namespace="/staff", test_client=staff_client, disconnect=False)
    response = get_last_received(staff_sio, namespace="/staff")
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit("create_tutorial", {"name": "UpdateTest", "group_size": 2, "discussion_time": 10}, namespace="/staff")
    time.sleep(0.5)

    code = utils.users[staff_uuid].get("tutorial")

    student_client = app.test_client()
    set_session(student_client, name="Student", currentGPA=5.0, goalGPA=6.0, availability="Mon")

    student_sio = socketio_client(test_client=student_client, disconnect=False)
    response = get_last_received(student_sio, name="session")
    student_uuid = response.get("uuid")

    student_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    staff_sio.emit("start_discussion", namespace="/staff")
    time.sleep(0.5)

    staff_response = get_last_received(staff_sio, namespace="/staff", name="tutorial_update")
    assert staff_response is not None
    assert "timer" in staff_response
    assert staff_response["timer"]["running"] == True

    student_response = get_last_received(student_sio, name="student_update")
    assert student_response is not None
    assert "timer" in student_response
    assert student_response["timer"]["running"] == True

    staff_sio.emit("stop_timer", namespace="/staff")
    time.sleep(0.5)

    staff_sio.disconnect(namespace="/staff")
    student_sio.disconnect()

def test_timer_decrements_over_time(client, socketio_client):
    namespace = "/staff"
    set_session(client, name="test", currentGPA=0.0, goalGPA=6.7, availability="")
    sio = socketio_client(namespace=namespace, test_client=client, disconnect=False)

    response = get_last_received(sio, namespace=namespace)
    uuid = response.get("uuid")
    utils.users[uuid]["role"] = "staff"

    sio.emit("create_tutorial", {"name": "DecrementTest", "group_size": 2, "discussion_time": 5}, namespace=namespace)
    time.sleep(0.5)

    code = utils.users[uuid].get("tutorial")
    tutorial = utils.tutorials.get(code)
    initial_remaining = tutorial["timer"]["remaining"]
    assert initial_remaining == 300

    sio.emit("start_discussion", namespace=namespace)
    time.sleep(0.5)
    assert tutorial["timer"]["running"] == True

    time.sleep(15)

    remaining_after_15 = tutorial["timer"]["remaining"]
    assert remaining_after_15 < initial_remaining, f"Timer did not decrease: {remaining_after_15} vs {initial_remaining}"
    assert remaining_after_15 >= 0, f"Timer went negative: {remaining_after_15}"

    sio.emit("stop_timer", namespace=namespace)
    time.sleep(0.5)
    assert tutorial["timer"]["running"] == False

    remaining_after_stop = tutorial["timer"]["remaining"]
    time.sleep(5)

    assert tutorial["timer"]["remaining"] == remaining_after_stop, "Timer continued after stopping"

    sio.disconnect(namespace=namespace)
