import os, tempfile

# Set before the App is imported, so that Tests never use the Local Database or Keys
database = tempfile.TemporaryDirectory()
os.environ["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database.name}/tests.sqlite"
os.environ["FLASK_SECRET_KEY"] = "test-flask-secret-key-0000000000000"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-000000000000000"
os.environ["SOCKETIO_LOGGER"] = "false"

import pytest

from app import create_app
from app.auth import auth_attempts
from app.database import db, Staff, SavedAttribute
from app.sockets.utils import tutorials, users, sessions
from app.sockets.timer import timer


@pytest.fixture(scope="session")
def server():
    return create_app()

@pytest.fixture
def app(server):
    app, _ = server
    with app.app_context():
        yield app

    for code in list(tutorials):
        timer.stop(code)
    for state in (tutorials, users, sessions, auth_attempts):
        state.clear()
    with app.app_context():
        SavedAttribute.query.delete()
        Staff.query.delete()
        db.session.commit()

@pytest.fixture
def api(app):
    return app.test_client()


class Client:
    """A connected client, which emits events and returns their acknowledgement"""
    def __init__(self, socketio, app, namespace, auth):
        self.namespace = namespace
        self.socket = socketio.test_client(app, namespace=namespace, auth=auth)
        self.events = []

    def emit(self, event, *args):
        return self.socket.emit(event, *args, namespace=self.namespace, callback=True)

    def received(self, event):
        """The payloads of an event since they were last received"""
        self.events += self.socket.get_received(self.namespace)
        matching = [e["args"][0] for e in self.events if e["name"] == event]
        self.events = [e for e in self.events if e["name"] != event]
        return matching

    def disconnect(self):
        self.socket.disconnect(namespace=self.namespace)


@pytest.fixture
def connect_staff(server, app, api):
    def connect(token=None):
        token = token or api.post("/api/staff/guest").get_json()["token"]
        client = Client(server[1], app, "/staff", {"token": token})
        client.token = token
        return client
    return connect

@pytest.fixture
def connect_student(server, app):
    def connect(code=None, student_id=None):
        client = Client(server[1], app, "/", {"uuid": student_id})
        client.id = client.received("session")[0]["uuid"]
        if code:
            client.joined = client.emit("enter_tutorial", {"code": code})
        return client
    return connect

@pytest.fixture
def staff(connect_staff):
    """A Staff Member running a Tutorial (in groups of 2)"""
    client = connect_staff()
    client.code = client.emit("create_tutorial", {"group_size": 2, "discussion_time": 5})["tutorial_code"]
    return client
