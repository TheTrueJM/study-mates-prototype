import pytest

from app.auth import register_staff
from app.custom_attributes import (
    MAX_CUSTOM_ATTRIBUTES, MAX_OPTIONS, parse_custom_attribute, parse_custom_attributes, validate_custom_value
)
from app.routes.saved import MAX_SAVED_ATTRIBUTES
from app.sockets.matching import form_groups
from app.sockets.utils import tutorials


def detail(label="Role", options=("Frontend", "Backend", "Design"), **extra):
    return {"label": label, "hint": "Which part do you enjoy most?", "options": list(options), **extra}

def latest(client, event):
    return client.received(event)[-1]


# ===== Definitions ===== #

def test_a_valid_detail_is_cleaned():
    definition, error = parse_custom_attribute(detail(label="  Preferred   Role ", options=[" Frontend ", "", "Backend"]))
    assert error is None
    assert definition["label"] == "Preferred Role" and definition["options"] == ["Frontend", "Backend"]
    assert definition["multiple"] is False and definition["matching"] == "display"
    assert definition["id"].startswith("custom_")

@pytest.mark.parametrize("changes", [
    {"label": ""}, {"label": "x" * 41}, {"label": 5}, {"hint": "x" * 151}, {"options": ["Only one"]},
    {"options": [f"Option {i}" for i in range(MAX_OPTIONS + 1)]}, {"options": ["Same", "same"]}, {"options": "a,b"},
    {"options": ["Fine", "x" * 41]}, {"multiple": "yes"}, {"matching": "opposite"}, {"label": "Bad\x00Name"},
])
def test_invalid_details(changes):
    definition, error = parse_custom_attribute({**detail(), **changes})
    assert definition is None and error

def test_ids_are_kept_unless_invalid_or_repeated():
    kept, _ = parse_custom_attribute(detail(id="custom_abc123"))
    assert kept["id"] == "custom_abc123"
    replaced, _ = parse_custom_attribute(detail(id="goal_grade"))
    assert replaced["id"] != "goal_grade"

    definitions, error = parse_custom_attributes([detail(id="custom_same"), detail(label="Other", id="custom_same")])
    assert error is None and len({d["id"] for d in definitions}) == 2

def test_tutorial_detail_limits():
    assert parse_custom_attributes([detail(label=f"Detail {i}") for i in range(MAX_CUSTOM_ATTRIBUTES + 1)])[1]
    assert parse_custom_attributes([detail(), detail()])[1] # Same Name
    assert parse_custom_attributes("details")[1]

def test_answers():
    single, _ = parse_custom_attribute(detail())
    multiple, _ = parse_custom_attribute(detail(multiple=True))

    assert validate_custom_value(single, "Backend") == ("Backend", None)
    assert validate_custom_value(single, None) == (None, None)
    assert validate_custom_value(single, "Other")[1] and validate_custom_value(single, ["Backend"])[1]
    assert validate_custom_value(multiple, ["Design", "Frontend"]) == (["Frontend", "Design"], None)
    assert validate_custom_value(multiple, []) == ([], None)
    assert validate_custom_value(multiple, ["Other"])[1] and validate_custom_value(multiple, "Design")[1]


# ===== Tutorials ===== #

@pytest.fixture
def custom_staff(connect_staff):
    client = connect_staff()
    response = client.emit("create_tutorial", {
        "group_size": 2,
        "available_attributes": ["goal_grade"],
        "custom_attributes": [detail(matching="similar"), detail(label="Languages", options=["Python", "Java", "C"], multiple=True)],
    })
    assert response["ok"]
    client.code = response["tutorial_code"]
    client.custom = {d["label"]: d["id"] for d in tutorials[client.code]["custom_attributes"]}
    return client

def test_custom_details_are_enabled_for_a_tutorial(custom_staff, connect_student):
    role, languages = custom_staff.custom["Role"], custom_staff.custom["Languages"]
    assert tutorials[custom_staff.code]["available_attributes"] == ["goal_grade", role, languages]

    update = latest(connect_student(custom_staff.code), "student_update")
    assert [d["label"] for d in update["custom_attributes"]] == ["Role", "Languages"]
    assert "saved_id" not in update["custom_attributes"][0]
    assert role in update["shared_attributes"] # Matching Details are visible by default

def test_students_answer_custom_details(custom_staff, connect_student):
    role, languages = custom_staff.custom["Role"], custom_staff.custom["Languages"]
    student = connect_student(custom_staff.code)

    assert student.emit("update_details", {role: "Design", languages: ["C", "Python"]})["ok"]
    assert tutorials[custom_staff.code]["students"][student.id]["attributes"] == {role: "Design", languages: ["Python", "C"]}
    assert not student.emit("update_details", {role: "Painting"})["ok"]
    assert tutorials[custom_staff.code]["students"][student.id]["attributes"][role] == "Design"

