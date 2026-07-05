import pytest
from unittest.mock import patch


@pytest.mark.asyncio
async def test_get_system_status(async_client, test_token):
    mock_results = {
        "vote-service": ("ok", "0.1.0"),
        "world-service": ("ok", "0.1.0"),
        "content-service": ("ok", "0.1.0"),
        "generation-service": ("ok", "0.1.0"),
        "review-service": ("ok", "0.1.0"),
        "gateway-service": ("ok", "0.1.0"),
        "player-service": ("ok", "0.1.0"),
        "ops-service": ("ok", "0.1.0"),
    }

    with patch("app.core.health_check_client.check_all_services_health", return_value=mock_results):
        response = await async_client.get(
            "/api/v1/ops/system/status",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert "request_id" in data
        assert "data" in data
        assert "services" in data["data"]
        assert "timestamp" in data["data"]


@pytest.mark.asyncio
async def test_system_status_service_list(async_client, test_token):
    mock_results = {
        "vote-service": ("ok", "0.1.0"),
        "world-service": ("ok", "0.1.0"),
        "content-service": ("ok", "0.1.0"),
        "generation-service": ("ok", "0.1.0"),
        "review-service": ("ok", "0.1.0"),
        "gateway-service": ("ok", "0.1.0"),
        "player-service": ("ok", "0.1.0"),
        "ops-service": ("ok", "0.1.0"),
    }

    with patch("app.core.health_check_client.check_all_services_health", return_value=mock_results):
        response = await async_client.get(
            "/api/v1/ops/system/status",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        services = data["data"]["services"]
        assert len(services) == 8

        service_names = [s["name"] for s in services]
        expected_services = [
            "vote-service",
            "world-service",
            "content-service",
            "generation-service",
            "review-service",
            "gateway-service",
            "player-service",
            "ops-service",
        ]
        assert sorted(service_names) == sorted(expected_services)


@pytest.mark.asyncio
async def test_system_status_each_service_has_fields(async_client, test_token):
    mock_results = {
        "vote-service": ("ok", "0.1.0"),
        "world-service": ("unavailable", "unknown"),
        "content-service": ("ok", "0.1.0"),
        "generation-service": ("ok", "0.1.0"),
        "review-service": ("ok", "0.1.0"),
        "gateway-service": ("ok", "0.1.0"),
        "player-service": ("ok", "0.1.0"),
        "ops-service": ("ok", "0.1.0"),
    }

    with patch("app.core.health_check_client.check_all_services_health", return_value=mock_results):
        response = await async_client.get(
            "/api/v1/ops/system/status",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        for service in data["data"]["services"]:
            assert "name" in service
            assert "status" in service
            assert "version" in service
            if service["name"] == "world-service":
                assert service["status"] == "unavailable"
                assert service["version"] == "unknown"
            else:
                assert service["status"] == "ok"
                assert service["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_system_status_response_format(async_client, test_token):
    mock_results = {
        "vote-service": ("ok", "0.1.0"),
        "world-service": ("ok", "0.1.0"),
        "content-service": ("ok", "0.1.0"),
        "generation-service": ("ok", "0.1.0"),
        "review-service": ("ok", "0.1.0"),
        "gateway-service": ("ok", "0.1.0"),
        "player-service": ("ok", "0.1.0"),
        "ops-service": ("ok", "0.1.0"),
    }

    with patch("app.core.health_check_client.check_all_services_health", return_value=mock_results):
        response = await async_client.get(
            "/api/v1/ops/system/status",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert response.status_code == 200
        data = response.json()

        assert "request_id" in data
        assert "data" in data
        assert "meta" in data
        assert data["meta"] is None
        assert "trace_id" in data