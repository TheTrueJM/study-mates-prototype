from time import monotonic
from collections import deque
import gevent, gevent.lock


class AsyncTimer:
    def __init__(self):
        self.codes = set()
        self.lock = gevent.lock.Semaphore()
        self.tutorials = None
        self.running = False
        self.next_tick = None
        self.socketio = None
        self.app_ctx = None
        self.timer_greenlet = None
        self.deque = deque()

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
            gevent.spawn(self._timer_loop)
            self.socketio.start_background_task(self._emit_loop)

    def _emit_loop(self):
        from . import utils

        socketio = self.socketio
        tutorials = self.tutorials
        app_ctx = self.app_ctx

        while self.running:
            for code, remaining, is_done in self._drain_deque():
                tutorial = tutorials.get(code)
                if not tutorial:
                    continue

                if app_ctx is not None:
                    with app_ctx.app_context():
                        if is_done:
                            message = {"message": "Time's up!"}
                            for namespace in ["/", "/staff"]:
                                socketio.emit("timer_notification", message, room=code, namespace=namespace)
                        else:
                            utils.emit_tutorial_update(code)
                else:
                    if is_done:
                        for namespace in ["/", "/staff"]:
                            socketio.emit("timer_notification", message, room=code, namespace=namespace)
                    else:
                        utils.emit_tutorial_update(code)

            gevent.sleep(0.01)

    def _drain_deque(self):
        items = []
        with self.lock:
            while self.deque:
                try:
                    items.append(self.deque.popleft())
                except IndexError:
                    break
        return items

    def _timer_loop(self):
        next_tick = self.next_tick or 0.0

        while self.running:
            gevent.sleep(max(0, next_tick - monotonic()))

            with self.lock:
                if not (codes := list(self.codes)):
                    self.running = False
                    return

                next_tick += 1
                self.next_tick = next_tick

                finished = []

                for c in codes:
                    tutorial = self.tutorials.get(c) if self.tutorials else None
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
                        self.deque.append((c, remaining, True))
                        finished.append(c)
                    else:
                        self.deque.append((c, remaining, False))

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


timer = AsyncTimer()