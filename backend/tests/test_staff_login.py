from pathlib import Path
import re, time
import gevent
import pytest

import app as app_package
from app.auth import MAX_LOGIN_ATTEMPTS, MAX_REGISTER_ATTEMPTS, MAX_PENDING_PASSWORDS, register_staff
from app.database import db, Staff


PASSWORD = "correct-password"


@pytest.fixture
def account(app):
    return register_staff("tutor", PASSWORD)

@pytest.fixture
def longest_gap():
    """Returns the longest time (in seconds) that the server has been held up for"""
    gaps = [0]

    def keep_ticking():
        while True:
            start = time.perf_counter()
            gevent.sleep(0.02)
            gaps.append(time.perf_counter() - start)

    ticker = gevent.spawn(keep_ticking)
    yield lambda: max(gaps)
    ticker.kill()

def register(api, username="tutor", password=PASSWORD):
    return api.post("/api/staff/register", json={"username": username, "password": password})

def login(api, username="tutor", password=PASSWORD):
    return api.post("/api/staff/login", json={"username": username, "password": password})


def test_login(api, account):
    response = login(api)
    assert response.status_code == 200

    headers = {"Authorization": f"Bearer {response.get_json()['token']}"}
    assert api.get("/api/staff/me", headers=headers).get_json() == {"staff_type": "account", "username": "tutor"}


@pytest.mark.parametrize("username, password", [
    ("tutor", "wrong"), ("nobody", "wrong"), ("nobody", PASSWORD), ("tutor", "a" * 80), ("nobody", "a" * 80),
    ("a" * 80, "wrong"), ("tutor", "\ud800"), ("\ud800", "wrong"), ("tutor", "\x00"),
])
def test_incorrect_logins_are_indistinguishable(api, account, username, password):
    response = login(api, username, password)
    assert response.status_code == 401
    assert response.get_json() == {"message": "Incorrect username or password"}


def test_unknown_usernames_take_as_long_as_known(api, account):
    def duration(username):
        start = time.perf_counter()
        login(api, username, "wrong")
        return time.perf_counter() - start

    known, unknown = min(duration("tutor") for _ in range(3)), min(duration("nobody") for _ in range(3))
    assert 0.5 < unknown / known < 2


def test_login_attempts_are_limited(api, account):
    for _ in range(MAX_LOGIN_ATTEMPTS):
        assert login(api, password="wrong").status_code == 401

    assert login(api).status_code == 429
    assert login(api, "nobody", "wrong").status_code == 401 # Other Usernames aren't affected

def test_successful_login_clears_attempts(api, account):
    for _ in range(MAX_LOGIN_ATTEMPTS * 2):
        assert login(api, password="wrong").status_code == 401
        assert login(api).status_code == 200


def test_many_logins_do_not_hold_up_the_server(app, account, longest_gap, monkeypatch):
    monkeypatch.setattr(db.engine.pool, "_timeout", 1) # Fail quickly if waiting for a Database Connection
    logins = [gevent.spawn(lambda i=i: login(app.test_client(), f"user{i}", "wrong").status_code) for i in range(40)]
    gevent.joinall(logins, timeout=15)

    statuses = [greenlet.value for greenlet in logins]
    assert statuses.count(401) == MAX_PENDING_PASSWORDS and statuses.count(429) == 40 - MAX_PENDING_PASSWORDS
    assert longest_gap() < 0.5


# ===== Register ===== #

def test_register_signs_in(api, connect_staff):
    response = register(api, "  New Tutor ")
    data = response.get_json()
    assert response.status_code == 201
    assert (data["staff_type"], data["username"]) == ("account", "New Tutor")

    headers = {"Authorization": f"Bearer {data['token']}"}
    assert api.get("/api/staff/me", headers=headers).get_json() == {"staff_type": "account", "username": "New Tutor"}
    assert connect_staff(data["token"]).emit("create_tutorial", {"group_size": 2})["ok"]
    assert login(api, "New Tutor").status_code == 200

def test_passwords_are_hashed(api):
    register(api)
    assert PASSWORD not in str(Staff.query.one().password_hash)

@pytest.mark.parametrize("username", ["tutor", "TUTOR", " Tutor "])
def test_taken_usernames(api, account, username):
    response = register(api, username, "another-password")
    assert response.status_code == 409 and "taken" in response.get_json()["message"]
    assert Staff.query.count() == 1
    assert login(api).status_code == 200 # Unchanged

@pytest.mark.parametrize("username, password", [
    ("ab", PASSWORD), ("a" * 51, PASSWORD), ("   ", PASSWORD), ("tu\x00tor", PASSWORD), ("tu\ntor", PASSWORD),
    ("\ud800\ud800\ud800", PASSWORD), ("tutor", "short"), ("tutor", "a" * 73), ("tutor", "\u20ac" * 25),
    ("tutor", "\ud800" * 8), ("tutor", "\x00" * 8), ("", PASSWORD), ("tutor", ""), (None, PASSWORD), ("tutor", ["a"] * 8),
])
def test_invalid_accounts(api, username, password):
    assert register(api, username, password).status_code == 400
    assert Staff.query.count() == 0

def test_invalid_register_data(api):
    assert api.post("/api/staff/register", data="invalid").status_code == 400
    assert api.post("/api/staff/register", json=["invalid"]).status_code == 400

def test_register_attempts_are_limited(api, account):
    for _ in range(MAX_REGISTER_ATTEMPTS):
        assert register(api).status_code == 409
    assert register(api, "someone-else").status_code == 429
    assert login(api).status_code == 200 # Not affected

def test_registering_the_same_username_at_once(app, longest_gap):
    requests = [gevent.spawn(lambda: register(app.test_client()).status_code) for _ in range(6)]
    gevent.joinall(requests, timeout=15)

    assert sorted(greenlet.value for greenlet in requests) == [201] + [409] * 5
    assert Staff.query.count() == 1
    assert longest_gap() < 0.5


# ===== Setup ===== #

def test_server_needs_a_key(monkeypatch):
    monkeypatch.setattr(app_package, "JWT_KEY", "")
    monkeypatch.setattr(app_package, "FLASK_KEY", "")
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        app_package.create_app()

def test_env_example_matches_the_server():
    """Every variable in .env.example is used by the server, and every variable it uses is in .env.example"""
    backend = Path(__file__).parent.parent
    example = {line.split("=")[0] for line in (backend / ".env.example").read_text().splitlines() if re.match(r"[A-Z_]+=", line)}
    code = "".join(path.read_text() for path in [backend / "main.py", *(backend / "app").rglob("*.py")])
    assert example == set(re.findall(r'getenv\("([A-Z_]+)"', code))
