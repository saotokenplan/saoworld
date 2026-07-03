import pytest


@pytest.mark.asyncio
async def test_all_endpoints_return_envelope_format(async_client, test_token):
    endpoints = [
        "/api/v1/health",
        "/api/v1/ops/dashboard",
        "/api/v1/ops/dashboard/history",
        "/api/v1/ops/actions",
        "/api/v1/ops/system/status",
    ]

    for endpoint in endpoints:
        response = await async_client.get(
            endpoint,
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200, f"Endpoint {endpoint} failed"

        data = response.json()
        assert "request_id" in data, f"Missing request_id in {endpoint}"
        assert "data" in data, f"Missing data in {endpoint}"
        assert "meta" in data, f"Missing meta in {endpoint}"
        assert "trace_id" in data, f"Missing trace_id in {endpoint}"


@pytest.mark.asyncio
async def test_error_endpoint_returns_envelope_format(async_client):
    response = await async_client.get("/api/v1/ops/dashboard")
    assert response.status_code == 401

    data = response.json()
    assert "code" in data
    assert "message" in data
    assert "request_id" in data


@pytest.mark.asyncio
async def test_paginated_endpoints_have_meta(async_client, test_token):
    endpoints = [
        "/api/v1/ops/dashboard/history",
        "/api/v1/ops/actions",
    ]

    for endpoint in endpoints:
        response = await async_client.get(
            endpoint,
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["meta"] is not None
        assert "total" in data["meta"]
        assert "limit" in data["meta"]
        assert "offset" in data["meta"]


@pytest.mark.asyncio
async def test_non_paginated_endpoints_have_null_meta(async_client, test_token):
    endpoints = [
        "/api/v1/health",
        "/api/v1/ops/dashboard",
        "/api/v1/ops/system/status",
    ]

    for endpoint in endpoints:
        response = await async_client.get(
            endpoint,
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["meta"] is None