def test_who_sees_custom_details(custom_staff, connect_student):
    role, languages = custom_staff.custom["Role"], custom_staff.custom["Languages"]
    student, other = connect_student(custom_staff.code), connect_student(custom_staff.code)
    student.emit("update_details", {role: "Design", languages: ["Java"], "shared_attributes": []})
    custom_staff.emit("start_grouping")

    member = next(m for m in latest(other, "student_update")["group_members"] if m["attributes"])
    assert member["attributes"] == {languages: ["Java"]} # Display Only is always visible, Matching can be hidden

def test_editing_custom_details_keeps_valid_answers(custom_staff, connect_student):
    role, languages = custom_staff.custom["Role"], custom_staff.custom["Languages"]
    student = connect_student(custom_staff.code)
    student.emit("update_details", {role: "Design", languages: ["Java", "C"]})
    student.emit("update_details", {"shared_attributes": []})

    definitions = tutorials[custom_staff.code]["custom_attributes"]
    assert custom_staff.emit("update_settings", {"custom_attributes": [
        {**definitions[0], "multiple": True, "matching": "display"},
        {**definitions[1], "options": ["Python", "C", "Rust"], "multiple": False, "matching": "mixed"},
    ]})["ok"]

    state = tutorials[custom_staff.code]["students"][student.id]
    assert state["attributes"] == {role: ["Design"], languages: "C"}
    assert state["shared_attributes"] == [languages] # Newly Matching, so visible until hidden

    custom_staff.emit("update_settings", {"custom_attributes": [definitions[1]]})
    assert role not in state["attributes"] and role not in tutorials[custom_staff.code]["available_attributes"]

def test_invalid_custom_details_are_refused(custom_staff):
    response = custom_staff.emit("update_settings", {"custom_attributes": [detail(options=["One"])]})
    assert not response["ok"] and "options" in response["message"]
    assert len(tutorials[custom_staff.code]["custom_attributes"]) == 2

def test_other_settings_keep_custom_details(custom_staff):
    custom_staff.emit("update_settings", {"available_attributes": ["availability"]})
    tutorial = tutorials[custom_staff.code]
    assert tutorial["available_attributes"] == ["availability", *custom_staff.custom.values()]

    custom_staff.emit("update_settings", {"group_size": 3})
    assert tutorial["available_attributes"] == ["availability", *custom_staff.custom.values()]


# ===== Matching ===== #

def tutorial_with(definition, answers):
    definitions, _ = parse_custom_attributes([definition])
    attribute = definitions[0]["id"]
    return {
        "group_size": 2, "max_groups": None, "available_attributes": [attribute], "custom_attributes": definitions,
        "previous_matches": {},
        "students": {f"s{i}": {"attributes": {attribute: answer}} for i, answer in enumerate(answers)},
    }

def test_similar_answers_are_grouped_together():
    tutorial = tutorial_with(detail(matching="similar"), ["Frontend", "Backend", "Frontend", "Backend", "Design", "Design"])
    for _ in range(5):
        groups = form_groups(tutorial)
        answers = [{tutorial["students"][s]["attributes"][tutorial["available_attributes"][0]] for s in g} for g in groups.values()]
        assert all(len(group) == 1 for group in answers)

def test_different_answers_are_mixed():
    tutorial = tutorial_with(detail(matching="mixed"), ["Frontend", "Frontend", "Backend", "Backend"])
    for _ in range(5):
        groups = form_groups(tutorial)
        answers = [{tutorial["students"][s]["attributes"][tutorial["available_attributes"][0]] for s in g} for g in groups.values()]
        assert all(len(group) == 2 for group in answers)

def test_multiple_choice_answers_are_compared_by_overlap():
    languages = detail(label="Languages", options=["Python", "Java", "C", "Rust"], multiple=True, matching="similar")
    tutorial = tutorial_with(languages, [["Python", "Java"], ["C", "Rust"], ["Java", "Python"], ["Rust"]])
    for _ in range(5):
        groups = sorted(sorted(g) for g in form_groups(tutorial).values())
        assert groups == [["s0", "s2"], ["s1", "s3"]]

def test_display_only_details_are_not_matched():
    tutorial = tutorial_with(detail(), ["Frontend", "Frontend", "Backend", "Backend"])
    seen = {tuple(sorted(tuple(sorted(g)) for g in form_groups(tutorial).values())) for _ in range(30)}
    assert len(seen) > 1


# ===== Saving to an Account ===== #

