import pytest


@pytest.mark.asyncio
async def test_no_token_returns_401(async_client):
    response = await async_client.get("/api/v1/ops/dashboard")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "MISSING_TOKEN"


@pytest.mark.asyncio
async def test_invalid_token_returns_401(async_client):
    response = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "INVALID_TOKEN"


@pytest.mark.asyncio
async def test_player_token_no_scope_returns_403(async_client, player_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_ops_token_valid_scope_returns_200(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_auth_error_response_format(async_client):
    response = await async_client.get("/api/v1/ops/dashboard")
    assert response.status_code == 401
    data = response.json()

    assert "code" in data
    assert "message" in data
    assert "request_id" in data


@pytest.mark.asyncio
async def test_request_id_header_present(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    assert "X-Request-Id" in response.headers


@pytest.mark.asyncio
async def test_trace_id_header_passed(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/dashboard",
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "test_trace_001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == "test_trace_001"
    assert response.headers.get("X-Trace-Id") == "test_trace_001"
