import sys

import uuid
from unittest.mock import MagicMock, AsyncMock

import pytest


class TestEventBusIntegration:
    @pytest.mark.asyncio
    async def test_event_bus_publish(self):
        old_path = sys.path.copy()
        sys.path.insert(0, '/workspace/workers')

        try:
            from events.event_bus import EventBus
            from events.schemas import EventType

            mock_redis = MagicMock()
            mock_redis.publish = AsyncMock(return_value=1)

            event_bus = EventBus()
            event_bus._redis = mock_redis

            await event_bus.publish(
                event_type=EventType.VOTE_RESULT_FINALIZED,
                payload={
                    "cycle_id": str(uuid.uuid4()),
                    "winning_candidate_id": str(uuid.uuid4()),
                    "total_votes": 100,
                },
                trace_id="trace_test",
            )

            mock_redis.publish.assert_called_once()
        finally:
            sys.path[:] = old_path

    @pytest.mark.asyncio
    async def test_event_bus_subscribe(self):
        old_path = sys.path.copy()
        sys.path.insert(0, '/workspace/workers')

        try:
            from events.event_bus import EventBus
            from events.schemas import EventType

            mock_redis = MagicMock()
            mock_pubsub = MagicMock()
            mock_redis.pubsub = MagicMock(return_value=mock_pubsub)
            mock_pubsub.subscribe = AsyncMock()

            event_bus = EventBus()
            event_bus._redis = mock_redis

            await event_bus.subscribe([EventType.VOTE_RESULT_FINALIZED, EventType.CONTENT_PACKAGE_RELEASED])

            mock_redis.pubsub.assert_called_once()
            mock_pubsub.subscribe.assert_called_once()
        finally:
            sys.path[:] = old_path
