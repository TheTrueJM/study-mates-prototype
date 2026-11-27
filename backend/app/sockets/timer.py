from time import monotonic
import gevent


class AsyncTimer:
    """
    Runs the Introduction, Discussion, and Wrap-Up Timer of each Tutorial. A running Timer only stores when it ends, so clients
    count down by themselves and are only updated when the Timer changes (rather than every second).
    """

    def __init__(self):
        self.socketio = None
        self.app_ctx = None
        self.greenlets = dict() # { code: Greenlet waiting for the Timer to finish }

    @staticmethod
    def create(duration):
        return {"duration": duration, "remaining": duration, "ends_at": None}

    @staticmethod
    def is_running(timer):
        return timer["ends_at"] is not None

    @staticmethod
    def get_remaining(timer):
        if timer["ends_at"] is None:
            return timer["remaining"]
        return max(0, timer["ends_at"] - monotonic())

    def get_state(self, timer):
        """The Timer as sent to clients, where the remaining seconds are from the moment it is sent"""
        return {
            "duration": timer["duration"],
            "remaining": round(self.get_remaining(timer), 3),
            "running": self.is_running(timer),
        }

    def start(self, code):
        if not (timer := self._get_timer(code)) or self.is_running(timer):
            return

        timer["ends_at"] = monotonic() + timer["remaining"]
        self._schedule(code, timer["remaining"])

    def stop(self, code):
        self._cancel(code)
        if timer := self._get_timer(code):
            timer["remaining"] = self.get_remaining(timer)
            timer["ends_at"] = None

    def reset(self, code, duration=None):
        self.stop(code)
        if timer := self._get_timer(code):
            if duration is not None:
                timer["duration"] = duration
            timer["remaining"] = timer["duration"]

    def adjust(self, code, seconds):
        """
        Adds (or removes) time from the Timer. Adding time continues the Timer if it was running or had finished,
        while removing all of the remaining time finishes it.
        """
        if not (timer := self._get_timer(code)):
            return

        running = self.is_running(timer)
        resume = running or (seconds > 0 and timer["remaining"] <= 0)
        self.stop(code)
        timer["remaining"] = max(0, timer["remaining"] + seconds)

        if timer["remaining"] > 0 and resume:
            self.start(code)
        elif timer["remaining"] <= 0 and running:
            self._finish(code)

    def _get_timer(self, code):
        from . import utils
        return utils.tutorials.get(code, {}).get("timer")

    def _schedule(self, code, seconds):
        self._cancel(code)
        self.greenlets[code] = gevent.spawn_later(seconds, self._finish, code)

    def _cancel(self, code):
        if greenlet := self.greenlets.pop(code, None):
            greenlet.kill(block=False)

    def _finish(self, code):
        from . import utils
        from ..enums import TutorialState

        self.greenlets.pop(code, None)
        if not (timer := self._get_timer(code)):
            return

        timer["remaining"] = 0
        timer["ends_at"] = None
        utils.record_activity(code)

        with self.app_ctx.app_context():
            state = utils.tutorials[code]["state"]
            namespaces = ["/", "/staff"]

            # Introductions roll straight into the Discussion
            if state == TutorialState.INTRODUCTION:
                utils.begin_discussion(code)
                message = {"message": "Introductions are over. Time to Discuss!"}
            # The Wrap-Up countdown is only a guide for the Staff Member
            elif state == TutorialState.WRAP_UP:
                namespaces = ["/staff"]
                message = {"message": "Wrap-Up time is over. Close the Session once everyone is Ready."}
            else:
                message = {"message": "Time's up! Discussion time has finished."}

            utils.emit_tutorial_update(code)
            for namespace in namespaces:
                self.socketio.emit("timer_notification", message, room=code, namespace=namespace)


timer = AsyncTimer()
