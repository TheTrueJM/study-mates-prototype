import pytest

from app.auth import register_staff


SETTINGS = {
    "group_size": 4, "max_groups": 6, "discussion_time": 7.5, "available_attributes": ["availability", "year", "unknown"],
    "custom_attributes": [{"label": "Role", "options": ["Frontend", "Backend"], "matching": "similar"}],
}


@pytest.fixture
def token(app, api):
    register_staff("tutor", "correct-password")
    return api.post("/api/staff/login", json={"username": "tutor", "password": "correct-password"}).get_json()["token"]

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def create(api, token, name="Wednesday Tutorial", settings=SETTINGS):
    return api.post("/api/staff/presets", json={"name": name, "settings": settings}, headers=auth(token))


def test_saving_a_preset(api, token):
    response = create(api, token)
    assert response.status_code == 201
    preset = response.get_json()["preset"]
    settings = preset["settings"]

    assert preset["name"] == "Wednesday Tutorial"
    assert (settings["group_size"], settings["max_groups"], settings["discussion_time"]) == (4, 6, 7.5)
    assert settings["available_attributes"] == ["availability", "year"]
    assert settings["custom_attributes"][0]["label"] == "Role" and settings["custom_attributes"][0]["id"].startswith("custom_")

    assert api.get("/api/staff/presets", headers=auth(token)).get_json()["presets"] == [preset]

def test_a_preset_creates_the_same_tutorial(api, token, connect_staff):
    settings = create(api, token).get_json()["preset"]["settings"]
    staff = connect_staff(token)
    assert staff.emit("create_tutorial", settings)["ok"]

def test_overriding_and_renaming_a_preset(api, token):
    preset = create(api, token).get_json()["preset"]
    response = api.put(f"/api/staff/presets/{preset['id']}", json={"settings": {**SETTINGS, "group_size": 3}}, headers=auth(token))
    assert response.status_code == 200 and response.get_json()["preset"]["settings"]["group_size"] == 3

    renamed = api.put(f"/api/staff/presets/{preset['id']}", json={"name": "Thursday"}, headers=auth(token)).get_json()["preset"]
    assert renamed["name"] == "Thursday" and renamed["settings"]["group_size"] == 3

def test_preset_names_are_unique(api, token):
    first = create(api, token).get_json()["preset"]
    response = create(api, token, name="  wednesday   tutorial ")
    assert response.status_code == 409 and response.get_json()["preset_id"] == first["id"]

    other = create(api, token, name="Other").get_json()["preset"]
    assert api.put(f"/api/staff/presets/{other['id']}", json={"name": "Wednesday Tutorial"}, headers=auth(token)).status_code == 409
    assert api.put(f"/api/staff/presets/{first['id']}", json={"name": "Wednesday Tutorial"}, headers=auth(token)).status_code == 200

@pytest.mark.parametrize("name, settings", [
    ("", SETTINGS), ("x" * 51, SETTINGS), (None, SETTINGS), ("Fine", {**SETTINGS, "group_size": 1}),
    ("Fine", {**SETTINGS, "discussion_time": 0}), ("Fine", {**SETTINGS, "custom_attributes": [{"label": "Bad"}]}), ("Fine", "settings"),
])
def test_invalid_presets(api, token, name, settings):
    assert create(api, token, name=name, settings=settings).status_code == 400

def test_deleting_a_preset(api, token):
    preset = create(api, token).get_json()["preset"]
    assert api.delete(f"/api/staff/presets/{preset['id']}", headers=auth(token)).status_code == 200
    assert api.get("/api/staff/presets", headers=auth(token)).get_json()["presets"] == []
    assert api.delete(f"/api/staff/presets/{preset['id']}", headers=auth(token)).status_code == 404

def test_presets_are_private_to_accounts(api, token):
    preset = create(api, token).get_json()["preset"]
    guest = api.post("/api/staff/guest").get_json()["token"]
    assert api.get("/api/staff/presets", headers=auth(guest)).status_code == 403

    register_staff("other", "correct-password")
    other = api.post("/api/staff/login", json={"username": "other", "password": "correct-password"}).get_json()["token"]
    assert api.get("/api/staff/presets", headers=auth(other)).get_json()["presets"] == []
    assert api.put(f"/api/staff/presets/{preset['id']}", json={"name": "Mine"}, headers=auth(other)).status_code == 404

def test_preset_limit(api, token, monkeypatch):
    monkeypatch.setattr("app.routes.saved.MAX_PRESETS", 1)
    assert create(api, token).status_code == 201
    assert create(api, token, name="Another").status_code == 400
