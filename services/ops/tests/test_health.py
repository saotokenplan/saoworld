import pytest

from app.core.config import settings


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


@pytest.mark.asyncio
async def test_business_metrics_exposed(async_client):
    """业务指标名应出现在 /metrics 端点输出中。"""
    response = await async_client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "ops_actions_total" in content
    assert "ops_dashboard_views_total" in content


@pytest.mark.asyncio
async def test_dashboard_view_metric_incremented(async_client, test_token: str):
    """访问仪表盘后，ops_dashboard_views_total 计数器应递增。"""
    metrics_before = (await async_client.get("/metrics")).text

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

    before = _extract_counter_value(metrics_before, "ops_dashboard_views_total")

    dashboard_resp = await async_client.get(
        f"{settings.api_v1_prefix}/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert dashboard_resp.status_code == 200

    metrics_after = (await async_client.get("/metrics")).text
    after = _extract_counter_value(metrics_after, "ops_dashboard_views_total")
    assert after > before
