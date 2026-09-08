import asyncio
from typing import Any


class EventBus:
    """Bus pub/sub en memoria para eventos de tiempo real (SSE)."""

    def __init__(self) -> None:
        self._subscribers: list[asyncio.Queue] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def publish(self, event_type: str, data: Any) -> None:
        if self._loop is None or self._loop.is_closed():
            return
        message = {"type": event_type, "data": data}
        for queue in self._subscribers:
            self._loop.call_soon_threadsafe(self._enqueue, queue, message)

    def _enqueue(self, queue: asyncio.Queue, message: dict) -> None:
        try:
            queue.put_nowait(message)
        except Exception:
            pass


event_bus = EventBus()
