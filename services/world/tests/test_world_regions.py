import uuid

import pytest
from httpx import AsyncClient

from app.core.errors import WorldErrorCodes


@pytest.mark.asyncio
async def test_list_regions_no_token_returns_401(client: AsyncClient):
    response = await client.get("/api/v1/world/regions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_regions_invalid_token_returns_401(client: AsyncClient):
    response = await client.get(
        "/api/v1/world/regions",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_regions_returns_visible_regions(
    client: AsyncClient, player_token: str, visible_regions
):
    response = await client.get(
        "/api/v1/world/regions",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 2
    assert len(data["data"]["regions"]) == 2
    assert data["meta"]["total"] == 2
    assert data["meta"]["limit"] == 20
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_list_regions_envelope_format(
    client: AsyncClient, player_token: str, visible_regions
):
    response = await client.get(
        "/api/v1/world/regions",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert "regions" in data["data"]
    assert "total" in data["data"]


@pytest.mark.asyncio
async def test_list_regions_pagination(
    client: AsyncClient, player_token: str, visible_regions
):
    response = await client.get(
        "/api/v1/world/regions?limit=1&offset=0",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["regions"]) == 1
    assert data["meta"]["total"] == 2
    assert data["meta"]["limit"] == 1
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_list_regions_filter_by_chapter(
    client: AsyncClient, player_token: str, visible_regions
):
    response = await client.get(
        "/api/v1/world/regions?chapter_id=ch_prologue_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 2


@pytest.mark.asyncio
async def test_list_regions_chapter_no_match(
    client: AsyncClient, player_token: str, visible_regions
):
    response = await client.get(
        "/api/v1/world/regions?chapter_id=ch_nonexistent",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 0
    assert len(data["data"]["regions"]) == 0


@pytest.mark.asyncio
async def test_get_region_detail_found(
    client: AsyncClient, player_token: str, visible_regions
):
    region = visible_regions[0]
    response = await client.get(
        f"/api/v1/world/regions/{region.region_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert str(data["data"]["region_id"]) == str(region.region_id)
    assert data["data"]["title"] == region.title
    assert data["data"]["status"] == region.status
    assert data["data"]["visible"] is True


@pytest.mark.asyncio
async def test_get_region_detail_not_found(
    client: AsyncClient, player_token: str
):
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/world/regions/{fake_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == WorldErrorCodes.REGION_NOT_FOUND


@pytest.mark.asyncio
async def test_get_region_detail_hidden_from_player(
    client: AsyncClient, player_token: str, visible_regions
):
    hidden_region = visible_regions[2]
    assert hidden_region.visible is False
    response = await client.get(
        f"/api/v1/world/regions/{hidden_region.region_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_region_detail_visible_to_ops(
    client: AsyncClient, ops_token: str, visible_regions
):
    hidden_region = visible_regions[2]
    response = await client.get(
        f"/api/v1/world/regions/{hidden_region.region_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert str(data["data"]["region_id"]) == str(hidden_region.region_id)


@pytest.mark.asyncio
async def test_list_regions_with_trace_id(
    client: AsyncClient, player_token: str, visible_regions
):
    trace_id = "trace_test_123"
    response = await client.get(
        "/api/v1/world/regions",
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Trace-Id": trace_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id
    assert response.headers["X-Trace-Id"] == trace_id


@pytest.mark.asyncio
async def test_list_regions_request_id_header(
    client: AsyncClient, player_token: str, visible_regions
):
    response = await client.get(
        "/api/v1/world/regions",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert "X-Request-Id" in response.headers
    assert response.headers["X-Request-Id"].startswith("req_")
