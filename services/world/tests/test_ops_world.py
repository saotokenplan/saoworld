import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_region_no_token_returns_401(client: AsyncClient):
    response = await client.post(
        "/api/v1/ops/world/regions",
        json={
            "chapter_id": "ch_01",
            "title": "测试区域",
            "summary": "一个测试区域",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_region_player_role_forbidden(
    client: AsyncClient, player_token: str
):
    response = await client.post(
        "/api/v1/ops/world/regions",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-create-001",
        },
        json={
            "chapter_id": "ch_01",
            "title": "测试区域",
            "summary": "一个测试区域",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_region_success(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/world/regions",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-002",
            "X-Trace-Id": "trace_create_001",
        },
        json={
            "chapter_id": "ch_01",
            "title": "新区域",
            "summary": "一个新创建的区域",
            "status": "locked",
            "visible": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "region_id" in data["data"]
    assert data["data"]["chapter_id"] == "ch_01"
    assert data["data"]["title"] == "新区域"
    assert data["data"]["status"] == "locked"
    assert data["data"]["visible"] is False
    assert data["trace_id"] == "trace_create_001"


@pytest.mark.asyncio
async def test_create_region_default_values(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/world/regions",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-003",
        },
        json={
            "chapter_id": "ch_01",
            "title": "默认区域",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["status"] == "locked"
    assert data["data"]["visible"] is False


@pytest.mark.asyncio
async def test_create_region_missing_title(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/world/regions",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-004",
        },
        json={
            "chapter_id": "ch_01",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_region_envelope_format(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/world/regions",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-005",
        },
        json={
            "chapter_id": "ch_01",
            "title": "格式测试区域",
        },
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "trace_id" in data


@pytest.mark.asyncio
async def test_update_region_status_success(client: AsyncClient, ops_token: str, visible_regions):
    region = visible_regions[0]
    assert region.status == "active"

    response = await client.post(
        f"/api/v1/ops/world/regions/{region.region_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-001",
            "X-Trace-Id": "trace_status_001",
        },
        json={
            "status": "unstable",
            "reason": "剧情推进导致区域动荡",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "unstable"
    assert data["trace_id"] == "trace_status_001"


@pytest.mark.asyncio
async def test_update_region_status_not_found(client: AsyncClient, ops_token: str):
    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/ops/world/regions/{fake_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-002",
        },
        json={
            "status": "active",
            "reason": "测试",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "REGION_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_region_status_invalid_transition(
    client: AsyncClient, ops_token: str, visible_regions
):
    region = visible_regions[2]
    assert region.status == "locked"

    response = await client.post(
        f"/api/v1/ops/world/regions/{region.region_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-003",
        },
        json={
            "status": "archived",
            "reason": "测试无效迁移",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "INVALID_REGION_STATUS"


@pytest.mark.asyncio
async def test_update_region_status_locked_to_active(
    client: AsyncClient, ops_token: str, visible_regions
):
    region = visible_regions[2]
    assert region.status == "locked"

    response = await client.post(
        f"/api/v1/ops/world/regions/{region.region_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-004",
        },
        json={
            "status": "active",
            "reason": "解锁新区域",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_update_region_status_player_forbidden(
    client: AsyncClient, player_token: str, visible_regions
):
    region = visible_regions[0]
    response = await client.post(
        f"/api/v1/ops/world/regions/{region.region_id}/status",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-status-005",
        },
        json={
            "status": "unstable",
            "reason": "测试",
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_region_status_missing_reason(
    client: AsyncClient, ops_token: str, visible_regions
):
    region = visible_regions[0]
    response = await client.post(
        f"/api/v1/ops/world/regions/{region.region_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-006",
        },
        json={
            "status": "unstable",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_region_with_unlock_condition(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/world/regions",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-006",
        },
        json={
            "chapter_id": "ch_01",
            "title": "条件解锁区域",
            "unlock_condition": {"level": 5, "quest": "quest_001"},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["title"] == "条件解锁区域"
