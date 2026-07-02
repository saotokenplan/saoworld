import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_content_updates_returns_visible_packages(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 3
    assert len(data["data"]["packages"]) == 3
    for pkg in data["data"]["packages"]:
        assert pkg["status"] in ("gray", "live")


@pytest.mark.asyncio
async def test_list_content_updates_envelope_format(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert "packages" in data["data"]
    assert "total" in data["data"]


@pytest.mark.asyncio
async def test_list_content_updates_pagination(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates?limit=1&offset=0",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["packages"]) == 1
    assert data["meta"]["total"] == 3
    assert data["meta"]["limit"] == 1
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_list_content_updates_pagination_offset(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates?limit=1&offset=2",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["packages"]) == 1
    assert data["meta"]["total"] == 3
    assert data["meta"]["offset"] == 2


@pytest.mark.asyncio
async def test_list_content_updates_filter_by_chapter(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates?chapter_id=chapter_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 2
    for pkg in data["data"]["packages"]:
        assert pkg["chapter_id"] == "chapter_01"


@pytest.mark.asyncio
async def test_list_content_updates_chapter_no_match(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates?chapter_id=chapter_nonexistent",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 0
    assert len(data["data"]["packages"]) == 0


@pytest.mark.asyncio
async def test_get_package_detail_found(
    client: AsyncClient, player_token: str, content_packages
):
    live_package = next(p for p in content_packages if p.status == "live")
    response = await client.get(
        f"/api/v1/content/packages/{live_package.content_package_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert str(data["data"]["content_package_id"]) == str(live_package.content_package_id)
    assert data["data"]["title"] == live_package.title
    assert data["data"]["status"] == live_package.status
    assert data["data"]["payload"] == live_package.payload_jsonb


@pytest.mark.asyncio
async def test_get_package_detail_not_found(
    client: AsyncClient, player_token: str
):
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/content/packages/{fake_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "PACKAGE_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_package_detail_packaged_hidden_from_player(
    client: AsyncClient, player_token: str, content_packages
):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.get(
        f"/api/v1/content/packages/{packaged_package.content_package_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_package_detail_rolled_back_hidden_from_player(
    client: AsyncClient, player_token: str, content_packages
):
    rolled_back_package = next(p for p in content_packages if p.status == "rolled_back")
    response = await client.get(
        f"/api/v1/content/packages/{rolled_back_package.content_package_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_package_detail_visible_to_ops(
    client: AsyncClient, ops_token: str, content_packages
):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.get(
        f"/api/v1/content/packages/{packaged_package.content_package_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert str(data["data"]["content_package_id"]) == str(packaged_package.content_package_id)


@pytest.mark.asyncio
async def test_list_content_updates_with_trace_id(
    client: AsyncClient, player_token: str, content_packages
):
    trace_id = "trace_test_123"
    response = await client.get(
        "/api/v1/content/updates",
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Trace-Id": trace_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id


@pytest.mark.asyncio
async def test_list_content_updates_request_id_header(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert "X-Request-Id" in response.headers
    assert response.headers["X-Request-Id"].startswith("req_")


@pytest.mark.asyncio
async def test_get_package_detail_with_trace_id(
    client: AsyncClient, player_token: str, content_packages
):
    live_package = next(p for p in content_packages if p.status == "live")
    trace_id = "trace_detail_456"
    response = await client.get(
        f"/api/v1/content/packages/{live_package.content_package_id}",
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Trace-Id": trace_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id
