import pytest


@pytest.mark.asyncio
async def test_get_system_status(async_client, test_token):
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
        assert service["status"] == "ok"


@pytest.mark.asyncio
async def test_system_status_response_format(async_client, test_token):
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
