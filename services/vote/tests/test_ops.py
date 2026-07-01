import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from app.core.config import settings


def _extract_data(response_json: dict) -> dict:
    """从 envelope 响应中提取 data 字段"""
    assert "request_id" in response_json
    assert "data" in response_json
    return response_json["data"]


@pytest.mark.asyncio
async def test_create_vote_cycle_success(client: AsyncClient):
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "ch_test_01",
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=7)).isoformat(),
        "created_by": "ops_user_001",
        "created_reason": "创建测试投票周期",
        "candidates": [
            {
                "title": "探索深渊",
                "summary": "深入地下探索未知区域",
                "description": "新增地下区域和3个NPC",
                "region_scope": ["underground_01"],
                "risk_tags": [],
            },
            {
                "title": "建设港口",
                "summary": "在海岸建设贸易港口",
                "description": None,
                "region_scope": ["coast_01"],
                "risk_tags": ["economy_risk"],
            },
        ],
    }

    response = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        headers={
            "Idempotency-Key": f"ops-create-{uuid.uuid4().hex[:8]}",
            "X-Trace-Id": "trace_ops_test",
        },
        json=payload,
    )
    assert response.status_code == 201
    body = response.json()
    data = _extract_data(body)

    assert "vote_cycle_id" in data
    assert data["chapter_id"] == "ch_test_01"
    assert data["status"] == "draft"
    assert len(data["candidates"]) == 2
    assert data["candidates"][0]["title"] == "探索深渊"
    assert data["candidates"][1]["title"] == "建设港口"
    assert body["trace_id"] == "trace_ops_test"


@pytest.mark.asyncio
async def test_create_vote_cycle_missing_idempotency_key(client: AsyncClient):
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "ch_test_02",
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=7)).isoformat(),
        "created_by": "ops_user_001",
        "created_reason": "测试缺少幂等键",
        "candidates": [
            {"title": "选项A", "summary": "摘要A"},
            {"title": "选项B", "summary": "摘要B"},
        ],
    }

    response = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_vote_cycle_too_few_candidates(client: AsyncClient):
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "ch_test_03",
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=7)).isoformat(),
        "created_by": "ops_user_001",
        "created_reason": "测试候选项不足",
        "candidates": [
            {"title": "唯一选项", "summary": "只有一个选项"},
        ],
    }

    response = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        headers={"Idempotency-Key": "ops-few-candidates"},
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_vote_cycle_empty_chapter_id(client: AsyncClient):
    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "",
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=7)).isoformat(),
        "created_by": "ops_user_001",
        "created_reason": "测试空chapter_id",
        "candidates": [
            {"title": "选项A", "summary": "摘要A"},
            {"title": "选项B", "summary": "摘要B"},
        ],
    }

    response = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        headers={"Idempotency-Key": "ops-empty-chapter"},
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_then_open_and_vote_e2e(client: AsyncClient):
    """端到端流程：创建投票周期 → 手动设为 open → 投票"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.domain.models import VoteCandidate, VoteCycle
    from tests.conftest import TestSessionLocal

    now = datetime.now(timezone.utc)
    payload = {
        "chapter_id": "ch_e2e_01",
        "starts_at": (now - timedelta(hours=1)).isoformat(),
        "ends_at": (now + timedelta(hours=23)).isoformat(),
        "created_by": "ops_user_001",
        "created_reason": "端到端测试",
        "candidates": [
            {
                "title": "方向A",
                "summary": "探索方向A",
                "region_scope": ["region_a"],
                "risk_tags": [],
            },
            {
                "title": "方向B",
                "summary": "探索方向B",
                "region_scope": ["region_b"],
                "risk_tags": [],
            },
        ],
    }

    # 步骤1：创建投票周期（状态为 draft）
    create_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/vote-cycles",
        headers={"Idempotency-Key": "ops-e2e-create"},
        json=payload,
    )
    assert create_resp.status_code == 201
    create_data = _extract_data(create_resp.json())
    cycle_id = create_data["vote_cycle_id"]
    assert create_data["status"] == "draft"

    # 步骤2：手动将周期状态改为 open（直接操作数据库模拟运营操作）
    async with TestSessionLocal() as session:
        stmt = (
            select(VoteCycle)
            .options(selectinload(VoteCycle.candidates))
            .where(VoteCycle.vote_cycle_id == uuid.UUID(cycle_id))
        )
        result = await session.execute(stmt)
        cycle = result.scalar_one()
        cycle.status = "open"
        await session.commit()

    # 步骤3：查询当前投票周期
    current_resp = await client.get(f"{settings.api_v1_prefix}/votes/current")
    assert current_resp.status_code == 200
    current_data = _extract_data(current_resp.json())
    assert current_data["vote_cycle_id"] == cycle_id
    assert current_data["status"] == "open"
    assert len(current_data["candidates"]) == 2

    # 步骤4：投票
    player_id = str(uuid.uuid4())
    candidate_id = current_data["candidates"][0]["candidate_id"]
    submit_resp = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "X-Player-Id": player_id,
            "Idempotency-Key": "e2e-vote-1",
        },
        json={
            "candidate_id": candidate_id,
            "device_fingerprint_hash": "hash_e2e",
            "weight": 1.0,
        },
    )
    assert submit_resp.status_code == 201
    submit_data = _extract_data(submit_resp.json())
    assert submit_data["candidate_id"] == candidate_id

    # 步骤5：查看投票历史
    history_resp = await client.get(
        f"{settings.api_v1_prefix}/votes/history",
        headers={"X-Player-Id": player_id},
    )
    assert history_resp.status_code == 200
    history_body = history_resp.json()
    history_data = _extract_data(history_body)
    assert history_body["meta"]["total"] == 1
    assert len(history_data["votes"]) == 1
