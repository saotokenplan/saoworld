import uuid

import pytest
from httpx import AsyncClient

from app.core.errors import WorldErrorCodes
from app.domain.models import WorldSkeleton


@pytest.mark.asyncio
async def test_get_world_skeleton_not_found(client: AsyncClient, player_token: str):
    response = await client.get(
        "/api/v1/world/skeleton",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == WorldErrorCodes.SKELETON_NOT_FOUND


@pytest.mark.asyncio
async def test_create_world_skeleton_success(client: AsyncClient, ops_token: str):
    payload = {
        "world_version": "v1.0.0",
        "chapter_id": "chapter_01",
        "regions": {
            "region_core_ironward": {"chapter_id": "chapter_01", "title": "铁卫城周边"},
            "region_expansion_grayvalley": {"chapter_id": "chapter_01", "title": "灰谷废墟"},
        },
        "factions": {
            "faction_ironward": {"name": "铁卫联盟", "alignment": "order"},
            "faction_freehold": {"name": "自由领地", "alignment": "freedom"},
        },
        "forbidden_tags": ["现代政治映射", "极端暴力", "现实宗教影射"],
        "reserved_characters": {"npc_hero": "主角"},
        "reward_limits": {"max_gold": 1000, "max_exp": 500},
        "is_active": True,
    }

    response = await client.post(
        "/api/v1/ops/world/skeleton",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-skeleton-001",
        },
        json=payload,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["world_version"] == "v1.0.0"
    assert data["data"]["chapter_id"] == "chapter_01"
    assert data["data"]["is_active"] is True


@pytest.mark.asyncio
async def test_create_world_skeleton_duplicate_version(client: AsyncClient, ops_token: str):
    payload = {
        "world_version": "v1.0.0",
        "chapter_id": "chapter_01",
        "regions": {"region_01": {"chapter_id": "chapter_01"}},
        "factions": {"faction_01": {"name": "测试阵营"}},
        "forbidden_tags": ["test"],
    }

    first_response = await client.post(
        "/api/v1/ops/world/skeleton",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-skeleton-dup-001",
        },
        json=payload,
    )
    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/ops/world/skeleton",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-skeleton-dup-002",
        },
        json=payload,
    )
    assert second_response.status_code == 409
    data = second_response.json()
    assert data["code"] == WorldErrorCodes.SKELETON_VERSION_EXISTS


@pytest.mark.asyncio
async def test_create_world_skeleton_missing_forbidden_tags(client: AsyncClient, ops_token: str):
    payload = {
        "world_version": "v1.0.1",
        "chapter_id": "chapter_01",
        "regions": {"region_01": {"chapter_id": "chapter_01"}},
        "factions": {"faction_01": {"name": "测试阵营"}},
        "forbidden_tags": [],
    }

    response = await client.post(
        "/api/v1/ops/world/skeleton",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-skeleton-003",
        },
        json=payload,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_world_skeleton_success(client: AsyncClient, player_token: str):
    from tests.conftest import TestSessionLocal

    skeleton = WorldSkeleton(
        skeleton_id=uuid.uuid4(),
        world_version="v2.0.0",
        chapter_id="chapter_01",
        regions={"region_test": {"chapter_id": "chapter_01"}},
        factions={"faction_test": {"name": "测试"}},
        forbidden_tags=["tag1", "tag2"],
        is_active=True,
    )

    async with TestSessionLocal() as session:
        session.add(skeleton)
        await session.commit()

    response = await client.get(
        "/api/v1/world/skeleton",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["world_version"] == "v2.0.0"
    assert data["data"]["chapter_id"] == "chapter_01"
    assert data["data"]["is_active"] is True
    assert "regions" in data["data"]
    assert "factions" in data["data"]
    assert "forbidden_tags" in data["data"]


@pytest.mark.asyncio
async def test_get_world_skeleton_envelope_format(client: AsyncClient, player_token: str):
    from tests.conftest import TestSessionLocal

    skeleton = WorldSkeleton(
        skeleton_id=uuid.uuid4(),
        world_version="v3.0.0",
        chapter_id="chapter_01",
        regions={},
        factions={},
        forbidden_tags=["test"],
        is_active=True,
    )

    async with TestSessionLocal() as session:
        session.add(skeleton)
        await session.commit()

    response = await client.get(
        "/api/v1/world/skeleton",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "trace_id" in data
