import uuid
from typing import Any, Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import OpsDashboard


class DashboardRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_dashboard(self, metrics_jsonb: dict[str, Any]) -> OpsDashboard:
        dashboard = OpsDashboard(
            dashboard_id=uuid.uuid4(),
            metrics_jsonb=metrics_jsonb,
        )
        self.db.add(dashboard)
        await self.db.flush()
        return dashboard

    async def get_latest_dashboard(self) -> OpsDashboard | None:
        stmt: Select[tuple[OpsDashboard]] = (
            select(OpsDashboard)
            .order_by(OpsDashboard.generated_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_dashboard_history(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[OpsDashboard], int]:
        count_stmt = select(sa_func.count(OpsDashboard.dashboard_id))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[OpsDashboard]] = (
            select(OpsDashboard)
            .order_by(OpsDashboard.generated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total
