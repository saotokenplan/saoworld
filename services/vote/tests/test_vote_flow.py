import uuid

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.domain.models import VoteCycle


def _extract_data(response_json: dict) -> dict:
    """从 envelope 响应中提取 data 字段"""
    assert "request_id" in response_json
    assert "data" in response_json
    return response_json["data"]


@pytest.mark.asyncio
async def test_get_current_vote_returns_open_cycle(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    response = await client.get(f"{settings.api_v1_prefix}/votes/current")
    assert response.status_code == 200
    body = response.json()
    data = _extract_data(body)

    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["chapter_id"] == "ch_prologue_01"
    assert data["status"] == "open"
    assert data["has_voted"] is False
    assert data["my_vote_candidate_id"] is None
    assert len(data["candidates"]) == 3
    candidate_titles = [c["title"] for c in data["candidates"]]
    assert "探索迷雾森林" in candidate_titles
    assert "重建边境哨所" in candidate_titles
    assert "追踪暗影盗贼" in candidate_titles


@pytest.mark.asyncio
async def test_get_current_vote_shows_my_vote(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    first_candidate = open_vote_cycle.candidates[0]

    submit_resp = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": "test-vote-1",
        },
        json={
            "candidate_id": str(first_candidate.candidate_id),
            "device_fingerprint_hash": "device_hash_abc123",
            "weight": 1.0,
        },
    )
    assert submit_resp.status_code == 201

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current",
        headers={"X-Player-Id": player_id},
    )
    assert response.status_code == 200
    data = _extract_data(response.json())
    assert data["has_voted"] is True
    assert data["my_vote_candidate_id"] == str(first_candidate.candidate_id)


@pytest.mark.asyncio
async def test_submit_vote_success(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[1]

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": "test-vote-2",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "device_hash_def456",
            "weight": 2.5,
        },
    )
    assert response.status_code == 201
    body = response.json()
    data = _extract_data(body)
    assert "vote_id" in data
    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["candidate_id"] == str(candidate.candidate_id)
    assert "submitted_at" in data
    assert "X-Request-Id" in response.headers


@pytest.mark.asyncio
async def test_submit_vote_duplicate_rejected(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    first = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": "test-vote-3a",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash1",
            "weight": 1.0,
        },
    )
    assert first.status_code == 201

    second = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": "test-vote-3b",
        },
        json={
            "candidate_id": str(open_vote_cycle.candidates[1].candidate_id),
            "device_fingerprint_hash": "hash2",
            "weight": 1.0,
        },
    )
    assert second.status_code == 409
    data = second.json()
    assert data["code"] == "ALREADY_VOTED"


@pytest.mark.asyncio
async def test_submit_vote_idempotency_key(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]
    idempotency_key = "test-vote-idempotent-4"

    first = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": idempotency_key,
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash1",
        },
    )
    assert first.status_code == 201
    first_data = _extract_data(first.json())

    second = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": idempotency_key,
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash1",
        },
    )
    assert second.status_code == 200 or second.status_code == 201
    second_data = _extract_data(second.json())
    assert second_data["vote_id"] == first_data["vote_id"]


@pytest.mark.asyncio
async def test_submit_vote_candidate_not_found(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    fake_candidate_id = str(uuid.uuid4())

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": "test-vote-5",
        },
        json={
            "candidate_id": fake_candidate_id,
            "device_fingerprint_hash": "hash",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "CANDIDATE_NOT_FOUND"


@pytest.mark.asyncio
async def test_submit_vote_invalid_player_id(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    candidate = open_vote_cycle.candidates[0]

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": "not-a-uuid",
            "Idempotency-Key": "test-vote-6",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "INVALID_PLAYER_ID"


@pytest.mark.asyncio
async def test_submit_vote_missing_player_id_header(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    candidate = open_vote_cycle.candidates[0]

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "Idempotency-Key": "test-vote-7",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_vote_history_empty(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history",
        headers={"X-Player-Id": player_id},
    )
    assert response.status_code == 200
    body = response.json()
    data = _extract_data(body)
    assert data["player_id"] == player_id
    assert data["votes"] == []
    assert "meta" in body
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_vote_history_returns_submitted_votes(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": "test-history-1",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash_hist",
            "weight": 1.5,
        },
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history",
        headers={"X-Player-Id": player_id},
    )
    assert response.status_code == 200
    body = response.json()
    data = _extract_data(body)
    assert data["player_id"] == player_id
    assert len(data["votes"]) == 1
    vote = data["votes"][0]
    assert vote["candidate_id"] == str(candidate.candidate_id)
    assert vote["candidate_title"] == candidate.title
    assert vote["weight"] == 1.5
    assert "vote_id" in vote
    assert "created_at" in vote
    assert body["meta"]["total"] == 1


@pytest.mark.asyncio
async def test_vote_history_invalid_player_id(client: AsyncClient):
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history",
        headers={"X-Player-Id": "bad-uuid"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "INVALID_PLAYER_ID"


@pytest.mark.asyncio
async def test_envelope_format_has_request_id_and_data(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """验证成功响应遵循统一 envelope 格式"""
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current",
        headers={"X-Trace-Id": "trace_test_123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "request_id" in body
    assert "data" in body
    assert body["trace_id"] == "trace_test_123"


@pytest.mark.asyncio
async def test_submit_vote_weight_zero_rejected(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """weight=0 应被拒绝（与 CHECK 约束 weight > 0 一致）"""
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": "test-weight-zero",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash",
            "weight": 0,
        },
    )
    assert response.status_code == 422
