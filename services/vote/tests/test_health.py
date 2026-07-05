import uuid

import pytest
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.core.config import settings
from app.core.errors import VoteErrorCodes
from app.domain.models import VoteCycle
from app.schemas.auth import Role


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get(f"{settings.api_v1_prefix}/health")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["service"] == settings.app_name
    assert data["data"]["version"] == settings.app_version
    assert data["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_get_current_vote_no_open_cycle(client: AsyncClient, player_token: str):
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == VoteErrorCodes.NO_OPEN_VOTE_CYCLE
    assert "request_id" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    response = await client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content


@pytest.mark.asyncio
async def test_business_metrics_exposed(client: AsyncClient):
    """业务指标名应出现在 /metrics 端点输出中。"""
    response = await client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "vote_submissions_total" in content
    assert "vote_cycles_by_status" in content
    assert "vote_candidates_by_status" in content
    assert "vote_cycle_transitions_total" in content


@pytest.mark.asyncio
async def test_vote_submission_metric_incremented(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """提交投票后，vote_submissions_total 计数器应递增。"""
    metrics_before = (await client.get("/metrics")).text

    def _extract_counter_value(text: str, name: str) -> float:
        for line in text.splitlines():
            if line.startswith(name) and not line.startswith(f"{name}_"):
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return float(parts[1])
                    except ValueError:
                        continue
        return 0.0

    before = _extract_counter_value(metrics_before, "vote_submissions_total")

    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]
    token = create_test_token(user_id=player_id, role=Role.PLAYER)
    submit_resp = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": f"metric-test-{uuid.uuid4().hex}",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "device_hash_metric",
            "weight": 1.0,
        },
    )
    assert submit_resp.status_code == 201

    metrics_after = (await client.get("/metrics")).text
    after = _extract_counter_value(metrics_after, "vote_submissions_total")
    assert after > before
