import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.domain.models import VoteCandidate, VoteCycle


def _ops_headers(
    ops_token: str,
    idempotency_key: str | None = None,
    trace_id: str | None = None,
) -> dict[str, str]:
    headers: dict[str, str] = {
        "Authorization": f"Bearer {ops_token}",
    }
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    if trace_id:
        headers["X-Trace-Id"] = trace_id
    return headers


def _sample_candidates() -> list[dict]:
    return [
        {
            "title": "探索迷雾森林",
            "summary": "玩家深入北部迷雾森林，揭开古老遗迹的秘密",
            "description": "一条探索向的主线",
            "region_scope": ["forest_north"],
            "risk_tags": ["content_risk"],
        },
        {
            "title": "重建边境哨所",
            "summary": "协助村民重建被摧毁的边境哨所",
            "description": "一条建设向的主线",
            "region_scope": ["border_outpost"],
            "risk_tags": ["economy_risk"],
        },
    ]


# --- 创建投票周期 ---


@pytest.mark.asyncio
async def test_create_vote_cycle_success(client: AsyncClient, ops_token: str):
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "chapter_03",
        "starts_at": (now + timedelta(hours=1)).isoformat(),
        "ends_at": (now + timedelta(hours=25)).isoformat(),
        "candidates": _sample_candidates(),
        "reason": "第三章主线剧情投票创建",
    }

    response = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        json=payload,
        headers=_ops_headers(ops_token, idempotency_key="test-create-vc-1"),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["vote_cycle_id"]
    assert data["chapter_id"] == "chapter_03"
    assert data["status"] == "draft"
    assert len(data["candidates"]) == 2
    assert data["request_id"]
    assert "X-Request-Id" in response.headers


@pytest.mark.asyncio
async def test_create_vote_cycle_ends_at_before_starts_at(client: AsyncClient, ops_token: str):
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "chapter_03",
        "starts_at": (now + timedelta(hours=25)).isoformat(),
        "ends_at": (now + timedelta(hours=1)).isoformat(),
        "candidates": _sample_candidates(),
        "reason": "时间顺序不对",
    }

    response = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        json=payload,
        headers=_ops_headers(ops_token, idempotency_key="test-create-vc-2"),
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == "INVALID_ARGUMENT"


@pytest.mark.asyncio
async def test_create_vote_cycle_with_existing_open_cycle(
    client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str
):
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": open_vote_cycle.chapter_id,
        "starts_at": (now + timedelta(hours=1)).isoformat(),
        "ends_at": (now + timedelta(hours=25)).isoformat(),
        "candidates": _sample_candidates(),
        "reason": "冲突测试",
    }

    response = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        json=payload,
        headers=_ops_headers(ops_token, idempotency_key="test-create-vc-3"),
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "VOTE_CYCLE_CONFLICT"


@pytest.mark.asyncio
async def test_create_vote_cycle_too_few_candidates(client: AsyncClient, ops_token: str):
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "chapter_04",
        "starts_at": (now + timedelta(hours=1)).isoformat(),
        "ends_at": (now + timedelta(hours=25)).isoformat(),
        "candidates": [
            {
                "title": "只有一个",
                "summary": "不足两个候选项",
            }
        ],
        "reason": "候选不足",
    }

    response = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        json=payload,
        headers=_ops_headers(ops_token, idempotency_key="test-create-vc-4"),
    )
    assert response.status_code == 422


# --- 状态迁移完整生命周期 ---


