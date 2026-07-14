from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

import structlog

from app.domain.models import Vote

logger = structlog.get_logger()


class AnomalyType(str, Enum):
    FREQUENCY = "frequency"
    DEVICE = "device"
    WEIGHT = "weight"
    TIME_DISTRIBUTION = "time_distribution"
    SUSPICIOUS_PATTERN = "suspicious_pattern"


class AnomalySeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(slots=True)
class AnomalyDetectionResult:
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    description: str
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AnomalyDetectionConfig:
    frequency_window_seconds: int = 300
    frequency_threshold: int = 3
    device_multi_player_threshold: int = 2
    weight_high_threshold: float = 8.0
    weight_critical_threshold: float = 9.5
    time_window_seconds: int = 60
    time_surge_threshold: int = 10


class AnomalyDetector:
    def __init__(self, config: AnomalyDetectionConfig) -> None:
        self.config = config
        self._log = logger.bind(component="anomaly_detector")

    async def detect_vote_anomalies(
        self,
        *,
        vote_cycle_id: uuid.UUID,
        player_id: uuid.UUID,
        candidate_id: uuid.UUID,
        weight: float,
        device_fingerprint_hash: str,
        recent_votes: list[Vote],
        recent_same_device_votes: list[Vote],
        cycle_vote_count: int,
    ) -> list[AnomalyDetectionResult]:
        results: list[AnomalyDetectionResult] = []

        now = datetime.now(timezone.utc)

        frequency_result = self._check_frequency(
            player_id=player_id,
            recent_votes=recent_votes,
            now=now,
        )
        if frequency_result:
            results.append(frequency_result)

        device_result = self._check_device(
            device_fingerprint_hash=device_fingerprint_hash,
            player_id=player_id,
            recent_same_device_votes=recent_same_device_votes,
        )
        if device_result:
            results.append(device_result)

        weight_result = self._check_weight(
            player_id=player_id,
            weight=weight,
        )
        if weight_result:
            results.append(weight_result)

        time_result = self._check_time_distribution(
            vote_cycle_id=vote_cycle_id,
            cycle_vote_count=cycle_vote_count,
        )
        if time_result:
            results.append(time_result)

        if results:
            self._log.info(
                "anomalies_detected",
                vote_cycle_id=str(vote_cycle_id),
                player_id=str(player_id),
                anomaly_count=len(results),
                anomaly_types=[r.anomaly_type.value for r in results],
            )

        return results

    def _check_frequency(
        self,
        *,
        player_id: uuid.UUID,
        recent_votes: list[Vote],
        now: datetime,
    ) -> AnomalyDetectionResult | None:
        window_start = now - timedelta(seconds=self.config.frequency_window_seconds)

        def _is_aware(dt: datetime) -> bool:
            return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None

        def _to_aware(dt: datetime | int | float | str) -> datetime:
            if isinstance(dt, datetime):
                if _is_aware(dt):
                    return dt
                return dt.replace(tzinfo=timezone.utc)
            if isinstance(dt, (int, float)):
                return datetime.fromtimestamp(dt, tz=timezone.utc)
            if isinstance(dt, str):
                try:
                    parsed = datetime.fromisoformat(dt)
                    if _is_aware(parsed):
                        return parsed
                    return parsed.replace(tzinfo=timezone.utc)
                except ValueError:
                    return datetime.now(timezone.utc)
            return datetime.now(timezone.utc)

        count = sum(
            1
            for vote in recent_votes
            if vote.player_id == player_id and _to_aware(vote.created_at) >= window_start
        )

        if count >= self.config.frequency_threshold:
            return AnomalyDetectionResult(
                anomaly_type=AnomalyType.FREQUENCY,
                severity=AnomalySeverity.HIGH,
                description=f"玩家在 {self.config.frequency_window_seconds} 秒内投票 {count} 次，超过阈值 {self.config.frequency_threshold}",
                detail={
                    "player_id": str(player_id),
                    "vote_count": count,
                    "window_seconds": self.config.frequency_window_seconds,
                    "threshold": self.config.frequency_threshold,
                },
            )

        return None

    def _check_device(
        self,
        *,
        device_fingerprint_hash: str,
        player_id: uuid.UUID,
        recent_same_device_votes: list[Vote],
    ) -> AnomalyDetectionResult | None:
        unique_players = {vote.player_id for vote in recent_same_device_votes}
        unique_players.add(player_id)

        player_count = len(unique_players)

        if player_count > self.config.device_multi_player_threshold:
            severity = AnomalySeverity.MEDIUM
            if player_count >= self.config.device_multi_player_threshold * 2:
                severity = AnomalySeverity.HIGH

            return AnomalyDetectionResult(
                anomaly_type=AnomalyType.DEVICE,
                severity=severity,
                description=f"同一设备指纹关联 {player_count} 个不同玩家，超过阈值 {self.config.device_multi_player_threshold}",
                detail={
                    "device_fingerprint_hash": device_fingerprint_hash,
                    "player_count": player_count,
                    "player_ids": [str(p) for p in unique_players],
                    "threshold": self.config.device_multi_player_threshold,
                },
            )

        return None

    def _check_weight(
        self,
        *,
        player_id: uuid.UUID,
        weight: float,
    ) -> AnomalyDetectionResult | None:
        if weight >= self.config.weight_critical_threshold:
            return AnomalyDetectionResult(
                anomaly_type=AnomalyType.WEIGHT,
                severity=AnomalySeverity.CRITICAL,
                description=f"投票权重 {weight} 达到严重异常级别，超过阈值 {self.config.weight_critical_threshold}",
                detail={
                    "player_id": str(player_id),
                    "weight": weight,
                    "threshold": self.config.weight_critical_threshold,
                },
            )

        if weight >= self.config.weight_high_threshold:
            return AnomalyDetectionResult(
                anomaly_type=AnomalyType.WEIGHT,
                severity=AnomalySeverity.HIGH,
                description=f"投票权重 {weight} 异常偏高，超过阈值 {self.config.weight_high_threshold}",
                detail={
                    "player_id": str(player_id),
                    "weight": weight,
                    "threshold": self.config.weight_high_threshold,
                },
            )

        return None

    def _check_time_distribution(
        self,
        *,
        vote_cycle_id: uuid.UUID,
        cycle_vote_count: int,
    ) -> AnomalyDetectionResult | None:
        if cycle_vote_count >= self.config.time_surge_threshold:
            return AnomalyDetectionResult(
                anomaly_type=AnomalyType.TIME_DISTRIBUTION,
                severity=AnomalySeverity.MEDIUM,
                description=f"投票周期在 {self.config.time_window_seconds} 秒内收到 {cycle_vote_count} 票，超过激增阈值 {self.config.time_surge_threshold}",
                detail={
                    "vote_cycle_id": str(vote_cycle_id),
                    "vote_count": cycle_vote_count,
                    "window_seconds": self.config.time_window_seconds,
                    "threshold": self.config.time_surge_threshold,
                },
            )

        return None
