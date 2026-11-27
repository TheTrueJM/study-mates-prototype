import time
import gevent
import pytest

from app.sockets import utils
from app.sockets.staff import TIMER_ADJUSTMENT_SECONDS, INTRODUCTION_SECONDS
from app.sockets.timer import timer
from app.sockets.utils import tutorials, users


def latest(client, event="tutorial_update"):
    return client.received(event)[-1]

def start_introductions(staff, connect_student, students=2):
    clients = [connect_student(staff.code) for _ in range(students)]
    assert staff.emit("start_grouping")["ok"]
    assert staff.emit("start_discussion")["ok"]
    return clients

def start_discussion(staff, connect_student, students=2):
    clients = start_introductions(staff, connect_student, students)
    assert staff.emit("skip_introduction")["ok"]
    return clients


# ===== Students ===== #

def test_student_returns_to_the_same_place(staff, connect_student):
    student = connect_student(staff.code)
    name = latest(student, "student_update")["username"]
    student.disconnect()

    assert list(latest(staff)["students"].values())[0]["connected"] is False
    returned = connect_student(student_id=student.id)
    assert latest(returned, "student_update")["username"] == name
    assert list(latest(staff)["students"].values())[0]["connected"] is True
    assert len(tutorials[staff.code]["students"]) == 1


def test_leaving(staff, connect_student):
    student = connect_student(staff.code)
    assert student.emit("leave_tutorial")["ok"]
    assert not tutorials[staff.code]["students"]


def test_removing_a_student(staff, connect_student):
    student, other = connect_student(staff.code), connect_student(staff.code)
    assert staff.emit("remove_student", {"student_id": student.id})["ok"]

    assert latest(student, "left_tutorial")["removed"] is True
    assert list(tutorials[staff.code]["students"]) == [other.id]
    assert not staff.emit("remove_student", {"student_id": student.id})["ok"]
    assert not staff.emit("remove_student", {"student_id": ["invalid"]})["ok"]

def test_removing_an_offline_student_forgets_them(staff, connect_student):
    student = connect_student(staff.code)
    student.disconnect()
    assert staff.emit("remove_student", {"student_id": student.id})["ok"]
    assert student.id not in users

def test_only_the_tutorials_staff_can_remove_students(staff, connect_staff, connect_student):
    student, other_staff = connect_student(staff.code), connect_staff()
    other_staff.emit("create_tutorial", {"group_size": 2})
    assert not other_staff.emit("remove_student", {"student_id": student.id})["ok"]
    assert student.id in tutorials[staff.code]["students"]


def test_locking(staff, connect_student):
    student = connect_student(staff.code)
    assert staff.emit("lock_tutorial", {"locked": True})["ok"]

    late = connect_student(staff.code)
    assert not late.joined["ok"] and "Locked" in late.joined["message"]
    assert student.emit("enter_tutorial", {"code": staff.code})["ok"] # Already in the Tutorial

    staff.emit("lock_tutorial", {"locked": False})
    assert late.emit("enter_tutorial", {"code": staff.code})["ok"]
    assert not staff.emit("lock_tutorial", {"locked": "yes"})["ok"]

def test_locked_tutorial_keeps_student_in_their_current_tutorial(staff, connect_staff, connect_student):
    other_staff = connect_staff()
    code = other_staff.emit("create_tutorial", {"group_size": 2})["tutorial_code"]
    other_staff.emit("lock_tutorial", {"locked": True})

    student = connect_student(staff.code)
    assert not student.emit("enter_tutorial", {"code": code})["ok"]
    assert student.id in tutorials[staff.code]["students"]


def test_full_tutorial(staff, connect_student, monkeypatch):
    monkeypatch.setattr("app.sockets.student.MAX_STUDENTS", 1)
    assert connect_student(staff.code).joined["ok"]
    assert not connect_student(staff.code).joined["ok"]

def test_names_are_unique_once_all_are_taken(app):
    names = [f"{d.capitalize()}-{a.capitalize()}" for d in utils.DESCRIPTORS for a in utils.ANIMALS]
    tutorials["NAMES"] = {"students": {i: {"name": name} for i, name in enumerate(names)}, "timer": timer.create(60)}
    assert utils.generate_unique_student_name("NAMES") not in names


