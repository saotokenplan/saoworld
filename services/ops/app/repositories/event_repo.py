import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import and_, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import OpsEvent


class EventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_event(
        self,
        *,
        event_name: str,
        event_type: str,
        start_at: datetime,
        end_at: datetime,
        created_by: str,
        target_scope: str = "all",
        target_scope_jsonb: dict | None = None,
        reward_config_jsonb: dict | None = None,
        multiplier_config_jsonb: dict | None = None,
        description: str | None = None,
        rules_jsonb: dict | None = None,
        status: str = "draft",
    ) -> OpsEvent:
        event = OpsEvent(
            event_id=uuid.uuid4(),
            event_name=event_name,
            event_type=event_type,
            status=status,
            start_at=start_at,
            end_at=end_at,
            target_scope=target_scope,
            target_scope_jsonb=target_scope_jsonb,
            reward_config_jsonb=reward_config_jsonb,
            multiplier_config_jsonb=multiplier_config_jsonb,
            description=description,
            rules_jsonb=rules_jsonb,
            created_by=created_by,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_event_by_id(self, event_id: uuid.UUID) -> OpsEvent | None:
        stmt = select(OpsEvent).where(OpsEvent.event_id == event_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_event_by_name(self, event_name: str) -> OpsEvent | None:
        stmt = select(OpsEvent).where(OpsEvent.event_name == event_name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_events(
        self,
        *,
        event_type: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[OpsEvent], int]:
        stmt = select(OpsEvent)
        count_stmt = select(sa_func.count(OpsEvent.event_id))

        if event_type:
            stmt = stmt.where(OpsEvent.event_type == event_type)
            count_stmt = count_stmt.where(OpsEvent.event_type == event_type)

        if status:
            stmt = stmt.where(OpsEvent.status == status)
            count_stmt = count_stmt.where(OpsEvent.status == status)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(OpsEvent.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def update_event(
        self,
        event_id: uuid.UUID,
        *,
        event_name: str | None = None,
        event_type: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        target_scope: str | None = None,
        target_scope_jsonb: dict | None = None,
        reward_config_jsonb: dict | None = None,
        multiplier_config_jsonb: dict | None = None,
        description: str | None = None,
        rules_jsonb: dict | None = None,
    ) -> OpsEvent | None:
        event = await self.get_event_by_id(event_id)
        if event is None:
            return None

        if event_name is not None:
            event.event_name = event_name
        if event_type is not None:
            event.event_type = event_type
        if start_at is not None:
            event.start_at = start_at
        if end_at is not None:
            event.end_at = end_at
        if target_scope is not None:
            event.target_scope = target_scope
        if target_scope_jsonb is not None:
            event.target_scope_jsonb = target_scope_jsonb
        if reward_config_jsonb is not None:
            event.reward_config_jsonb = reward_config_jsonb
        if multiplier_config_jsonb is not None:
            event.multiplier_config_jsonb = multiplier_config_jsonb
        if description is not None:
            event.description = description
        if rules_jsonb is not None:
            event.rules_jsonb = rules_jsonb

        event.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def update_event_status(
        self,
        event_id: uuid.UUID,
        new_status: str,
    ) -> OpsEvent | None:
        event = await self.get_event_by_id(event_id)
        if event is None:
            return None
        event.status = new_status
        event.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def delete_event(self, event_id: uuid.UUID) -> bool:
        event = await self.get_event_by_id(event_id)
        if event is None:
            return False
        event.status = "archived"
        event.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def get_active_events(
        self,
        *,
        at_time: datetime | None = None,
    ) -> Sequence[OpsEvent]:
        if at_time is None:
            at_time = datetime.now(timezone.utc)

        stmt = select(OpsEvent).where(
            and_(
                OpsEvent.status == "active",
                OpsEvent.start_at <= at_time,
                OpsEvent.end_at >= at_time,
            )
        ).order_by(OpsEvent.start_at.asc())

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def check_event_overlap(
        self,
        *,
        start_at: datetime,
        end_at: datetime,
        exclude_event_id: uuid.UUID | None = None,
        event_type: str | None = None,
    ) -> Sequence[OpsEvent]:
        stmt = select(OpsEvent).where(
            and_(
                OpsEvent.status.in_(["draft", "active", "paused"]),
                OpsEvent.start_at < end_at,
                OpsEvent.end_at > start_at,
            )
        )

        if exclude_event_id is not None:
            stmt = stmt.where(OpsEvent.event_id != exclude_event_id)

        if event_type is not None:
            stmt = stmt.where(OpsEvent.event_type == event_type)

        result = await self.db.execute(stmt)
        return result.scalars().all()
