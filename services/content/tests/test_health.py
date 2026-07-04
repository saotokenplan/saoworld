import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["service"] == "content-service"
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
    assert "content_package_operations_total" in content
    assert "content_releases_total" in content
    assert "content_rollbacks_total" in content
    assert "content_packages_by_status" in content


@pytest.mark.asyncio
async def test_package_create_metric_incremented(
    client: AsyncClient, ops_token: str
):
    """创建内容包后，content_package_operations_total{action="create"} 计数器应递增。"""
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
        metrics_before, "content_package_operations_total", 'action="create"'
    )

    response = await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": f"metric-test-pkg-{uuid.uuid4().hex}",
        },
        json={
            "chapter_id": "ch_metric_test",
            "region_id": str(uuid.uuid4()),
            "package_version": f"pkg_metric_{uuid.uuid4().hex[:8]}",
            "title": "指标测试内容包",
            "summary": "用于业务指标测试",
            "payload": {"test": True},
            "schema_version": 1,
        },
    )
    assert response.status_code == 201

    metrics_after = (await client.get("/metrics")).text
    after = _extract_labeled_counter(
        metrics_after, "content_package_operations_total", 'action="create"'
    )
    assert after > before
