from httpx import AsyncClient

import pytest


@pytest.mark.asyncio
async def test_get_player_metrics_empty(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/player-metrics",
        params={"player_id": "player_test_001"},
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_analytics_001",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] is not None
    assert data["data"] == []
    assert data["meta"]["total"] == 0
    assert data["trace_id"] == "trace_test_analytics_001"


@pytest.mark.asyncio
async def test_get_player_metrics_requires_auth(async_client: AsyncClient) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/player-metrics",
        params={"player_id": "player_test_001"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_region_metrics_empty(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/region-metrics",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_analytics_002",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] is not None
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_region_metrics_with_filter(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/region-metrics",
        params={"region_id": "region_wasteland_01"},
        headers={
            "Authorization": f"Bearer {test_token}",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_trends_empty(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/trends",
        params={
            "metric_type": "region_visits",
            "time_range": "7d",
        },
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_analytics_003",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] is not None
    assert data["data"]["metric_type"] == "region_visits"
    assert data["data"]["time_range"] == "7d"
    assert data["data"]["trends"] == []


@pytest.mark.asyncio
async def test_get_trends_invalid_metric_type(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/trends",
        params={
            "metric_type": "invalid_type",
            "time_range": "7d",
        },
        headers={
            "Authorization": f"Bearer {test_token}",
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_analytics_reports_empty(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/reports",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_analytics_004",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] is not None
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_analytics_reports_with_filters(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/ops/analytics/reports",
        params={
            "report_type": "daily_summary",
            "status": "completed",
            "limit": 10,
            "offset": 0,
        },
        headers={
            "Authorization": f"Bearer {test_token}",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0
    assert data["meta"]["limit"] == 10


@pytest.mark.asyncio
async def test_analytics_endpoints_return_envelope_format(async_client: AsyncClient, test_token: str) -> None:
    endpoints = [
        ("/api/v1/ops/analytics/player-metrics", {"player_id": "p1"}),
        ("/api/v1/ops/analytics/region-metrics", {}),
        ("/api/v1/ops/analytics/trends", {"metric_type": "region_visits", "time_range": "7d"}),
        ("/api/v1/ops/analytics/reports", {}),
    ]

    for path, params in endpoints:
        response = await async_client.get(
            path,
            params=params,
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert "trace_id" in data
