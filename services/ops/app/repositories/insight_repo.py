import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Insight


class InsightRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_insights(
        self,
        category: str | None = None,
        min_confidence: str | None = None,
        min_impact: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Insight], int]:
        stmt = select(Insight)
        count_stmt = select(sa_func.count(Insight.insight_id))

        if category:
            stmt = stmt.where(Insight.category == category)
            count_stmt = count_stmt.where(Insight.category == category)

        if min_confidence:
            confidence_order = {"low": 0, "medium": 1, "high": 2}
            if min_confidence in confidence_order:
                min_value = confidence_order[min_confidence]
                for key, value in confidence_order.items():
                    if value >= min_value:
                        stmt = stmt.where(Insight.confidence == key)
                        count_stmt = count_stmt.where(Insight.confidence == key)

        if min_impact:
            impact_order = {"low": 0, "medium": 1, "high": 2}
            if min_impact in impact_order:
                min_value = impact_order[min_impact]
                for key, value in impact_order.items():
                    if value >= min_value:
                        stmt = stmt.where(Insight.impact == key)
                        count_stmt = count_stmt.where(Insight.impact == key)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(Insight.quality_score.desc(), Insight.discovered_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def get_insight_by_id(self, insight_id: uuid.UUID) -> Insight | None:
        stmt: Select[tuple[Insight]] = select(Insight).where(Insight.insight_id == insight_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_insight(
        self,
        *,
        category: str,
        summary: str,
        confidence: str = "medium",
        impact: str = "medium",
        novelty: str = "medium",
        feasibility: str = "medium",
        quality_score: float = 0.0,
        source_report_id: uuid.UUID | None = None,
        source_data_jsonb: dict | None = None,
        tags: list[str] | None = None,
        discovered_at: datetime | None = None,
    ) -> Insight:
        insight = Insight(
            insight_id=uuid.uuid4(),
            category=category,
            summary=summary,
            confidence=confidence,
            impact=impact,
            novelty=novelty,
            feasibility=feasibility,
            quality_score=quality_score,
            source_report_id=source_report_id,
            source_data_jsonb=source_data_jsonb,
            tags=tags,
            discovered_at=discovered_at or datetime.now(),
        )
        self.db.add(insight)
        await self.db.flush()
        return insight

    async def delete_insight(self, insight_id: uuid.UUID) -> bool:
        insight = await self.get_insight_by_id(insight_id)
        if insight is None:
            return False
        await self.db.delete(insight)
        await self.db.flush()
        return True
