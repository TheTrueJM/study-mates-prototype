# ORIGINAL TEST_STUDENT_SOCKETIO.py FILE
from app import create_app, socketio

import pytest, logging, os, time
from pudb import set_trace

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_session(client, **kwargs):
   with client.session_transaction() as s:
       for k,v in kwargs.items():
           s[k] = v

def get_session(client):
   with client.flask_test_client.session_transaction() as s:
       return s

def get_last_received(sio_client, timeout=5, namespace="/", name=None, all=False):
    # get_received returns this for example:
    # [{'name': 'session', 'args': [{'uuid': 'a182809c-ed95-4ebb-86ab-d08ea3ecfa08', 'abc': 'waow'}], 'namespace': '/'}, {'name': 'session', 'args': [{'uuid': 'ac9a7da9-a85a-41d8-990b-a7343caf2f87', 'abc': 'waow'}], 'namespace': '/'}]

    deadline = time.time() + timeout

    while (
        len(r := sio_client.get_received(namespace)) == 0
        or (
            name is not None
            and not (
                match := next(
                    (m for m in reversed(r) if m["name"] == name),
                    None,
                )
            )
        )
    ):
        logger.info(r)
        if time.time() > deadline:
            return None
        time.sleep(0.1)

    if all:
        return r
    elif name is None:
        return r.pop()["args"][0]

    return match["args"][0]

@pytest.fixture
def app():
   os.environ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
   app = create_app()
   app.config['TESTING'] = True
   return app

@pytest.fixture
def client(app):
   return app.test_client()

@pytest.fixture
def socketio_client(app):
   def _client(namespace="/", test_client=None, disconnect=True):
       client = socketio.test_client(app, namespace=namespace, flask_test_client=test_client)
       if disconnect:
           client.disconnect()
       return client

   return _client

@pytest.fixture(autouse=True)
def reset_socket_state():
    from app.sockets import utils
    utils.users.clear()
    utils.sessions.clear()
    utils.tutorials.clear()
    yield

def test_no_uuid(client, socketio_client):
    sio = socketio_client(test_client=client, disconnect=False)
    assert sio.is_connected()

    response = get_last_received(sio)

    logger.info(response)

    assert response.get("uuid", False)
    assert response.get("role", False) == "student"
    assert response.get("tutorial", False) == None

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

    from app.sockets import utils
    utils.users[uuid]["role"] = "staff"

    sio.emit("create_tutorial",
        {
            "name": "CAB202",
            "group_size": 2
        },
        namespace=namespace
    )

    time.sleep(0.5)

    # after create_tutorial()

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


def test_staff_creates_student_joins(app, client, socketio_client):
    from app.sockets import utils

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
    response = get_last_received(student_sio)
    assert response is not None, "Student connection timeout"
    student_uuid = response.get("uuid")

    student_sio.emit("join_tutorial", {"code": code})
    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)
    assert student_uuid in tutorial["students"]
    assert tutorial["students"][student_uuid]["name"] == "Student1"
    assert tutorial["students"][student_uuid]["currentGPA"] == 5.0

    staff_sio.disconnect(namespace="/staff")
    student_sio.disconnect()


def test_five_students_grouping(app, client, socketio_client):
    # note: this only verifies group slicing and doesn't verify
    # based on student attributes (yet)

    from app.sockets import utils

    staff_client = app.test_client()
    set_session(staff_client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(namespace="/staff", test_client=staff_client, disconnect=False)
    response = get_last_received(staff_sio, namespace="/staff")
    assert response is not None, "Staff connection timeout"
    staff_uuid = response.get("uuid")
    utils.users[staff_uuid]["role"] = "staff"

    staff_sio.emit("create_tutorial", {"name": "GroupTest", "group_size": 3}, namespace="/staff")
    time.sleep(0.5)
    code = utils.users[staff_uuid].get("tutorial")

    students = []
    student_uuids = []

    for i in range(5):
        student_client = app.test_client()
        set_session(student_client, name=f"Student{i+1}", currentGPA=5.0, goalGPA=6.0, availability="Mon")

        student_sio = socketio_client(test_client=student_client, disconnect=False)
        response = get_last_received(student_sio)
        student_uuid = response.get("uuid")
        student_uuids.append(student_uuid)

        student_sio.emit("join_tutorial", {"code": code})
        time.sleep(0.1)
        students.append(student_sio)

    time.sleep(0.5)

    tutorial = utils.tutorials.get(code)
    assert len(tutorial["students"]) == 5

    staff_sio.emit("start_grouping", namespace="/staff")
    time.sleep(0.5)

    assert tutorial["state"] == "groups"
    assert len(tutorial["groups"]) == 2

    group_sizes = sorted([len(members) for members in tutorial["groups"].values()])
    assert group_sizes == [2, 3]

    for group_id, members in tutorial["groups"].items():
        member_names = [tutorial["students"][uid]["name"] for uid in members]
        from pudb import set_trace
        set_trace()
        logger.info(f"Group {group_id} assignments: {member_names}")

    for student_uuid in student_uuids:
        assert tutorial["students"][student_uuid]["group"] is not None

    staff_sio.disconnect(namespace="/staff")
    for sio in students:
        sio.disconnect()


def test_student_auto_join(app, client, socketio_client):
    from app.sockets import utils

    staff_client = app.test_client()
    set_session(staff_client, name="Staff", currentGPA=0.0, goalGPA=0.0, availability="")

    staff_sio = socketio_client(namespace="/staff", test_client=staff_client, disconnect=False)
    response = get_last_received(staff_sio, namespace="/staff")
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

    response = get_last_received(student_sio, name="student_update", all=True)
    logger.info(response)
    tutorial_code = response[-1]["args"][0].get("tutorial_code", None)
    student_uuid = response[-2]["args"][0].get("uuid", None)
    assert tutorial_code == code

    tutorial = utils.tutorials.get(code)
    assert student_uuid in tutorial["students"]
    assert tutorial["students"][student_uuid]["name"] == "AutoStudent"

    staff_sio.disconnect(namespace="/staff")
    student_sio.disconnect()
