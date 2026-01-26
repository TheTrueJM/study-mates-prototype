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

def get_last_received(sio_client):
    # get_received returns this for example:
    # [{'name': 'session', 'args': [{'uuid': 'a182809c-ed95-4ebb-86ab-d08ea3ecfa08', 'abc': 'waow'}], 'namespace': '/'}, {'name': 'session', 'args': [{'uuid': 'ac9a7da9-a85a-41d8-990b-a7343caf2f87', 'abc': 'waow'}], 'namespace': '/'}]
    return sio_client.get_received()[-1]["args"][0]

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
    assert response.get("uuid", False)
    assert response.get("role", False) == "student"
    assert response.get("tutorial", False) == None
