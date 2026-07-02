import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["service"] == "review-service"
    assert data["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_check_envelope_format(client: AsyncClient):
    response = await client.get("/api/v1/health")
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["request_id"].startswith("req_health_")