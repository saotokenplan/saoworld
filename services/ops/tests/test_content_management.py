"""内容管理 API 测试。"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest


CONTENT_PKG_URL = "/api/v1/ops/content-packages"


@pytest.mark.asyncio
async def test_release_content_package_success(async_client, test_token):
    pkg_id = uuid.uuid4()
    with patch("app.core.content_service_client.ContentServiceClient.release_content_package", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"content_package_id": str(pkg_id), "status": "gray"}}
        resp = await async_client.post(
            f"{CONTENT_PKG_URL}/{pkg_id}/release",
            json={"release_mode": "gray"},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["detail"]["status"] == "gray"


@pytest.mark.asyncio
async def test_rollback_content_package_success(async_client, test_token):
    pkg_id = uuid.uuid4()
    with patch("app.core.content_service_client.ContentServiceClient.rollback_content_package", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"content_package_id": str(pkg_id), "status": "rolled_back"}}
        resp = await async_client.post(
            f"{CONTENT_PKG_URL}/{pkg_id}/rollback",
            json={"reason": "test rollback"},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_content_packages_success(async_client, test_token):
    with patch("app.core.content_service_client.ContentServiceClient.list_content_packages", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": [], "meta": {"total": 0, "limit": 20, "offset": 0}}
        resp = await async_client.get(
            CONTENT_PKG_URL,
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body


@pytest.mark.asyncio
async def test_get_content_package_detail_success(async_client, test_token):
    pkg_id = uuid.uuid4()
    with patch("app.core.content_service_client.ContentServiceClient.get_content_package_detail", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": {"content_package_id": str(pkg_id), "status": "live"}}
        resp = await async_client.get(
            f"{CONTENT_PKG_URL}/{pkg_id}",
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_content_release_upstream_error(async_client, test_token):
    pkg_id = uuid.uuid4()
    with patch("app.core.content_service_client.ContentServiceClient.release_content_package", new_callable=AsyncMock) as mock:
        mock.side_effect = Exception("Connection refused")
        resp = await async_client.post(
            f"{CONTENT_PKG_URL}/{pkg_id}/release",
            json={"release_mode": "gray"},
            headers={"Authorization": f"Bearer {test_token}"},
        )
        assert resp.status_code == 502


@pytest.mark.asyncio
async def test_content_management_unauthorized(async_client):
    resp = await async_client.get(CONTENT_PKG_URL)
    assert resp.status_code in (401, 403)
