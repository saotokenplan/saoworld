import uuid

import pytest


@pytest.mark.asyncio
async def test_get_ops_actions_empty(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/actions",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_ops_actions_with_filter(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/actions?action_type=vote_cycle_create",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert "data" in data


@pytest.mark.asyncio
async def test_get_ops_actions_pagination(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/actions?limit=5&offset=0",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["meta"]["limit"] == 5
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_get_ops_action_detail_not_found(async_client, test_token):
    fake_id = uuid.uuid4()
    response = await async_client.get(
        f"/api/v1/ops/actions/{fake_id}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "ACTION_NOT_FOUND"


@pytest.mark.asyncio
async def test_ops_actions_response_format(async_client, test_token):
    response = await async_client.get(
        "/api/v1/ops/actions",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert "trace_id" in data
