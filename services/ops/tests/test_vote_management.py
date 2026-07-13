"""投票管理 API 测试。"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest


VOTE_CYCLE_URL = "/api/v1/ops/vote-cycles"


@pytest.mark.asyncio
async def test_create_vote_cycle_success(async_client, test_token):
    with patch("app.core.vote_service_client.VoteServiceClient.create_vote_cycle", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"vote_cycle_id": str(uuid.uuid4()), "status": "draft"}}
        resp = await async_client.post(
            VOTE_CYCLE_URL,
            json={"chapter_id": "chapter_01", "title": "Test Cycle"},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert body["data"]["detail"]["status"] == "draft"


@pytest.mark.asyncio
async def test_schedule_vote_cycle_success(async_client, test_token):
    cycle_id = uuid.uuid4()
    with patch("app.core.vote_service_client.VoteServiceClient.schedule_vote_cycle", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"vote_cycle_id": str(cycle_id), "status": "scheduled"}}
        resp = await async_client.post(
            f"{VOTE_CYCLE_URL}/{cycle_id}/schedule",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["detail"]["status"] == "scheduled"


@pytest.mark.asyncio
async def test_open_vote_cycle_success(async_client, test_token):
    cycle_id = uuid.uuid4()
    with patch("app.core.vote_service_client.VoteServiceClient.open_vote_cycle", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"vote_cycle_id": str(cycle_id), "status": "open"}}
        resp = await async_client.post(
            f"{VOTE_CYCLE_URL}/{cycle_id}/open",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_close_vote_cycle_success(async_client, test_token):
    cycle_id = uuid.uuid4()
    with patch("app.core.vote_service_client.VoteServiceClient.close_vote_cycle", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"vote_cycle_id": str(cycle_id), "status": "closed"}}
        resp = await async_client.post(
            f"{VOTE_CYCLE_URL}/{cycle_id}/close",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_finalize_vote_cycle_success(async_client, test_token):
    cycle_id = uuid.uuid4()
    with patch("app.core.vote_service_client.VoteServiceClient.finalize_vote_cycle", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"vote_cycle_id": str(cycle_id), "status": "finalized"}}
        resp = await async_client.post(
            f"{VOTE_CYCLE_URL}/{cycle_id}/finalize",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_vote_cycles_success(async_client, test_token):
    with patch("app.core.vote_service_client.VoteServiceClient.list_vote_cycles", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": [], "meta": {"total": 0, "limit": 20, "offset": 0}}
        resp = await async_client.get(
            VOTE_CYCLE_URL,
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_vote_cycle_upstream_error(async_client, test_token):
    with patch("app.core.vote_service_client.VoteServiceClient.create_vote_cycle", new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("Connection refused")
        resp = await async_client.post(
            VOTE_CYCLE_URL,
            json={"chapter_id": "chapter_01", "title": "Test Cycle"},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 502


@pytest.mark.asyncio
async def test_vote_cycle_unauthorized(async_client):
    resp = await async_client.post(
        VOTE_CYCLE_URL,
        json={"chapter_id": "chapter_01", "title": "Test Cycle"},
    )
    assert resp.status_code in (401, 403)
