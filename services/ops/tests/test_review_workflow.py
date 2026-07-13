"""审核工作流 API 测试。"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest


REVIEW_URL = "/api/v1/ops/review"


@pytest.mark.asyncio
async def test_approve_review_object_success(async_client, test_token):
    obj_id = uuid.uuid4()
    with patch("app.core.review_service_client.ReviewServiceClient.approve_review_object", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"object_id": str(obj_id), "status": "approved"}}
        resp = await async_client.post(
            f"{REVIEW_URL}/{obj_id}/approve",
            json={"notes": "looks good"},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["detail"]["status"] == "approved"


@pytest.mark.asyncio
async def test_reject_review_object_success(async_client, test_token):
    obj_id = uuid.uuid4()
    with patch("app.core.review_service_client.ReviewServiceClient.reject_review_object", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"object_id": str(obj_id), "status": "rejected"}}
        resp = await async_client.post(
            f"{REVIEW_URL}/{obj_id}/reject",
            json={"reason": "inappropriate content"},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_review_objects_success(async_client, test_token):
    with patch("app.core.review_service_client.ReviewServiceClient.list_review_objects", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": [], "meta": {"total": 0, "limit": 20, "offset": 0}}
        resp = await async_client.get(
            f"{REVIEW_URL}/objects",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body


@pytest.mark.asyncio
async def test_get_review_stats_success(async_client, test_token):
    with patch("app.core.review_service_client.ReviewServiceClient.get_review_stats", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"total_pending": 5, "total_approved": 10, "total_rejected": 2, "total_needs_revision": 1}}
        resp = await async_client.get(
            f"{REVIEW_URL}/stats",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total_pending"] == 5


@pytest.mark.asyncio
async def test_review_approve_upstream_error(async_client, test_token):
    obj_id = uuid.uuid4()
    with patch("app.core.review_service_client.ReviewServiceClient.approve_review_object", new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("Connection refused")
        resp = await async_client.post(
            f"{REVIEW_URL}/{obj_id}/approve",
            json={"notes": "test"},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 502


@pytest.mark.asyncio
async def test_review_workflow_unauthorized(async_client):
    resp = await async_client.get(f"{REVIEW_URL}/objects")
    assert resp.status_code in (401, 403)
