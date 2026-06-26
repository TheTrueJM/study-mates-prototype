# TODO REVIEW THIS STILL

from threading import Thread, Lock
from time import monotonic, sleep
from collections import deque


class AsyncTimer:
    __slots__ = (
        "codes",
        "lock",
        "tutorials",
        "running",
        "next_tick",
        "socketio",
        "app_ctx",
        "deque",
        "_timer_thread",
    )

    def __init__(self):
        self.codes = set()
        self.lock = Lock()
        self.tutorials = None
        self.running = False
        self.next_tick = None
        self.socketio = None
        self.app_ctx = None
        self.deque = deque()
        self._timer_thread = None

    def start(self, code):
        from . import utils

        if not utils.tutorials.get(code):
            return

        with self.lock:
            self.codes.add(code)

        if self.tutorials is None:
            self.tutorials = utils.tutorials

        if not self.running:
            self.running = True
            self.next_tick = monotonic() + 1
            self.deque.clear()
            self._timer_thread = Thread(target=self._timer_loop, daemon=True)
            self._timer_thread.start()
            self.socketio.start_background_task(self._emit_loop)

    def _emit_loop(self):
        import eventlet
        from . import utils

        socketio = self.socketio
        tutorials = self.tutorials
        dq = self.deque
        app_ctx = self.app_ctx

        while self.running:
            while dq:
                try:
                    item = dq.popleft()
                except IndexError:
                    break

                if item is None:
                    return

                code, remaining, is_done = item
                tutorial = tutorials.get(code)
                if not tutorial:
                    continue

                with app_ctx.app_context():
                    if is_done:
                        message = {"message": "Time's up!"}
                        socketio.emit(
                            "timer_notification", message, room=code, namespace="/"
                        )
                        socketio.emit(
                            "timer_notification", message, room=code, namespace="/staff"
                        )
                    else:
                        utils._emit_tutorial_update(code)

            eventlet.sleep(0.001)

    def _timer_loop(self):
        tutorials = self.tutorials
        dq = self.deque
        next_tick = self.next_tick or 0.0

        while self.running:
            sleep(max(0, next_tick - monotonic()))

            with self.lock:
                if not (codes := list(self.codes)):
                    self.running = False
                    dq.append(None)
                    return

                next_tick += 1
                self.next_tick = next_tick

                finished = []

                for c in codes:
                    tutorial = tutorials.get(c) if tutorials else None
                    if not tutorial:
                        finished.append(c)
                        continue

                    timer = tutorial.get("timer")
                    if not timer or not timer.get("running", False):
                        finished.append(c)
                        continue

                    remaining = timer["remaining"] - 1
                    timer["remaining"] = max(0, remaining)

                    if remaining <= 0:
                        timer["running"] = False
                        dq.append((c, remaining, True))
                        finished.append(c)
                    else:
                        dq.append((c, remaining, False))

                if finished:
                    for c in finished:
                        self.codes.discard(c)

    def stop(self, code):
        with self.lock:
            self.codes.discard(code)

    def _reset(self):
        self.codes.clear()
        self.running = False
        self.next_tick = None
        self.tutorials = None
        self.deque.clear()
        self._timer_thread = None


timer = AsyncTimer()
