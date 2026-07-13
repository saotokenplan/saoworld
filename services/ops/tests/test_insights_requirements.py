import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_insights_empty(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/insights",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_insights_001",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] is not None
    assert data["data"] == []
    assert data["meta"]["total"] == 0
    assert data["trace_id"] == "trace_test_insights_001"


@pytest.mark.asyncio
async def test_get_insights_requires_auth(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/insights")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_insights_with_filters(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/insights",
        params={
            "category": "player_behavior",
            "min_confidence": "high",
            "min_impact": "high",
        },
        headers={
            "Authorization": f"Bearer {test_token}",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_insight_detail_not_found(async_client: AsyncClient, test_token: str) -> None:
    fake_id = uuid.uuid4()
    response = await async_client.get(
        f"/api/v1/insights/{fake_id}",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_insights_002",
        },
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "INSIGHT_NOT_FOUND"


@pytest.mark.asyncio
async def test_generate_requirement_from_insight_not_found(async_client: AsyncClient, test_token: str) -> None:
    fake_id = uuid.uuid4()
    response = await async_client.post(
        f"/api/v1/ops/insights/{fake_id}/generate-requirement",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_requirements_001",
        },
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "INSIGHT_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_requirements_empty(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/ops/requirements",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_requirements_002",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] is not None
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_requirements_with_filters(async_client: AsyncClient, test_token: str) -> None:
    response = await async_client.get(
        "/api/v1/ops/requirements",
        params={
            "status": "pending",
            "priority": "high",
            "target_scope": "content",
        },
        headers={
            "Authorization": f"Bearer {test_token}",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []


@pytest.mark.asyncio
async def test_get_requirement_detail_not_found(async_client: AsyncClient, test_token: str) -> None:
    fake_id = uuid.uuid4()
    response = await async_client.get(
        f"/api/v1/ops/requirements/{fake_id}",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_requirements_003",
        },
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "REQUIREMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_approve_requirement_not_found(async_client: AsyncClient, test_token: str) -> None:
    fake_id = uuid.uuid4()
    response = await async_client.post(
        f"/api/v1/ops/requirements/{fake_id}/approve",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_requirements_004",
        },
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "REQUIREMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_insights_endpoints_return_envelope_format(async_client: AsyncClient, test_token: str) -> None:
    endpoints = [
        ("/api/v1/insights", {}),
        ("/api/v1/ops/requirements", {}),
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
