import queue
import threading
from enum import Enum


class MessageType(Enum):
    PROGRESS = "progress"
    RESULT = "result"
    ERROR = "error"
    DONE = "done"


class QueueHandler:
    def __init__(self):
        self._queue = queue.Queue()

    def put(self, msg_type, data=None):
        self._queue.put({"type": msg_type.value, "data": data})

    def get(self, block=False, timeout=None):
        try:
            return self._queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def drain(self):
        items = []
        while not self._queue.empty():
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                break
        return items

    @property
    def q(self):
        return self._queue