@pytest.mark.parametrize("details", [
    {"shared_attributes": [[1], {}, None]}, {"meeting_mode": ["virtual"]}, {"meeting_mode": {}},
    {"goal_grade": {}}, {"current_gpa": [4]}, {"availability": {}}, {"communication": 5}, "invalid",
])
def test_malformed_details_are_answered(staff, connect_student, details):
    response = connect_student(staff.code).emit("update_details", details)
    assert isinstance(response, dict) and "ok" in response


# ===== Rounds ===== #

def test_steps_are_in_order(staff, connect_student):
    assert not staff.emit("start_discussion")["ok"]
    for event in ("start_timer", "stop_timer", "reset_timer", "adjust_timer", "skip_introduction"):
        assert not staff.emit(event)["ok"]
    assert tutorials[staff.code]["state"].value == "lobby"

    start_discussion(staff, connect_student)
    assert not staff.emit("start_discussion")["ok"] # Already started

def test_discussion_needs_groups(staff, connect_student):
    clients = [connect_student(staff.code) for _ in range(2)]
    staff.emit("start_grouping")
    for client in clients:
        client.emit("leave_tutorial")
    assert not staff.emit("start_discussion")["ok"]


def test_round_counter(staff, connect_student):
    students = [connect_student(staff.code) for _ in range(4)]
    current = lambda: (tutorials[staff.code]["round"], tutorials[staff.code]["formation"])
    assert current() == (0, 0)

    staff.emit("start_grouping")
    assert current() == (1, 1)
    staff.emit("start_grouping") # Reform
    assert current() == (1, 2)
    staff.emit("return_lobby")
    staff.emit("start_grouping") # Never Discussed
    assert current() == (1, 3)

    staff.emit("start_discussion")
    staff.emit("start_grouping")
    assert current() == (2, 4)
    assert latest(staff)["round"] == 2
    update = latest(students[0], "student_update")
    assert (update["round"], update["formation"]) == (2, 4)


# ===== Introductions ===== #

def test_discussion_begins_with_introductions(staff, connect_student):
    student = start_introductions(staff, connect_student)[0]
    tutorial = tutorials[staff.code]
    assert tutorial["state"].value == "introduction" and len(tutorial["questions"]) == 3

    update = latest(student, "student_update")
    assert update["state"] == "introduction" and update["questions"] == tutorial["questions"]
    assert update["timer"]["duration"] == INTRODUCTION_SECONDS and update["timer"]["running"]
    assert update["discussion_time"] == 300

def test_introductions_roll_into_the_full_discussion(staff, connect_student):
    student = start_introductions(staff, connect_student)[0]
    questions = list(tutorials[staff.code]["questions"])
    staff.emit("stop_timer")
    tutorials[staff.code]["timer"]["remaining"] = 0.1
    staff.emit("start_timer")
    gevent.sleep(0.3)

    update = latest(student, "student_update")
    assert update["state"] == "discussion" and update["questions"] == questions
    assert update["timer"]["running"] and update["timer"]["duration"] == 300 and update["timer"]["remaining"] > 299
    assert "Discuss" in latest(student, "timer_notification")["message"]

def test_skipping_introductions(staff, connect_student):
    start_introductions(staff, connect_student)
    assert staff.emit("skip_introduction")["ok"]
    state = tutorials[staff.code]["timer"]
    assert tutorials[staff.code]["state"].value == "discussion"
    assert timer.is_running(state) and 299 < timer.get_remaining(state) <= 300
    assert not staff.emit("skip_introduction")["ok"]

def test_changing_the_discussion_time_during_introductions(staff, connect_student):
    start_introductions(staff, connect_student)
    assert staff.emit("update_settings", {"discussion_time": 2})["ok"]
    state = tutorials[staff.code]["timer"]
    assert timer.is_running(state) and timer.get_remaining(state) <= INTRODUCTION_SECONDS

    staff.emit("skip_introduction")
    assert 119 < timer.get_remaining(state) <= 120
    assert not staff.emit("reset_timer", {"time": 90})["ok"] # Too long
    assert staff.emit("reset_timer", {"time": 3})["ok"]
    assert latest(staff)["discussion_time"] == state["duration"] == 180

