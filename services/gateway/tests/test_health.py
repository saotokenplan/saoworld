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

    @pytest.mark.asyncio
    async def test_business_metrics_exposed(self, client):
        """业务指标名应出现在 /metrics 端点输出中。"""
        response = await client.get("/metrics")
        assert response.status_code == 200
        content = response.text
        assert "gateway_proxy_requests_total" in content
        assert "gateway_rate_limit_hits_total" in content
        assert "gateway_auth_failures_total" in content

    @pytest.mark.asyncio
    async def test_auth_failure_metric_incremented(self, client, invalid_token):
        """使用无效 Token 访问受保护接口，gateway_auth_failures_total 计数器应递增。"""

        def _extract_counter_value(text: str, name: str) -> float:
            for line in text.splitlines():
                if line.startswith(name) and not line.startswith(f"{name}_"):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            return float(parts[1])
                        except ValueError:
                            continue
            return 0.0

        metrics_before = (await client.get("/metrics")).text
        before = _extract_counter_value(metrics_before, "gateway_auth_failures_total")

        # 触发认证失败
        response = await client.get(
            "/api/v1/votes/current",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
        assert response.status_code == 401

        metrics_after = (await client.get("/metrics")).text
        after = _extract_counter_value(metrics_after, "gateway_auth_failures_total")
        assert after > before