import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_analytics_overview_returns_zero_metrics_when_no_data(
    async_client: AsyncClient, test_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/dashboard/overview",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    overview = data["data"]
    assert overview["total_players"] == 0
    assert overview["active_players_today"] == 0
    assert overview["total_votes"] == 0
    assert overview["votes_today"] == 0
    assert overview["total_quests_completed"] == 0
    assert overview["quests_completed_today"] == 0
    assert overview["total_regions_visited"] == 0
    assert overview["regions_visited_today"] == 0
    assert overview["avg_session_duration_seconds"] == 0
    assert overview["report_count"] == 0


@pytest.mark.asyncio
async def test_get_analytics_overview_requires_auth(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/api/v1/ops/analytics/dashboard/overview")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_region_analytics_returns_empty_when_no_data(
    async_client: AsyncClient, test_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/dashboard/regions",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_region_analytics_with_pagination(
    async_client: AsyncClient, test_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/dashboard/regions?limit=5&offset=0",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert data["meta"]["limit"] == 5
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_get_quest_analytics_returns_empty_when_no_data(
    async_client: AsyncClient, test_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/dashboard/quests",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_vote_analytics_returns_empty_when_no_data(
    async_client: AsyncClient, test_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/dashboard/votes",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_region_analytics_requires_auth(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/api/v1/ops/analytics/dashboard/regions")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_quest_analytics_requires_auth(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/api/v1/ops/analytics/dashboard/quests")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_vote_analytics_requires_auth(
    async_client: AsyncClient,
) -> None:
    response = await async_client.get("/api/v1/ops/analytics/dashboard/votes")
    assert response.status_code == 401