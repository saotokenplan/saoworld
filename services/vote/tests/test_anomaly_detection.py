import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.core.anomaly_detector import (
    AnomalyDetectionConfig,
    AnomalyDetector,
    AnomalySeverity,
    AnomalyType,
)
from app.core.auth import create_test_token
from app.core.config import settings
from app.core.errors import VoteErrorCodes
from app.domain.models import Vote, VoteAnomaly, VoteCandidate, VoteCycle
from app.schemas.auth import Role


def _ops_headers(ops_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {ops_token}"}


def _make_vote(
    *,
    vote_id: uuid.UUID | None = None,
    vote_cycle_id: uuid.UUID,
    player_id: uuid.UUID,
    candidate_id: uuid.UUID,
    weight: float = 1.0,
    device_fingerprint_hash: str = "test_device",
    created_at: datetime | None = None,
) -> Vote:
    return Vote(
        vote_id=vote_id or uuid.uuid4(),
        vote_cycle_id=vote_cycle_id,
        player_id=player_id,
        candidate_id=candidate_id,
        weight=weight,
        device_fingerprint_hash=device_fingerprint_hash,
        idempotency_key=f"test_{uuid.uuid4().hex[:8]}",
        created_at=created_at or datetime.now(timezone.utc),
    )


@pytest.fixture
def detector() -> AnomalyDetector:
    config = AnomalyDetectionConfig(
        frequency_window_seconds=300,
        frequency_threshold=3,
        device_multi_player_threshold=2,
        weight_high_threshold=8.0,
        weight_critical_threshold=9.5,
        time_window_seconds=60,
        time_surge_threshold=10,
    )
    return AnomalyDetector(config)


# ============================================================
# 1. 异常检测引擎单元测试
# ============================================================


@pytest.mark.asyncio
async def test_frequency_detection(detector: AnomalyDetector):
    vote_cycle_id = uuid.uuid4()
    player_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    recent_votes = [
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            candidate_id=candidate_id,
            created_at=now - timedelta(seconds=10),
        ),
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            candidate_id=candidate_id,
            created_at=now - timedelta(seconds=30),
        ),
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            candidate_id=candidate_id,
            created_at=now - timedelta(seconds=60),
        ),
    ]

    results = await detector.detect_vote_anomalies(
        vote_cycle_id=vote_cycle_id,
        player_id=player_id,
        candidate_id=candidate_id,
        weight=1.0,
        device_fingerprint_hash="device_hash",
        recent_votes=recent_votes,
        recent_same_device_votes=[],
        cycle_vote_count=0,
    )

    frequency_results = [r for r in results if r.anomaly_type == AnomalyType.FREQUENCY]
    assert len(frequency_results) == 1
    assert frequency_results[0].severity == AnomalySeverity.HIGH
    assert frequency_results[0].detail["vote_count"] == 3
    assert frequency_results[0].detail["window_seconds"] == 300
    assert frequency_results[0].detail["threshold"] == 3


@pytest.mark.asyncio
async def test_device_detection(detector: AnomalyDetector):
    vote_cycle_id = uuid.uuid4()
    player_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    device_hash = "suspicious_device_abc"

    other_player_1 = uuid.uuid4()
    other_player_2 = uuid.uuid4()
    other_player_3 = uuid.uuid4()

    recent_same_device_votes = [
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=other_player_1,
            candidate_id=candidate_id,
            device_fingerprint_hash=device_hash,
        ),
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=other_player_2,
            candidate_id=candidate_id,
            device_fingerprint_hash=device_hash,
        ),
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=other_player_3,
            candidate_id=candidate_id,
            device_fingerprint_hash=device_hash,
        ),
    ]

    results = await detector.detect_vote_anomalies(
        vote_cycle_id=vote_cycle_id,
        player_id=player_id,
        candidate_id=candidate_id,
        weight=1.0,
        device_fingerprint_hash=device_hash,
        recent_votes=[],
        recent_same_device_votes=recent_same_device_votes,
        cycle_vote_count=0,
    )

    device_results = [r for r in results if r.anomaly_type == AnomalyType.DEVICE]
    assert len(device_results) == 1
    assert device_results[0].severity == AnomalySeverity.HIGH
    assert device_results[0].detail["player_count"] == 4
    assert device_results[0].detail["device_fingerprint_hash"] == device_hash
    assert device_results[0].detail["threshold"] == 2


