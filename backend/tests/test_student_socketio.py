from app import create_app, socketio

import pytest
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def set_session(client, **kwargs):
    with client.session_transaction() as s:
        for k,v in kwargs.items():
            s[k] = v

def get_session(client):
    with client.flask_test_client.session_transaction() as s:
        return s

def get_last_received(sio_client, timeout=5):
    # get_received returns this for example:
    # [{'name': 'session', 'args': [{'uuid': 'a182809c-ed95-4ebb-86ab-d08ea3ecfa08', 'abc': 'waow'}], 'namespace': '/'}, {'name': 'session', 'args': [{'uuid': 'ac9a7da9-a85a-41d8-990b-a7343caf2f87', 'abc': 'waow'}], 'namespace': '/'}]

    import time
    deadline = time.time() + timeout

    while len(r := sio_client.get_received()) == 0:
        logger.info(r)
        if time.time() > deadline:
            return None
        time.sleep(0.1)

    return r.pop()["args"][0]

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
    def _client(test_client=None, disconnect=True):
        client = socketio.test_client(app, flask_test_client=test_client)
        if disconnect:
            client.disconnect()
        return client

    return _client

def test_no_uuid(client, socketio_client):
    set_session(client, abc="not student")
    sio = socketio_client(test_client=client, disconnect=False)
    assert sio.is_connected()

    response = get_last_received(sio)

    logger.info(response)

    assert response.get("uuid", False)
    assert response.get("role", False) == "student"
    assert response.get("tutorial", False) == None

def test_create_tutorial(client, socketio_client):
    set_session(
        client,
        name="test",
        currentGPA=0.0,
        goalGPA=6.7,
        availability=""
    )
    sio = socketio_client(test_client=client, disconnect=False)
    logger.info(f"Connection: {sio.is_connected()}")

    assert sio.is_connected()
    response = get_last_received(sio)
    assert response is not None, "Timeout"
    uuid = response.get("uuid", False)
    assert uuid

    from app.sockets import server
    server.users[uuid]["role"] = "staff"

    sio.emit("create_tutorial",
        {
            "name": "CAB202",
            "group_size": 2
        }
    )

    # after create_tutorial()

    code = server.users[uuid].get("tutorial", None)
    assert code

    tutorial = server.tutorials.get(code)
    assert tutorial is not None

    assert tutorial["name"] == "CAB202"
    assert tutorial["group_size"] == 2
    assert tutorial["staff"] == uuid
    assert tutorial["state"] == "lobby"
    assert tutorial["students"] == dict()
    assert tutorial["groups"] == dict()
    assert tutorial["questions"] == list()

    response = get_last_received(sio)
    assert response is not None, "Timeout"
    assert response.get("code", None) == code
