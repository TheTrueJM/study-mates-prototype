from pudb import set_trace
import logging
import time

logger = logging.getLogger(__name__)

def set_session(client, **kwargs):
   with client.session_transaction() as s:
       for k,v in kwargs.items():
           s[k] = v

def get_last_received(sio_client, timeout=5, namespace="/", name=None, all=False):
    deadline = time.time() + timeout

    while (
        len(r := sio_client.get_received(namespace)) == 0
        or (
            name is not None
            and not (
                match := next(
                    (m for m in reversed(r) if m["name"] == name),
                    None,
                )
            )
        )
    ):
        logger.info(r)
        if time.time() > deadline:
            return None
        time.sleep(0.1)

    if all:
        return r
    elif name is None:
        return r.pop()["args"][0]

    return match["args"][0]