@pytest.mark.asyncio
async def test_full_lifecycle_draft_scheduled_open_closed_finalized(client: AsyncClient, ops_token: str):
    """测试完整状态迁移路径 draft → scheduled → open → closed → finalized"""
    now = datetime.now(timezone.utc)

    # 1. 创建投票周期（draft）
    payload = {
        "chapter_id": "chapter_lifecycle",
        "starts_at": (now - timedelta(hours=1)).isoformat(),
        "ends_at": (now + timedelta(hours=23)).isoformat(),
        "candidates": _sample_candidates(),
        "reason": "全生命周期测试",
    }
    create_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        json=payload,
        headers=_ops_headers(ops_token, idempotency_key="test-lifecycle-1"),
    )
    assert create_resp.status_code == 201
    cycle_id = create_resp.json()["vote_cycle_id"]
    assert create_resp.json()["status"] == "draft"

    # 2. draft → scheduled
    schedule_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{cycle_id}/schedule",
        json={"reason": "计划上线"},
        headers=_ops_headers(ops_token, idempotency_key="test-lifecycle-2"),
    )
    assert schedule_resp.status_code == 200
    assert schedule_resp.json()["status"] == "scheduled"

    # 3. scheduled → open
    open_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{cycle_id}/open",
        json={"reason": "开放投票"},
        headers=_ops_headers(ops_token, idempotency_key="test-lifecycle-3"),
    )
    assert open_resp.status_code == 200
    assert open_resp.json()["status"] == "open"

    # 4. open → closed（含计票）
    close_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{cycle_id}/close",
        json={"reason": "关闭投票"},
        headers=_ops_headers(ops_token, idempotency_key="test-lifecycle-4"),
    )
    assert close_resp.status_code == 200
    assert close_resp.json()["status"] == "closed"

    # 5. closed → finalized
    finalize_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{cycle_id}/finalize",
        json={"reason": "确认结果"},
        headers=_ops_headers(ops_token, idempotency_key="test-lifecycle-5"),
    )
    assert finalize_resp.status_code == 200
    assert finalize_resp.json()["status"] == "finalized"


@pytest.mark.asyncio
async def test_cannot_open_from_draft(client: AsyncClient, ops_token: str):
    """测试 draft 不能直接 open"""
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "chapter_skip_scheduled",
        "starts_at": (now - timedelta(hours=1)).isoformat(),
        "ends_at": (now + timedelta(hours=23)).isoformat(),
        "candidates": _sample_candidates(),
        "reason": "跳过 scheduled 测试",
    }
    create_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        json=payload,
        headers=_ops_headers(ops_token, idempotency_key="test-skip-1"),
    )
    assert create_resp.status_code == 201
    cycle_id = create_resp.json()["vote_cycle_id"]

    open_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{cycle_id}/open",
        json={"reason": "非法迁移"},
        headers=_ops_headers(ops_token, idempotency_key="test-skip-2"),
    )
    assert open_resp.status_code == 409
    assert open_resp.json()["code"] == "INVALID_VOTE_STATE"


@pytest.mark.asyncio
async def test_open_vote_cycle_from_scheduled(client: AsyncClient, ops_token: str):
    """测试从 scheduled 状态 open 投票周期"""
    from tests.conftest import TestSessionLocal

    now = datetime.now(timezone.utc)
    cycle_id = uuid.uuid4()

    candidates = [
        VoteCandidate(
            candidate_id=uuid.uuid4(),
            vote_cycle_id=cycle_id,
            title="探索荒原",
            summary="探索荒原深处",
            status="active",
        ),
        VoteCandidate(
            candidate_id=uuid.uuid4(),
            vote_cycle_id=cycle_id,
            title="建设前哨",
            summary="建设边境前哨站",
            status="active",
        ),
    ]
    cycle = VoteCycle(
        vote_cycle_id=cycle_id,
        chapter_id="chapter_scheduled",
        status="scheduled",
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(hours=23),
        created_by="ops",
        created_reason="测试 scheduled 到 open",
        candidates=candidates,
    )

    async with TestSessionLocal() as session:
        session.add(cycle)
        await session.commit()

    open_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{cycle_id}/open",
        json={"reason": "开放投票"},
        headers=_ops_headers(ops_token, idempotency_key="test-scheduled-open-1"),
    )
    assert open_resp.status_code == 200
    data = open_resp.json()
    assert data["status"] == "open"
    assert data["vote_cycle_id"] == str(cycle_id)


# --- 计票逻辑 ---