@pytest.mark.asyncio
async def test_weight_detection_high(detector: AnomalyDetector):
    vote_cycle_id = uuid.uuid4()
    player_id = uuid.uuid4()
    candidate_id = uuid.uuid4()

    results = await detector.detect_vote_anomalies(
        vote_cycle_id=vote_cycle_id,
        player_id=player_id,
        candidate_id=candidate_id,
        weight=8.5,
        device_fingerprint_hash="device_hash",
        recent_votes=[],
        recent_same_device_votes=[],
        cycle_vote_count=0,
    )

    weight_results = [r for r in results if r.anomaly_type == AnomalyType.WEIGHT]
    assert len(weight_results) == 1
    assert weight_results[0].severity == AnomalySeverity.HIGH
    assert weight_results[0].detail["weight"] == 8.5
    assert weight_results[0].detail["threshold"] == 8.0


@pytest.mark.asyncio
async def test_weight_detection_critical(detector: AnomalyDetector):
    vote_cycle_id = uuid.uuid4()
    player_id = uuid.uuid4()
    candidate_id = uuid.uuid4()

    results = await detector.detect_vote_anomalies(
        vote_cycle_id=vote_cycle_id,
        player_id=player_id,
        candidate_id=candidate_id,
        weight=9.8,
        device_fingerprint_hash="device_hash",
        recent_votes=[],
        recent_same_device_votes=[],
        cycle_vote_count=0,
    )

    weight_results = [r for r in results if r.anomaly_type == AnomalyType.WEIGHT]
    assert len(weight_results) == 1
    assert weight_results[0].severity == AnomalySeverity.CRITICAL
    assert weight_results[0].detail["weight"] == 9.8
    assert weight_results[0].detail["threshold"] == 9.5


@pytest.mark.asyncio
async def test_time_distribution_detection(detector: AnomalyDetector):
    vote_cycle_id = uuid.uuid4()
    player_id = uuid.uuid4()
    candidate_id = uuid.uuid4()

    results = await detector.detect_vote_anomalies(
        vote_cycle_id=vote_cycle_id,
        player_id=player_id,
        candidate_id=candidate_id,
        weight=1.0,
        device_fingerprint_hash="device_hash",
        recent_votes=[],
        recent_same_device_votes=[],
        cycle_vote_count=15,
    )

    time_results = [r for r in results if r.anomaly_type == AnomalyType.TIME_DISTRIBUTION]
    assert len(time_results) == 1
    assert time_results[0].severity == AnomalySeverity.MEDIUM
    assert time_results[0].detail["vote_count"] == 15
    assert time_results[0].detail["window_seconds"] == 60
    assert time_results[0].detail["threshold"] == 10


@pytest.mark.asyncio
async def test_no_anomaly_normal_vote(detector: AnomalyDetector):
    vote_cycle_id = uuid.uuid4()
    player_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    recent_votes = [
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            candidate_id=candidate_id,
            created_at=now - timedelta(hours=2),
        ),
    ]

    results = await detector.detect_vote_anomalies(
        vote_cycle_id=vote_cycle_id,
        player_id=player_id,
        candidate_id=candidate_id,
        weight=2.0,
        device_fingerprint_hash="normal_device",
        recent_votes=recent_votes,
        recent_same_device_votes=[],
        cycle_vote_count=3,
    )

    assert len(results) == 0


@pytest.mark.asyncio
async def test_multiple_anomalies(detector: AnomalyDetector):
    vote_cycle_id = uuid.uuid4()
    player_id = uuid.uuid4()
    candidate_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    device_hash = "multi_anomaly_device"

    other_player_1 = uuid.uuid4()
    other_player_2 = uuid.uuid4()

    recent_votes = [
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            candidate_id=candidate_id,
            device_fingerprint_hash=device_hash,
            created_at=now - timedelta(seconds=10),
        ),
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            candidate_id=candidate_id,
            device_fingerprint_hash=device_hash,
            created_at=now - timedelta(seconds=30),
        ),
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            candidate_id=candidate_id,
            device_fingerprint_hash=device_hash,
            created_at=now - timedelta(seconds=60),
        ),
    ]

    recent_same_device_votes = [
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=other_player_1,
            candidate_id=candidate_id,
            device_fingerprint_hash=device_hash,
            created_at=now - timedelta(seconds=20),
        ),
        _make_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=other_player_2,
            candidate_id=candidate_id,
            device_fingerprint_hash=device_hash,
            created_at=now - timedelta(seconds=50),
        ),
    ]

    results = await detector.detect_vote_anomalies(
        vote_cycle_id=vote_cycle_id,
        player_id=player_id,
        candidate_id=candidate_id,
        weight=9.0,
        device_fingerprint_hash=device_hash,
        recent_votes=recent_votes,
        recent_same_device_votes=recent_same_device_votes,
        cycle_vote_count=12,
    )

    anomaly_types = {r.anomaly_type for r in results}
    assert AnomalyType.FREQUENCY in anomaly_types
    assert AnomalyType.DEVICE in anomaly_types
    assert AnomalyType.WEIGHT in anomaly_types
    assert AnomalyType.TIME_DISTRIBUTION in anomaly_types
    assert len(results) == 4


