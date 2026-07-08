import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import PlayerEvent


class PlayerEventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_event(
        self,
        *,
        event_id: uuid.UUID,
        event_type: str,
        player_id: str,
        region_id: str | None = None,
        occurred_at: datetime | None = None,
        payload_jsonb: dict | None = None,
        trace_id: str | None = None,
        producer: str = "gateway",
        schema_version: int = 1,
    ) -> PlayerEvent:
        event = PlayerEvent(
            event_id=event_id,
            event_type=event_type,
            player_id=player_id,
            region_id=region_id,
            occurred_at=occurred_at or datetime.utcnow(),
            payload_jsonb=payload_jsonb,
            trace_id=trace_id,
            producer=producer,
            schema_version=schema_version,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_event_by_id(self, event_id: uuid.UUID) -> PlayerEvent | None:
        stmt: Select[tuple[PlayerEvent]] = select(PlayerEvent).where(
            PlayerEvent.event_id == event_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_player_events(
        self,
        player_id: str | None = None,
        event_type: str | None = None,
        region_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[PlayerEvent], int]:
        stmt = select(PlayerEvent)
        count_stmt = select(sa_func.count(PlayerEvent.event_id))

        if player_id:
            stmt = stmt.where(PlayerEvent.player_id == player_id)
            count_stmt = count_stmt.where(PlayerEvent.player_id == player_id)

        if event_type:
            stmt = stmt.where(PlayerEvent.event_type == event_type)
            count_stmt = count_stmt.where(PlayerEvent.event_type == event_type)

        if region_id:
            stmt = stmt.where(PlayerEvent.region_id == region_id)
            count_stmt = count_stmt.where(PlayerEvent.region_id == region_id)

        if start_time:
            stmt = stmt.where(PlayerEvent.occurred_at >= start_time)
            count_stmt = count_stmt.where(PlayerEvent.occurred_at >= start_time)

        if end_time:
            stmt = stmt.where(PlayerEvent.occurred_at <= end_time)
            count_stmt = count_stmt.where(PlayerEvent.occurred_at <= end_time)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(PlayerEvent.occurred_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total