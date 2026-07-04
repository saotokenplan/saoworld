import pytest


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "gateway-service"
        assert data["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_health_check_no_auth_required(self, client):
        response = await client.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_services_health(self, client):
        response = await client.get("/api/v1/health/services")
        assert response.status_code == 200
        data = response.json()
        assert data["gateway"]["status"] == "ok"
        assert len(data["services"]) == 5

    @pytest.mark.asyncio
    async def test_request_id_header(self, client):
        response = await client.get("/api/v1/health")
        assert response.headers.get("X-Request-Id") is not None

    @pytest.mark.asyncio
    async def test_custom_request_id(self, client):
        custom_id = "req_test_12345"
        response = await client.get("/api/v1/health", headers={"X-Request-Id": custom_id})
        assert response.headers["X-Request-Id"] == custom_id

    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, client):
        response = await client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        assert "http_requests_total" in content
        assert "http_request_duration_seconds" in content