import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    AnalyticsReport,
    PlayerMetricsDaily,
    QuestMetricsDaily,
    RegionMetricsDaily,
    VoteMetricsDaily,
)


class AnalyticsRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_player_metrics(
        self,
        player_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> tuple[Sequence[PlayerMetricsDaily], int]:
        stmt = select(PlayerMetricsDaily)
        count_stmt = select(sa_func.count(PlayerMetricsDaily.metric_id))

        if player_id:
            stmt = stmt.where(PlayerMetricsDaily.player_id == player_id)
            count_stmt = count_stmt.where(PlayerMetricsDaily.player_id == player_id)

        if start_date:
            stmt = stmt.where(PlayerMetricsDaily.stat_date >= start_date)
            count_stmt = count_stmt.where(PlayerMetricsDaily.stat_date >= start_date)
        if end_date:
            stmt = stmt.where(PlayerMetricsDaily.stat_date <= end_date)
            count_stmt = count_stmt.where(PlayerMetricsDaily.stat_date <= end_date)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(PlayerMetricsDaily.stat_date.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def upsert_player_metrics(
        self,
        *,
        player_id: str,
        stat_date: datetime,
        total_session_seconds: int = 0,
        regions_visited: int = 0,
        quests_completed: int = 0,
        votes_submitted: int = 0,
        npcs_interacted: int = 0,
        events_count: int = 0,
        detail_jsonb: dict | None = None,
    ) -> PlayerMetricsDaily:
        stmt = select(PlayerMetricsDaily).where(
            PlayerMetricsDaily.player_id == player_id,
            PlayerMetricsDaily.stat_date == stat_date,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.total_session_seconds = total_session_seconds
            existing.regions_visited = regions_visited
            existing.quests_completed = quests_completed
            existing.votes_submitted = votes_submitted
            existing.npcs_interacted = npcs_interacted
            existing.events_count = events_count
            existing.detail_jsonb = detail_jsonb
            await self.db.flush()
            return existing

        metric = PlayerMetricsDaily(
            metric_id=uuid.uuid4(),
            player_id=player_id,
            stat_date=stat_date,
            total_session_seconds=total_session_seconds,
            regions_visited=regions_visited,
            quests_completed=quests_completed,
            votes_submitted=votes_submitted,
            npcs_interacted=npcs_interacted,
            events_count=events_count,
            detail_jsonb=detail_jsonb,
        )
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def get_region_metrics(
        self,
        region_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> tuple[Sequence[RegionMetricsDaily], int]:
        stmt = select(RegionMetricsDaily)
        count_stmt = select(sa_func.count(RegionMetricsDaily.metric_id))

        if region_id:
            stmt = stmt.where(RegionMetricsDaily.region_id == region_id)
            count_stmt = count_stmt.where(RegionMetricsDaily.region_id == region_id)
        if start_date:
            stmt = stmt.where(RegionMetricsDaily.stat_date >= start_date)
            count_stmt = count_stmt.where(RegionMetricsDaily.stat_date >= start_date)
        if end_date:
            stmt = stmt.where(RegionMetricsDaily.stat_date <= end_date)
            count_stmt = count_stmt.where(RegionMetricsDaily.stat_date <= end_date)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(RegionMetricsDaily.stat_date.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def upsert_region_metrics(
        self,
        *,
        region_id: str,
        stat_date: datetime,
        unique_players: int = 0,
        total_visits: int = 0,
        total_duration_seconds: int = 0,
        quests_started: int = 0,
        quests_completed: int = 0,
        events_count: int = 0,
        detail_jsonb: dict | None = None,
    ) -> RegionMetricsDaily:
        stmt = select(RegionMetricsDaily).where(
            RegionMetricsDaily.region_id == region_id,
            RegionMetricsDaily.stat_date == stat_date,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.unique_players = unique_players
            existing.total_visits = total_visits
            existing.total_duration_seconds = total_duration_seconds
            existing.quests_started = quests_started
            existing.quests_completed = quests_completed
            existing.events_count = events_count
            existing.detail_jsonb = detail_jsonb
            await self.db.flush()
            return existing

        metric = RegionMetricsDaily(
            metric_id=uuid.uuid4(),
            region_id=region_id,
            stat_date=stat_date,
            unique_players=unique_players,
            total_visits=total_visits,
            total_duration_seconds=total_duration_seconds,
            quests_started=quests_started,
            quests_completed=quests_completed,
            events_count=events_count,
            detail_jsonb=detail_jsonb,
        )
        self.db.add(metric)
        await self.db.flush()
        return metric

    async def get_quest_metrics(
        self,
        quest_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> tuple[Sequence[QuestMetricsDaily], int]:
        stmt = select(QuestMetricsDaily)
        count_stmt = select(sa_func.count(QuestMetricsDaily.metric_id))

        if quest_id:
            stmt = stmt.where(QuestMetricsDaily.quest_id == quest_id)
            count_stmt = count_stmt.where(QuestMetricsDaily.quest_id == quest_id)
        if start_date:
            stmt = stmt.where(QuestMetricsDaily.stat_date >= start_date)
            count_stmt = count_stmt.where(QuestMetricsDaily.stat_date >= start_date)
        if end_date:
            stmt = stmt.where(QuestMetricsDaily.stat_date <= end_date)
            count_stmt = count_stmt.where(QuestMetricsDaily.stat_date <= end_date)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(QuestMetricsDaily.stat_date.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def get_vote_metrics(
        self,
        vote_cycle_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 30,
        offset: int = 0,
    ) -> tuple[Sequence[VoteMetricsDaily], int]:
        stmt = select(VoteMetricsDaily)
        count_stmt = select(sa_func.count(VoteMetricsDaily.metric_id))

        if vote_cycle_id:
            stmt = stmt.where(VoteMetricsDaily.vote_cycle_id == vote_cycle_id)
            count_stmt = count_stmt.where(VoteMetricsDaily.vote_cycle_id == vote_cycle_id)
        if start_date:
            stmt = stmt.where(VoteMetricsDaily.stat_date >= start_date)
            count_stmt = count_stmt.where(VoteMetricsDaily.stat_date >= start_date)
        if end_date:
            stmt = stmt.where(VoteMetricsDaily.stat_date <= end_date)
            count_stmt = count_stmt.where(VoteMetricsDaily.stat_date <= end_date)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(VoteMetricsDaily.stat_date.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def get_reports(
        self,
        report_type: str | None = None,
        status: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[AnalyticsReport], int]:
        stmt = select(AnalyticsReport)
        count_stmt = select(sa_func.count(AnalyticsReport.report_id))

        if report_type:
            stmt = stmt.where(AnalyticsReport.report_type == report_type)
            count_stmt = count_stmt.where(AnalyticsReport.report_type == report_type)
        if status:
            stmt = stmt.where(AnalyticsReport.status == status)
            count_stmt = count_stmt.where(AnalyticsReport.status == status)
        if start_date:
            stmt = stmt.where(AnalyticsReport.period_start >= start_date)
            count_stmt = count_stmt.where(AnalyticsReport.period_start >= start_date)
        if end_date:
            stmt = stmt.where(AnalyticsReport.period_end <= end_date)
            count_stmt = count_stmt.where(AnalyticsReport.period_end <= end_date)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(AnalyticsReport.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def get_report_by_id(self, report_id: uuid.UUID) -> AnalyticsReport | None:
        stmt: Select[tuple[AnalyticsReport]] = select(AnalyticsReport).where(
            AnalyticsReport.report_id == report_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_report(
        self,
        *,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        status: str = "pending",
        summary_jsonb: dict | None = None,
        detail_jsonb: dict | None = None,
        generated_by: str = "system",
        trace_id: str | None = None,
        schema_version: int = 1,
    ) -> AnalyticsReport:
        report = AnalyticsReport(
            report_id=uuid.uuid4(),
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            status=status,
            summary_jsonb=summary_jsonb,
            detail_jsonb=detail_jsonb,
            generated_by=generated_by,
            trace_id=trace_id,
            schema_version=schema_version,
        )
        self.db.add(report)
        await self.db.flush()
        return report

    async def update_report_status(
        self,
        report_id: uuid.UUID,
        status: str,
        summary_jsonb: dict | None = None,
        detail_jsonb: dict | None = None,
    ) -> AnalyticsReport | None:
        report = await self.get_report_by_id(report_id)
        if report is None:
            return None
        report.status = status
        if summary_jsonb is not None:
            report.summary_jsonb = summary_jsonb
        if detail_jsonb is not None:
            report.detail_jsonb = detail_jsonb
        await self.db.flush()
        return report