@pytest.mark.asyncio
async def test_close_vote_cycle_with_tally(client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str):
    """测试关闭投票周期时自动计票"""
    player_1 = uuid.uuid4()
    player_2 = uuid.uuid4()
    player_3 = uuid.uuid4()
    candidate_1 = open_vote_cycle.candidates[0]
    candidate_2 = open_vote_cycle.candidates[1]

    # 3 人投票：2票给 candidate_1，1票给 candidate_2
    for i, (player_id, candidate, weight) in enumerate([
        (player_1, candidate_1, 1.0),
        (player_2, candidate_1, 2.0),
        (player_3, candidate_2, 1.5),
    ]):
        await client.post(
            f"{settings.api_v1_prefix}/votes/submit",
            headers={
                "X-Player-Id": str(player_id),
                "Idempotency-Key": f"test-tally-{i}",
            },
            json={
                "candidate_id": str(candidate.candidate_id),
                "device_fingerprint_hash": f"hash_{i}",
                "weight": weight,
            },
        )

    close_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{open_vote_cycle.vote_cycle_id}/close",
        json={"reason": "投票结束，开始计票"},
        headers=_ops_headers(ops_token, idempotency_key="test-close-tally-1"),
    )
    assert close_resp.status_code == 200
    data = close_resp.json()
    assert data["status"] == "closed"
    # candidate_1 的加权总分 = 1.0 + 2.0 = 3.0 > candidate_2 的 1.5
    assert data["winning_candidate_id"] == str(candidate_1.candidate_id)


@pytest.mark.asyncio
async def test_tally_with_no_votes(client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str):
    """测试无人投票时关闭投票周期"""
    close_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{open_vote_cycle.vote_cycle_id}/close",
        json={"reason": "无人投票"},
        headers=_ops_headers(ops_token, idempotency_key="test-no-votes-close-1"),
    )
    assert close_resp.status_code == 200
    data = close_resp.json()
    assert data["status"] == "closed"
    assert data["winning_candidate_id"] is None


# --- 确认结果 ---


@pytest.mark.asyncio
async def test_finalize_vote_cycle(client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str):
    """测试确认投票结果"""
    close_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{open_vote_cycle.vote_cycle_id}/close",
        json={"reason": "关闭投票"},
        headers=_ops_headers(ops_token, idempotency_key="test-finalize-close-1"),
    )
    assert close_resp.status_code == 200

    finalize_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{open_vote_cycle.vote_cycle_id}/finalize",
        json={"reason": "确认投票结果，开始内容生成"},
        headers=_ops_headers(ops_token, idempotency_key="test-finalize-1"),
    )
    assert finalize_resp.status_code == 200
    data = finalize_resp.json()
    assert data["status"] == "finalized"


# --- 非法状态迁移 ---


@pytest.mark.asyncio
async def test_cannot_finalize_open_cycle(client: AsyncClient, open_vote_cycle: VoteCycle, ops_token: str):
    """测试不能直接从 open finalized"""
    finalize_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{open_vote_cycle.vote_cycle_id}/finalize",
        json={"reason": "非法迁移"},
        headers=_ops_headers(ops_token, idempotency_key="test-finalize-invalid-1"),
    )
    assert finalize_resp.status_code == 409
    assert finalize_resp.json()["code"] == "INVALID_VOTE_STATE"


@pytest.mark.asyncio
async def test_cannot_close_draft_cycle(client: AsyncClient, ops_token: str):
    """测试不能关闭 draft 状态的周期"""
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "chapter_no_close_draft",
        "starts_at": (now + timedelta(hours=1)).isoformat(),
        "ends_at": (now + timedelta(hours=25)).isoformat(),
        "candidates": _sample_candidates(),
        "reason": "测试",
    }
    create_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        json=payload,
        headers=_ops_headers(ops_token, idempotency_key="test-draft-close-1"),
    )
    assert create_resp.status_code == 201
    cycle_id = create_resp.json()["vote_cycle_id"]

    close_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{cycle_id}/close",
        json={"reason": "非法迁移"},
        headers=_ops_headers(ops_token, idempotency_key="test-draft-close-2"),
    )
    assert close_resp.status_code == 409


@pytest.mark.asyncio
async def test_vote_cycle_not_found(client: AsyncClient, ops_token: str):
    """测试操作不存在的投票周期"""
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles/{fake_id}/open",
        json={"reason": "测试"},
        headers=_ops_headers(ops_token, idempotency_key="test-not-found-1"),
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "VOTE_CYCLE_NOT_FOUND"
