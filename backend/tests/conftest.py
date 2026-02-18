from app import create_app, socketio

import pytest, logging, os, time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def app():
    os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def socketio_client(app):
    def _client(namespace="/", test_client=None, disconnect=True, auth=None):
        client = socketio.test_client(
            app, namespace=namespace, flask_test_client=test_client, auth=auth
        )
        if disconnect:
            client.disconnect()
        return client

    return _client


@pytest.fixture(autouse=True)
def reset_socket_state():
    from app.sockets import utils
    from app.sockets.timer import timer

    utils.users.clear()
    utils.sessions.clear()
    utils.tutorials.clear()
    utils.disconnected_students.clear()
    timer._reset()
    yield