# ============================================================
# 2. 运营异常管理 API 测试（集成测试）
# ============================================================


async def _create_test_anomaly(
    *,
    vote_cycle_id: uuid.UUID,
    player_id: uuid.UUID,
    anomaly_type: str = "frequency",
    severity: str = "high",
    status: str = "detected",
) -> VoteAnomaly:
    from tests.conftest import TestSessionLocal

    from app.repositories.anomaly_repo import AnomalyRepository
    from app.repositories.vote_repo import VoteRepository

    async with TestSessionLocal() as session:
        vote_repo = VoteRepository(session)
        candidates = await vote_repo.get_candidates_for_cycle(vote_cycle_id)
        candidate_id = candidates[0].candidate_id

        vote = await vote_repo.create_vote(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            candidate_id=candidate_id,
            weight=1.0,
            device_fingerprint_hash=f"device_{uuid.uuid4().hex[:8]}",
            idempotency_key=f"test_anomaly_{uuid.uuid4().hex[:12]}",
        )
        vote_id = vote.vote_id

        anomaly_repo = AnomalyRepository(session)
        anomaly = await anomaly_repo.create_anomaly(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            vote_id=vote_id,
            anomaly_type=anomaly_type,
            severity=severity,
            description=f"测试异常记录: {anomaly_type}",
            detail={"test_key": "test_value"},
            detected_at=datetime.now(timezone.utc),
        )
        if status != "detected":
            updated = await anomaly_repo.update_anomaly_status(
                anomaly_id=anomaly.anomaly_id,
                status=status,
                resolver_id="test_resolver",
            )
            anomaly = updated
        await session.commit()
        anomaly_id = anomaly.anomaly_id

    async with TestSessionLocal() as session:
        anomaly_repo = AnomalyRepository(session)
        result = await anomaly_repo.get_anomaly_by_id(anomaly_id)
        return result


