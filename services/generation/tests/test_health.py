import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["service"] == "generation-service"
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


@pytest.mark.asyncio
async def test_business_metrics_exposed(client: AsyncClient):
    """业务指标名应出现在 /metrics 端点输出中。"""
    response = await client.get("/metrics")
    assert response.status_code == 200
    content = response.text
    assert "generation_requests_total" in content
    assert "generated_objects_total" in content
    assert "generation_requests_by_status" in content


@pytest.mark.asyncio
async def test_generation_request_create_metric_incremented(
    client: AsyncClient, ops_token: str
):
    """创建生成请求后，generation_requests_total{status="pending"} 计数器应递增。"""
    metrics_before = (await client.get("/metrics")).text

    def _extract_labeled_counter(text: str, name: str, label_filter: str) -> float:
        for line in text.splitlines():
            if line.startswith(name) and label_filter in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return float(parts[1])
                    except ValueError:
                        continue
        return 0.0

    before = _extract_labeled_counter(
        metrics_before, "generation_requests_total", 'status="pending"'
    )

    response = await client.post(
        "/api/v1/ops/generation/requests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "metric-test-gen-request-create",
        },
        json={
            "template_id": "tpl_npc_v2",
            "input_payload": {"region": "wasteland", "count": 5},
            "trace_id": "trace_metric_test_create",
        },
    )
    assert response.status_code == 201

    metrics_after = (await client.get("/metrics")).text
    after = _extract_labeled_counter(
        metrics_after, "generation_requests_total", 'status="pending"'
    )
    assert after > before

