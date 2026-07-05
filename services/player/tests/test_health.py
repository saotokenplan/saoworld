import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get(f"{settings.api_v1_prefix}/health")
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["service"] == settings.app_name
    assert data["data"]["version"] == settings.app_version
    assert data["data"]["status"] == "ok"


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
    assert "players_total" in content
    assert "player_operations_total" in content
    assert "player_quests_by_status" in content


@pytest.mark.asyncio
async def test_player_create_metric_incremented(client: AsyncClient, ops_token: str):
    """创建玩家后，player_operations_total{action="create"} 计数器应递增。"""
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
        metrics_before, "player_operations_total", 'action="create"'
    )

    create_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/players",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "metric-test-player-create-001",
        },
        json={"display_name": "MetricPlayer", "chapter_id": "ch_prologue_01"},
    )
    assert create_resp.status_code == 201

    metrics_after = (await client.get("/metrics")).text
    after = _extract_labeled_counter(
        metrics_after, "player_operations_total", 'action="create"'
    )
    assert after > before


@pytest.mark.asyncio
async def test_player_update_metric_incremented(client: AsyncClient, ops_token: str, test_player):
    """更新玩家后，player_operations_total{action="update"} 计数器应递增。"""
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
        metrics_before, "player_operations_total", 'action="update"'
    )

    update_resp = await client.put(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "metric-test-player-update-001",
        },
        json={"display_name": "UpdatedMetricPlayer"},
    )
    assert update_resp.status_code == 200

    metrics_after = (await client.get("/metrics")).text
    after = _extract_labeled_counter(
        metrics_after, "player_operations_total", 'action="update"'
    )
    assert after > before


@pytest.mark.asyncio
async def test_region_unlock_metric_incremented(client: AsyncClient, ops_token: str, test_player):
    """解锁区域后，player_operations_total{action="unlock_region"} 计数器应递增。"""
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
        metrics_before, "player_operations_total", 'action="unlock_region"'
    )

    unlock_resp = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/regions/region_metric_01/unlock",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "metric-test-region-unlock-001",
        },
    )
    assert unlock_resp.status_code == 200

    metrics_after = (await client.get("/metrics")).text
    after = _extract_labeled_counter(
        metrics_after, "player_operations_total", 'action="unlock_region"'
    )
    assert after > before
