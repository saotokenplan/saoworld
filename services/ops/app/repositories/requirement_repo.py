import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Requirement


class RequirementRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_requirements(
        self,
        insight_id: uuid.UUID | None = None,
        status: str | None = None,
        priority: str | None = None,
        target_scope: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Requirement], int]:
        stmt = select(Requirement)
        count_stmt = select(sa_func.count(Requirement.requirement_id))

        if insight_id:
            stmt = stmt.where(Requirement.insight_id == insight_id)
            count_stmt = count_stmt.where(Requirement.insight_id == insight_id)

        if status:
            stmt = stmt.where(Requirement.status == status)
            count_stmt = count_stmt.where(Requirement.status == status)

        if priority:
            stmt = stmt.where(Requirement.priority == priority)
            count_stmt = count_stmt.where(Requirement.priority == priority)

        if target_scope:
            stmt = stmt.where(Requirement.target_scope == target_scope)
            count_stmt = count_stmt.where(Requirement.target_scope == target_scope)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Requirement.priority.desc(), Requirement.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def get_requirement_by_id(self, requirement_id: uuid.UUID) -> Requirement | None:
        stmt: Select[tuple[Requirement]] = select(Requirement).where(Requirement.requirement_id == requirement_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_requirement(
        self,
        *,
        insight_id: uuid.UUID | None = None,
        title: str,
        description: str,
        status: str = "pending_review",
        priority: str = "medium",
        target_scope: str = "content",
        estimated_effort: int = 1,
        acceptance_criteria_jsonb: dict | None = None,
        related_content_jsonb: dict | None = None,
        generated_by: str = "system",
        trace_id: str | None = None,
        schema_version: int = 1,
    ) -> Requirement:
        requirement = Requirement(
            requirement_id=uuid.uuid4(),
            insight_id=insight_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            target_scope=target_scope,
            estimated_effort=estimated_effort,
            acceptance_criteria_jsonb=acceptance_criteria_jsonb,
            related_content_jsonb=related_content_jsonb,
            generated_by=generated_by,
            trace_id=trace_id,
            schema_version=schema_version,
        )
        self.db.add(requirement)
        await self.db.flush()
        return requirement

    async def approve_requirement(
        self,
        requirement_id: uuid.UUID,
        approved_by: str,
    ) -> Requirement | None:
        requirement = await self.get_requirement_by_id(requirement_id)
        if requirement is None:
            return None
        requirement.status = "approved"
        requirement.approved_by = approved_by
        requirement.approved_at = datetime.now()
        await self.db.flush()
        return requirement

    async def update_requirement(
        self,
        requirement_id: uuid.UUID,
        *,
        status: str | None = None,
        priority: str | None = None,
        title: str | None = None,
        description: str | None = None,
    ) -> Requirement | None:
        requirement = await self.get_requirement_by_id(requirement_id)
        if requirement is None:
            return None
        if status is not None:
            requirement.status = status
        if priority is not None:
            requirement.priority = priority
        if title is not None:
            requirement.title = title
        if description is not None:
            requirement.description = description
        await self.db.flush()
        return requirement

    async def delete_requirement(self, requirement_id: uuid.UUID) -> bool:
        requirement = await self.get_requirement_by_id(requirement_id)
        if requirement is None:
            return False
        await self.db.delete(requirement)
        await self.db.flush()
        return True
