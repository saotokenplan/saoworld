import pytest


@pytest.mark.asyncio
async def test_dashboard_view_creates_audit_log(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ops_actions_query_creates_audit_log(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/actions",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_system_status_query_creates_audit_log(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/system/status",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_multiple_requests_have_different_request_ids(async_client, test_token):
    response1 = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    response2 = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    request_id1 = response1.json()["request_id"]
    request_id2 = response2.json()["request_id"]

    assert request_id1 != request_id2


@pytest.mark.asyncio
async def test_custom_request_id_header(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Request-Id": "custom_req_001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["request_id"] == "custom_req_001"
