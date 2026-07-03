import pytest


@pytest.mark.asyncio
async def test_get_dashboard_returns_empty_metrics_when_no_data(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert "data" in data
    assert "dashboard_id" in data["data"]
    assert "metrics" in data["data"]

    metrics = data["data"]["metrics"]
    assert metrics["total_players"] == 0
    assert metrics["total_vote_cycles"] == 0
    assert metrics["total_votes"] == 0
    assert metrics["total_content_packages"] == 0
    assert metrics["total_regions"] == 0
    assert metrics["live_content_packages"] == 0
    assert metrics["open_vote_cycle"] is False
    assert metrics["active_generation_requests"] == 0
    assert metrics["pending_review_count"] == 0


@pytest.mark.asyncio
async def test_get_dashboard_creates_initial_metrics(async_client, test_token):
    response1 = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response1.status_code == 200
    dashboard_id_1 = response1.json()["data"]["dashboard_id"]

    response2 = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response2.status_code == 200
    dashboard_id_2 = response2.json()["data"]["dashboard_id"]

    assert dashboard_id_1 == dashboard_id_2


@pytest.mark.asyncio
async def test_dashboard_response_format(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["meta"] is None
    assert "trace_id" in data


@pytest.mark.asyncio
async def test_dashboard_history_empty(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard/history",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["total"] >= 0


@pytest.mark.asyncio
async def test_dashboard_history_pagination(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard/history?limit=10&offset=0",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["meta"]["limit"] == 10
    assert data["meta"]["offset"] == 0
    assert len(data["data"]) <= 10
