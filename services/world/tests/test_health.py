import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["service"] == "world-service"
    assert data["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_check_envelope_format(client: AsyncClient):
    response = await client.get("/api/v1/health")
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["request_id"].startswith("req_health_")


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    response = await client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
