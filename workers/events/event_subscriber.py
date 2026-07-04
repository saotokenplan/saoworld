import asyncio
import logging
from typing import Callable, Dict, List, Optional

from workers.events.event_bus import EventBus
from workers.events.schemas import Event, EventType

logger = logging.getLogger(__name__)


class EventSubscriber:
    def __init__(self, event_bus: EventBus | None = None):
        self.event_bus = event_bus or EventBus.create()
        self._handlers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._max_retries: int = 3
        self._base_delay: float = 1.0
        self._dead_letter_channel: str = "event.dead_letter"

    def register_handler(
        self, event_type: EventType, handler: Callable[[Event], None]
    ) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def set_retry_config(self, max_retries: int = 3, base_delay: float = 1.0) -> None:
        self._max_retries = max_retries
        self._base_delay = base_delay

    async def subscribe(self, event_types: List[EventType]) -> None:
        pubsub = await self.event_bus.subscribe(event_types)
        try:
            while True:
                event = await self.event_bus.get_message(pubsub)
                if event:
                    await self._handle_event_with_retry(event)
        except asyncio.CancelledError:
            await self.event_bus.unsubscribe(pubsub)

    async def _handle_event_with_retry(self, event: Event) -> None:
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            await self._execute_with_retry(handler, event)

    async def _execute_with_retry(self, handler: Callable[[Event], None], event: Event) -> None:
        last_exception = None
        for attempt in range(self._max_retries + 1):
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
                return
            except Exception as e:
                last_exception = e
                logger.warning(
                    "Event handler failed (attempt %d/%d): %s",
                    attempt + 1,
                    self._max_retries + 1,
                    str(e),
                )
                if attempt < self._max_retries:
                    delay = self._base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)

        logger.error(
            "Event handler failed after %d attempts, sending to dead letter queue. Event: %s",
            self._max_retries + 1,
            event.event_id,
        )
        await self._send_to_dead_letter(event, last_exception)

    async def _send_to_dead_letter(self, event: Event, exception: Exception) -> None:
        import json
        from datetime import datetime

        dead_letter_message = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "original_payload": event.payload,
            "trace_id": event.trace_id,
            "producer": event.producer,
            "occurred_at": event.occurred_at,
            "failed_at": datetime.utcnow().isoformat(),
            "error": str(exception),
            "error_type": type(exception).__name__,
        }
        try:
            await self.event_bus._redis.publish(
                self._dead_letter_channel,
                json.dumps(dead_letter_message),
            )
        except Exception as e:
            logger.error("Failed to send event to dead letter queue: %s", str(e))

    async def handle_single_event(self, event_type: EventType, timeout: float = 5.0) -> Optional[Event]:
        pubsub = await self.event_bus.subscribe([event_type])
        try:
            return await self.event_bus.get_message(pubsub, timeout=timeout)
        finally:
            await self.event_bus.unsubscribe(pubsub)