@pytest.fixture
def account_token(app, api):
    register_staff("tutor", "correct-password")
    return api.post("/api/staff/login", json={"username": "tutor", "password": "correct-password"}).get_json()["token"]

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def test_saving_custom_details(api, account_token):
    created = api.post("/api/staff/attributes", json=detail(matching="mixed", id="custom_ignored"), headers=auth(account_token))
    assert created.status_code == 201
    saved = created.get_json()["attribute"]
    assert saved["label"] == "Role" and saved["matching"] == "mixed" and "custom_" not in str(saved["id"])

    updated = api.put(f"/api/staff/attributes/{saved['id']}", json=detail(label="Team Role"), headers=auth(account_token))
    assert updated.status_code == 200 and updated.get_json()["attribute"]["label"] == "Team Role"

    listed = api.get("/api/staff/attributes", headers=auth(account_token)).get_json()["attributes"]
    assert [a["label"] for a in listed] == ["Team Role"]

    assert api.delete(f"/api/staff/attributes/{saved['id']}", headers=auth(account_token)).status_code == 200
    assert api.get("/api/staff/attributes", headers=auth(account_token)).get_json()["attributes"] == []

def test_invalid_saved_details(api, account_token):
    response = api.post("/api/staff/attributes", json=detail(options=["One"]), headers=auth(account_token))
    assert response.status_code == 400 and "options" in response.get_json()["message"]
    assert api.post("/api/staff/attributes", data="nonsense", headers=auth(account_token)).status_code == 400

def test_guests_cant_save(api):
    token = api.post("/api/staff/guest").get_json()["token"]
    assert api.get("/api/staff/attributes", headers=auth(token)).status_code == 403
    assert api.post("/api/staff/attributes", json=detail(), headers=auth(token)).status_code == 403
    assert api.get("/api/staff/attributes").status_code == 401

def test_accounts_only_see_their_own_details(api, account_token):
    saved = api.post("/api/staff/attributes", json=detail(), headers=auth(account_token)).get_json()["attribute"]
    register_staff("other", "correct-password")
    other = api.post("/api/staff/login", json={"username": "other", "password": "correct-password"}).get_json()["token"]

    assert api.get("/api/staff/attributes", headers=auth(other)).get_json()["attributes"] == []
    assert api.put(f"/api/staff/attributes/{saved['id']}", json=detail(), headers=auth(other)).status_code == 404
    assert api.delete(f"/api/staff/attributes/{saved['id']}", headers=auth(other)).status_code == 404

def test_saved_detail_limit(api, account_token, monkeypatch):
    monkeypatch.setattr("app.routes.saved.MAX_SAVED_ATTRIBUTES", 1)
    assert api.post("/api/staff/attributes", json=detail(), headers=auth(account_token)).status_code == 201
    assert api.post("/api/staff/attributes", json=detail(), headers=auth(account_token)).status_code == 400


# ===== Matching Weights ===== #

def test_weights_default_to_normal():
    definition, _ = parse_custom_attribute(detail(matching="similar"))
    assert definition["weight"] == "normal"
    high, _ = parse_custom_attribute(detail(matching="similar", weight="high"))
    assert high["weight"] == "high"
    assert parse_custom_attribute(detail(weight="extreme"))[1]

def test_weights_are_scaled_around_the_built_in_details():
    from app.custom_attributes import WEIGHTS
    assert WEIGHTS["low"] < WEIGHTS["normal"] < WEIGHTS["high"] < 5 # An exact grade match
    assert 2 <= WEIGHTS["low"] and WEIGHTS["high"] / WEIGHTS["low"] < 2 # Not too drastic

def test_higher_weighted_details_count_more():
    definitions, _ = parse_custom_attributes([
        detail(label="Role", matching="similar", weight="high"),
        detail(label="Campus", options=["North", "South"], matching="similar", weight="low"),
    ])
    role, campus = (d["id"] for d in definitions)
    # Grouping by Role pairs (s0, s1) and (s2, s3), but by Campus pairs (s0, s2) and (s1, s3)
    answers = [("Frontend", "North"), ("Frontend", "South"), ("Backend", "North"), ("Backend", "South")]
    tutorial = {
        "group_size": 2, "max_groups": None, "available_attributes": [role, campus], "custom_attributes": definitions,
        "previous_matches": {},
        "students": {f"s{i}": {"attributes": {role: r, campus: c}} for i, (r, c) in enumerate(answers)},
    }
    for _ in range(5):
        assert sorted(sorted(g) for g in form_groups(tutorial).values()) == [["s0", "s1"], ["s2", "s3"]]

    definitions[0]["weight"], definitions[1]["weight"] = "low", "high"
    for _ in range(5):
        assert sorted(sorted(g) for g in form_groups(tutorial).values()) == [["s0", "s2"], ["s1", "s3"]]

def test_saved_details_keep_their_weight(api, account_token):
    saved = api.post("/api/staff/attributes", json=detail(matching="mixed", weight="low"), headers=auth(account_token))
    assert saved.get_json()["attribute"]["weight"] == "low"
