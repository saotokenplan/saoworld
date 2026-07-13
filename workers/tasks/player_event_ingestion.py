from datetime import datetime
from typing import Any, Dict

import structlog

from workers.config import settings

logger = structlog.get_logger()


async def store_player_event(event_data: Dict[str, Any]) -> None:
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import insert
        from app.domain.models import PlayerEvent

        engine = create_async_engine(settings.database_url)
        async with engine.begin() as conn:
            occurred_at = datetime.fromisoformat(event_data.get("occurred_at"))
            stmt = insert(PlayerEvent).values(
                event_id=event_data.get("event_id"),
                event_type=event_data.get("event_type", ""),
                player_id=event_data.get("player_id", ""),
                region_id=event_data.get("region_id"),
                occurred_at=occurred_at,
                payload_jsonb=event_data.get("payload"),
                trace_id=event_data.get("trace_id"),
                producer=event_data.get("producer", "gateway"),
                schema_version=event_data.get("schema_version", 1),
            )
            await conn.execute(stmt)

        logger.info(
            "player_event_stored",
            event_id=event_data.get("event_id"),
            event_type=event_data.get("event_type"),
            player_id=event_data.get("player_id"),
        )
    except Exception as exc:
        logger.error(
            "player_event_store_failed",
            error=str(exc),
            event_type=event_data.get("event_type"),
            player_id=event_data.get("player_id"),
        )
        raise