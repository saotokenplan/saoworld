from typing import Callable, Dict, List, Optional

from workers.events.event_bus import EventBus
from workers.events.schemas import Event, EventType


class EventSubscriber:
    def __init__(self, event_bus: EventBus | None = None):
        self.event_bus = event_bus or EventBus.create()
        self._handlers: Dict[EventType, List[Callable[[Event], None]]] = {}

    def register_handler(
        self, event_type: EventType, handler: Callable[[Event], None]
    ) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    async def subscribe(self, event_types: List[EventType]) -> None:
        pubsub = await self.event_bus.subscribe(event_types)
        try:
            while True:
                event = await self.event_bus.get_message(pubsub)
                if event:
                    await self._handle_event(event)
        except asyncio.CancelledError:
            await self.event_bus.unsubscribe(pubsub)

    async def _handle_event(self, event: Event) -> None:
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                pass

    async def handle_single_event(self, event_type: EventType, timeout: float = 5.0) -> Optional[Event]:
        pubsub = await self.event_bus.subscribe([event_type])
        try:
            return await self.event_bus.get_message(pubsub, timeout=timeout)
        finally:
            await self.event_bus.unsubscribe(pubsub)


import asyncio