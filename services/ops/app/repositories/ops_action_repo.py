import uuid
from typing import Any, Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import OpsAction


class OpsActionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_action(
        self,
        *,
        action_type: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        operator_id: str,
        operator_role: str,
        status: str = "completed",
        payload_jsonb: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> OpsAction:
        action = OpsAction(
            action_id=uuid.uuid4(),
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            operator_id=operator_id,
            operator_role=operator_role,
            status=status,
            payload_jsonb=payload_jsonb,
            trace_id=trace_id,
        )
        self.db.add(action)
        await self.db.flush()
        return action

    async def get_action_by_id(self, action_id: uuid.UUID) -> OpsAction | None:
        stmt: Select[tuple[OpsAction]] = select(OpsAction).where(
            OpsAction.action_id == action_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_actions(
        self,
        action_type: str | None = None,
        status: str | None = None,
        operator_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[OpsAction], int]:
        stmt = select(OpsAction)
        count_stmt = select(sa_func.count(OpsAction.action_id))

        if action_type:
            stmt = stmt.where(OpsAction.action_type == action_type)
            count_stmt = count_stmt.where(OpsAction.action_type == action_type)

        if status:
            stmt = stmt.where(OpsAction.status == status)
            count_stmt = count_stmt.where(OpsAction.status == status)

        if operator_id:
            stmt = stmt.where(OpsAction.operator_id == operator_id)
            count_stmt = count_stmt.where(OpsAction.operator_id == operator_id)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(OpsAction.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total
