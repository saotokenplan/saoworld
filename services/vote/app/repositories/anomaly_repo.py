import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Vote, VoteAnomaly


class AnomalyRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_anomaly(
        self,
        *,
        vote_cycle_id: uuid.UUID,
        player_id: uuid.UUID,
        vote_id: uuid.UUID | None,
        anomaly_type: str,
        severity: str,
        description: str,
        detail: dict[str, Any] | None = None,
        detected_at: datetime,
    ) -> VoteAnomaly:
        anomaly = VoteAnomaly(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            vote_id=vote_id,
            anomaly_type=anomaly_type,
            severity=severity,
            description=description,
            detail_jsonb=detail,
            detected_at=detected_at,
        )
        self.db.add(anomaly)
        await self.db.flush()
        return anomaly

    async def get_anomaly_by_id(self, anomaly_id: uuid.UUID) -> VoteAnomaly | None:
        stmt: Select[tuple[VoteAnomaly]] = select(VoteAnomaly).where(
            VoteAnomaly.anomaly_id == anomaly_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_anomalies(
        self,
        *,
        vote_cycle_id: uuid.UUID | None = None,
        player_id: uuid.UUID | None = None,
        anomaly_type: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[VoteAnomaly], int]:
        count_stmt = select(sa_func.count(VoteAnomaly.anomaly_id))

        if vote_cycle_id is not None:
            count_stmt = count_stmt.where(VoteAnomaly.vote_cycle_id == vote_cycle_id)
        if player_id is not None:
            count_stmt = count_stmt.where(VoteAnomaly.player_id == player_id)
        if anomaly_type is not None:
            count_stmt = count_stmt.where(VoteAnomaly.anomaly_type == anomaly_type)
        if severity is not None:
            count_stmt = count_stmt.where(VoteAnomaly.severity == severity)
        if status is not None:
            count_stmt = count_stmt.where(VoteAnomaly.status == status)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[VoteAnomaly]] = select(VoteAnomaly)

        if vote_cycle_id is not None:
            stmt = stmt.where(VoteAnomaly.vote_cycle_id == vote_cycle_id)
        if player_id is not None:
            stmt = stmt.where(VoteAnomaly.player_id == player_id)
        if anomaly_type is not None:
            stmt = stmt.where(VoteAnomaly.anomaly_type == anomaly_type)
        if severity is not None:
            stmt = stmt.where(VoteAnomaly.severity == severity)
        if status is not None:
            stmt = stmt.where(VoteAnomaly.status == status)

        stmt = stmt.order_by(VoteAnomaly.detected_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        anomalies = list(result.scalars().all())

        return anomalies, total

    async def update_anomaly_status(
        self,
        anomaly_id: uuid.UUID,
        status: str,
        resolver_id: str | None = None,
    ) -> VoteAnomaly | None:
        stmt: Select[tuple[VoteAnomaly]] = select(VoteAnomaly).where(
            VoteAnomaly.anomaly_id == anomaly_id
        )
        result = await self.db.execute(stmt)
        anomaly = result.scalar_one_or_none()
        if anomaly is None:
            return None

        anomaly.status = status
        if resolver_id is not None:
            anomaly.resolver_id = resolver_id

        if status in ("resolved", "false_positive"):
            anomaly.resolved_at = datetime.now(timezone.utc)

        await self.db.flush()
        return anomaly

    async def get_anomaly_stats(
        self,
        *,
        vote_cycle_id: uuid.UUID | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        base_conditions = []
        if vote_cycle_id is not None:
            base_conditions.append(VoteAnomaly.vote_cycle_id == vote_cycle_id)
        if start_time is not None:
            base_conditions.append(VoteAnomaly.detected_at >= start_time)
        if end_time is not None:
            base_conditions.append(VoteAnomaly.detected_at < end_time)

        total_stmt = select(sa_func.count(VoteAnomaly.anomaly_id))
        for condition in base_conditions:
            total_stmt = total_stmt.where(condition)
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar_one()

        by_type_stmt = select(
            VoteAnomaly.anomaly_type,
            sa_func.count(VoteAnomaly.anomaly_id).label("count"),
        )
        for condition in base_conditions:
            by_type_stmt = by_type_stmt.where(condition)
        by_type_stmt = by_type_stmt.group_by(VoteAnomaly.anomaly_type)
        by_type_result = await self.db.execute(by_type_stmt)
        by_type = {row.anomaly_type: row.count for row in by_type_result.all()}

        by_severity_stmt = select(
            VoteAnomaly.severity,
            sa_func.count(VoteAnomaly.anomaly_id).label("count"),
        )
        for condition in base_conditions:
            by_severity_stmt = by_severity_stmt.where(condition)
        by_severity_stmt = by_severity_stmt.group_by(VoteAnomaly.severity)
        by_severity_result = await self.db.execute(by_severity_stmt)
        by_severity = {row.severity: row.count for row in by_severity_result.all()}

        by_status_stmt = select(
            VoteAnomaly.status,
            sa_func.count(VoteAnomaly.anomaly_id).label("count"),
        )
        for condition in base_conditions:
            by_status_stmt = by_status_stmt.where(condition)
        by_status_stmt = by_status_stmt.group_by(VoteAnomaly.status)
        by_status_result = await self.db.execute(by_status_stmt)
        by_status = {row.status: row.count for row in by_status_result.all()}

        return {
            "total": total,
            "by_type": by_type,
            "by_severity": by_severity,
            "by_status": by_status,
        }

    async def count_recent_by_player(self, player_id: uuid.UUID, since: datetime) -> int:
        stmt = select(sa_func.count(VoteAnomaly.anomaly_id)).where(
            VoteAnomaly.player_id == player_id,
            VoteAnomaly.detected_at >= since,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def count_recent_by_device(self, device_fingerprint_hash: str, since: datetime) -> int:
        stmt = (
            select(sa_func.count(VoteAnomaly.anomaly_id))
            .join(Vote, VoteAnomaly.vote_id == Vote.vote_id)
            .where(
                Vote.device_fingerprint_hash == device_fingerprint_hash,
                VoteAnomaly.detected_at >= since,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