@pytest.mark.asyncio
async def test_list_anomalies_empty(
    client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str
):
    response = await client.get(
        f"{settings.api_v1_prefix}/ops/anomalies",
        headers=_ops_headers(ops_token),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["anomalies"] == []
    assert body["meta"]["total"] == 0
    assert body["meta"]["limit"] == 20
    assert body["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_list_anomalies_with_filters(
    client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str
):
    player_1 = uuid.uuid4()
    player_2 = uuid.uuid4()
    player_3 = uuid.uuid4()

    await _create_test_anomaly(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        player_id=player_1,
        anomaly_type="frequency",
        severity="high",
        status="detected",
    )
    await _create_test_anomaly(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        player_id=player_2,
        anomaly_type="weight",
        severity="critical",
        status="detected",
    )
    await _create_test_anomaly(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        player_id=player_3,
        anomaly_type="device",
        severity="medium",
        status="resolved",
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/ops/anomalies",
        headers=_ops_headers(ops_token),
        params={"anomaly_type": "frequency"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert len(body["data"]["anomalies"]) == 1
    assert body["data"]["anomalies"][0]["anomaly_type"] == "frequency"

    response_severity = await client.get(
        f"{settings.api_v1_prefix}/ops/anomalies",
        headers=_ops_headers(ops_token),
        params={"severity": "critical"},
    )
    assert response_severity.status_code == 200
    assert response_severity.json()["meta"]["total"] == 1
    assert response_severity.json()["data"]["anomalies"][0]["severity"] == "critical"

    response_status = await client.get(
        f"{settings.api_v1_prefix}/ops/anomalies",
        headers=_ops_headers(ops_token),
        params={"status": "resolved"},
    )
    assert response_status.status_code == 200
    assert response_status.json()["meta"]["total"] == 1
    assert response_status.json()["data"]["anomalies"][0]["status"] == "resolved"

    response_player = await client.get(
        f"{settings.api_v1_prefix}/ops/anomalies",
        headers=_ops_headers(ops_token),
        params={"player_id": str(player_1)},
    )
    assert response_player.status_code == 200
    assert response_player.json()["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_get_anomaly_by_id(
    client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str
):
    player_id = uuid.uuid4()
    anomaly = await _create_test_anomaly(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        player_id=player_id,
        anomaly_type="frequency",
        severity="high",
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/ops/anomalies/{anomaly.anomaly_id}",
        headers=_ops_headers(ops_token),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["anomaly_id"] == str(anomaly.anomaly_id)
    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["player_id"] == str(player_id)
    assert data["anomaly_type"] == "frequency"
    assert data["severity"] == "high"
    assert data["status"] == "detected"
    assert data["description"] == "测试异常记录: frequency"
    assert data["detail"]["test_key"] == "test_value"
    assert data["detected_at"]
    assert body["request_id"]


@pytest.mark.asyncio
async def test_get_anomaly_not_found(
    client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str
):
    fake_anomaly_id = uuid.uuid4()

    response = await client.get(
        f"{settings.api_v1_prefix}/ops/anomalies/{fake_anomaly_id}",
        headers=_ops_headers(ops_token),
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == VoteErrorCodes.ANOMALY_NOT_FOUND


@pytest.mark.asyncio
async def test_resolve_anomaly(
    client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str
):
    player_id = uuid.uuid4()
    anomaly = await _create_test_anomaly(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        player_id=player_id,
        anomaly_type="frequency",
        severity="high",
    )

    response = await client.patch(
        f"{settings.api_v1_prefix}/ops/anomalies/{anomaly.anomaly_id}/resolve",
        headers=_ops_headers(ops_token),
        json={"reason": "人工审核确认异常已处理"},
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["anomaly_id"] == str(anomaly.anomaly_id)
    assert data["status"] == "resolved"
    assert data["resolved_at"] is not None
    assert data["resolver_id"] is not None


@pytest.mark.asyncio
async def test_resolve_anomaly_not_found(
    client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str
):
    fake_anomaly_id = uuid.uuid4()

    response = await client.patch(
        f"{settings.api_v1_prefix}/ops/anomalies/{fake_anomaly_id}/resolve",
        headers=_ops_headers(ops_token),
        json={"reason": "测试不存在的异常"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == VoteErrorCodes.ANOMALY_NOT_FOUND


@pytest.mark.asyncio
async def test_false_positive_anomaly(
    client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str
):
    player_id = uuid.uuid4()
    anomaly = await _create_test_anomaly(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        player_id=player_id,
        anomaly_type="frequency",
        severity="high",
    )

    response = await client.patch(
        f"{settings.api_v1_prefix}/ops/anomalies/{anomaly.anomaly_id}/false-positive",
        headers=_ops_headers(ops_token),
        json={"reason": "经核实为误报，玩家行为正常"},
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["anomaly_id"] == str(anomaly.anomaly_id)
    assert data["status"] == "false_positive"
    assert data["resolved_at"] is not None
    assert data["resolver_id"] is not None


@pytest.mark.asyncio
async def test_anomaly_stats(
    client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str
):
    player_1 = uuid.uuid4()
    player_2 = uuid.uuid4()
    player_3 = uuid.uuid4()

    await _create_test_anomaly(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        player_id=player_1,
        anomaly_type="frequency",
        severity="high",
        status="detected",
    )
    await _create_test_anomaly(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        player_id=player_2,
        anomaly_type="weight",
        severity="critical",
        status="detected",
    )
    await _create_test_anomaly(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        player_id=player_3,
        anomaly_type="device",
        severity="medium",
        status="resolved",
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/ops/anomalies/stats",
        headers=_ops_headers(ops_token),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["total"] == 3
    assert data["by_type"]["frequency"] == 1
    assert data["by_type"]["weight"] == 1
    assert data["by_type"]["device"] == 1
    assert data["by_severity"]["high"] == 1
    assert data["by_severity"]["critical"] == 1
    assert data["by_severity"]["medium"] == 1
    assert data["by_status"]["detected"] == 2
    assert data["by_status"]["resolved"] == 1
    assert body["request_id"]