def test_the_next_round_returns_to_the_discussion_time(staff, connect_student):
    start_introductions(staff, connect_student)
    staff.emit("start_grouping")
    assert tutorials[staff.code]["timer"]["duration"] == 300 and not timer.is_running(tutorials[staff.code]["timer"])


# ===== Timer ===== #

def test_running_timer_only_sends_changes(staff, connect_student):
    students = start_discussion(staff, connect_student)
    state = latest(staff)["timer"]
    assert state["running"] and state["duration"] == 300 and 299 < state["remaining"] <= 300

    students[0].received("student_update")
    gevent.sleep(1.2)
    assert not students[0].received("student_update")
    assert 298 < timer.get_remaining(tutorials[staff.code]["timer"]) < 299

def test_pausing_keeps_the_exact_time(staff, connect_student):
    start_discussion(staff, connect_student)
    for _ in range(4):
        staff.emit("stop_timer")
        gevent.sleep(0.2)
        staff.emit("start_timer")
        gevent.sleep(0.1)
    staff.emit("stop_timer")
    assert 299.3 < latest(staff)["timer"]["remaining"] < 299.65

def test_timer_finishes(staff, connect_student):
    student = start_discussion(staff, connect_student)[0]
    staff.emit("stop_timer")
    tutorials[staff.code]["timer"]["remaining"] = 0.1
    staff.emit("start_timer")
    student.received("student_update")
    gevent.sleep(0.3)

    assert [update["timer"] for update in student.received("student_update")] == [
        {"duration": 300, "remaining": 0, "running": False}
    ]
    assert len(student.received("timer_notification")) == 1

    staff.emit("start_timer") # Restarts
    assert latest(staff)["timer"]["remaining"] > 299

def adjust(staff, seconds):
    return staff.emit("adjust_timer", {"seconds": seconds})

def test_adding_time(staff, connect_student):
    start_discussion(staff, connect_student)
    state = tutorials[staff.code]["timer"]

    assert adjust(staff, TIMER_ADJUSTMENT_SECONDS)["ok"]
    assert timer.is_running(state) and 299 < timer.get_remaining(state) - TIMER_ADJUSTMENT_SECONDS <= 300

    staff.emit("stop_timer")
    paused = timer.get_remaining(state)
    adjust(staff, TIMER_ADJUSTMENT_SECONDS)
    assert not timer.is_running(state) and timer.get_remaining(state) == pytest.approx(paused + TIMER_ADJUSTMENT_SECONDS)

    state["remaining"] = 0 # Finished
    adjust(staff, TIMER_ADJUSTMENT_SECONDS)
    assert timer.is_running(state) and timer.get_remaining(state) <= TIMER_ADJUSTMENT_SECONDS

    staff.emit("stop_timer")
    state["remaining"] = 60 * 60
    assert not adjust(staff, TIMER_ADJUSTMENT_SECONDS)["ok"]
    staff.emit("reset_timer")
    assert state["remaining"] == state["duration"] == 300

def test_removing_time(staff, connect_student):
    student = start_discussion(staff, connect_student)[0]
    state = tutorials[staff.code]["timer"]

    assert adjust(staff, -TIMER_ADJUSTMENT_SECONDS)["ok"]
    assert timer.is_running(state) and 269 < timer.get_remaining(state) <= 270

    staff.emit("stop_timer")
    adjust(staff, -TIMER_ADJUSTMENT_SECONDS)
    assert not timer.is_running(state) and 239 < timer.get_remaining(state) <= 240

    # Removing the last of the time finishes the Timer
    staff.emit("start_timer")
    state["ends_at"] = time.monotonic() + 10
    student.received("timer_notification")
    adjust(staff, -TIMER_ADJUSTMENT_SECONDS)
    assert not timer.is_running(state) and state["remaining"] == 0
    assert len(student.received("timer_notification")) == 1
    assert not adjust(staff, -TIMER_ADJUSTMENT_SECONDS)["ok"]

