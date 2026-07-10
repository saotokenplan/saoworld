import uuid

import pytest
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.core.config import settings
from app.core.errors import VoteErrorCodes
from app.domain.models import VoteCycle
from app.schemas.auth import Role


def _player_headers(player_id: str | None = None) -> dict[str, str]:
    """创建玩家请求头（含 JWT Token）。"""
    if player_id is None:
        player_id = str(uuid.uuid4())
    token = create_test_token(user_id=player_id, role=Role.PLAYER)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_current_vote_returns_open_cycle(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert body["request_id"]
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
            **_player_headers(player_id),
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
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    data = response.json()["data"]
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
            **_player_headers(player_id),
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
    data = body["data"]
    assert "vote_id" in data
    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["candidate_id"] == str(candidate.candidate_id)
    assert data["request_id"]
    assert "submitted_at" in data
    assert data["weight"] == 2.75
    assert data["weight_multiplier"] == 1.1
    assert data["contribution_points"] == 1000
    assert body["request_id"]
    assert "X-Request-Id" in response.headers


@pytest.mark.asyncio
async def test_submit_vote_insufficient_contribution(
    client: AsyncClient, open_vote_cycle: VoteCycle, monkeypatch
):
    """测试贡献度不足时投票被拒绝。"""
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    async def mock_get_contribution(*args: object, **kwargs: object) -> int:
        return 50

    monkeypatch.setattr(
        "app.core.player_client.PlayerContributionClient.get_contribution",
        mock_get_contribution,
    )

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-insufficient-contribution",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash_test",
            "weight": 1.0,
        },
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == VoteErrorCodes.INSUFFICIENT_CONTRIBUTION
    assert "贡献度不足" in data["message"]


@pytest.mark.asyncio
async def test_submit_vote_high_contribution_weight_multiplier(
    client: AsyncClient, open_vote_cycle: VoteCycle, monkeypatch
):
    """测试高贡献度玩家投票权重按倍率放大并受上限约束。"""
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[1]

    async def mock_get_contribution(*args: object, **kwargs: object) -> int:
        return 2500

    monkeypatch.setattr(
        "app.core.player_client.PlayerContributionClient.get_contribution",
        mock_get_contribution,
    )

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-high-contribution",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash_high",
            "weight": 2.5,
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["weight"] == 3.0
    assert data["weight_multiplier"] == 1.2
    assert data["contribution_points"] == 2500


@pytest.mark.asyncio
async def test_submit_vote_duplicate_rejected(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    first = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
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
            **_player_headers(player_id),
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
    assert data["code"] == VoteErrorCodes.ALREADY_VOTED


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
            **_player_headers(player_id),
            "Idempotency-Key": idempotency_key,
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash1",
        },
    )
    assert first.status_code == 201
    first_data = first.json()["data"]

    second = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": idempotency_key,
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash1",
        },
    )
    assert second.status_code == 200 or second.status_code == 201
    second_data = second.json()["data"]
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
            **_player_headers(player_id),
            "Idempotency-Key": "test-vote-5",
        },
        json={
            "candidate_id": fake_candidate_id,
            "device_fingerprint_hash": "hash",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == VoteErrorCodes.CANDIDATE_NOT_FOUND


@pytest.mark.asyncio
async def test_submit_vote_missing_token_returns_401(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试玩家接口缺少 JWT Token 返回 401。"""
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
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_vote_history_empty(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["player_id"] == player_id
    assert data["total"] == 0
    assert data["votes"] == []
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
            **_player_headers(player_id),
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
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["player_id"] == player_id
    assert data["total"] == 1
    assert len(data["votes"]) == 1
    vote = data["votes"][0]
    assert vote["candidate_id"] == str(candidate.candidate_id)
    assert vote["candidate_title"] == candidate.title
    assert vote["weight"] == 1.65
    assert "vote_id" in vote
    assert "created_at" in vote


@pytest.mark.asyncio
async def test_vote_history_missing_token_returns_401(client: AsyncClient):
    """测试投票历史接口缺少 JWT Token 返回 401。"""
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history",
    )
    assert response.status_code == 401
