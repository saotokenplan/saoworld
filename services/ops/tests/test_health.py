import pytest


@pytest.mark.asyncio
async def test_health_check(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["service"] == "ops-service"
    assert data["data"]["version"] == "0.1.0"
    assert data["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_response_format(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["meta"] is None
    assert "trace_id" in data


@pytest.mark.asyncio
async def test_metrics_endpoint(async_client):
    response = await async_client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