@pytest.mark.parametrize("data", [{}, {"seconds": 60}, {"seconds": "30"}, {"seconds": True}, {"seconds": 30.5}, "30"])
def test_invalid_adjustments(staff, connect_student, data):
    start_discussion(staff, connect_student)
    assert not staff.emit("adjust_timer", data)["ok"]


# ===== Closing ===== #

def test_wrapping_up(staff, connect_student):
    student = start_discussion(staff, connect_student)[0]
    assert staff.emit("wrap_up")["ok"]
    tutorial = tutorials[staff.code]

    update = latest(student, "student_update")
    assert update["state"] == "wrap_up" and not update["questions"]
    assert update["timer"]["running"] and update["timer"]["duration"] == 120
    assert not staff.emit("wrap_up")["ok"]
    assert staff.emit("adjust_timer", {"seconds": 30})["ok"] and staff.emit("stop_timer")["ok"]

    # Only the Staff Member is told the Countdown has finished, and the Session stays open
    tutorial["timer"]["remaining"] = 0.1
    staff.emit("start_timer")
    student.received("timer_notification")
    gevent.sleep(0.3)
    assert staff.code in tutorials and tutorial["state"].value == "wrap_up"
    assert len(staff.received("timer_notification")) == 1 and not student.received("timer_notification")

def test_no_one_new_joins_while_wrapping_up(staff, connect_student):
    student = start_discussion(staff, connect_student)[0]
    staff.emit("wrap_up")
    late = connect_student(staff.code)
    assert not late.joined["ok"] and "Finishing" in late.joined["message"]
    assert student.emit("enter_tutorial", {"code": staff.code})["ok"] # Already in the Tutorial

def test_wrapping_up_can_be_undone(staff, connect_student):
    start_discussion(staff, connect_student)
    staff.emit("wrap_up")
    assert staff.emit("return_lobby")["ok"]
    assert tutorials[staff.code]["state"].value == "lobby" and not timer.is_running(tutorials[staff.code]["timer"])

def test_closing_after_wrapping_up(staff, connect_student):
    student = start_discussion(staff, connect_student)[0]
    staff.emit("wrap_up")
    assert staff.emit("end_tutorial")["ok"]
    assert latest(student, "tutorial_ended")["reason"] == "ended" and not tutorials

def test_ending_deletes_everything(staff, connect_student):
    online, offline = connect_student(staff.code), connect_student(staff.code)
    offline.disconnect()
    assert staff.emit("end_tutorial")["ok"]

    assert latest(online, "tutorial_ended")["reason"] == "ended"
    assert not tutorials and offline.id not in users
    assert staff.emit("create_tutorial", {"group_size": 2})["ok"]


def test_idle_tutorials_are_closed(staff, connect_student):
    student = connect_student(staff.code)
    utils.cleanup_expired_tutorials()
    assert staff.code in tutorials

    tutorials[staff.code]["last_activity"] = time.time() - utils.IDLE_LIMIT - 1
    utils.cleanup_expired_tutorials()
    assert staff.code not in tutorials
    assert latest(staff, "tutorial_ended")["reason"] == latest(student, "tutorial_ended")["reason"] == "idle"
    assert staff.emit("create_tutorial", {"group_size": 2})["ok"] # No longer running one

def test_tutorials_with_a_running_timer_are_not_idle(staff, connect_student):
    start_discussion(staff, connect_student)
    tutorials[staff.code]["last_activity"] = time.time() - utils.IDLE_LIMIT - 1
    utils.cleanup_expired_tutorials()
    assert staff.code in tutorials

def test_student_activity_keeps_a_tutorial_open(staff, connect_student):
    tutorials[staff.code]["last_activity"] = time.time() - utils.IDLE_LIMIT - 1
    connect_student(staff.code)
    utils.cleanup_expired_tutorials()
    assert staff.code in tutorials
