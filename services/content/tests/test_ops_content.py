import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_package_success(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-001",
            "X-Trace-Id": "trace_create_001",
        },
        json={
            "chapter_id": "chapter_03",
            "package_version": "pkg_ch03_20260701_01",
            "title": "第三章新内容包",
            "summary": "第三章的全新内容",
            "payload": {"test": "data", "chapter": 3},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "content_package_id" in data["data"]
    assert data["data"]["chapter_id"] == "chapter_03"
    assert data["data"]["title"] == "第三章新内容包"
    assert data["data"]["status"] == "packaged"
    assert data["data"]["package_version"] == "pkg_ch03_20260701_01"
    assert data["trace_id"] == "trace_create_001"


@pytest.mark.asyncio
async def test_create_package_envelope_format(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-002",
        },
        json={
            "chapter_id": "chapter_03",
            "package_version": "pkg_ch03_20260701_02",
            "title": "格式测试内容包",
            "payload": {"test": "data"},
        },
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "trace_id" in data


@pytest.mark.asyncio
async def test_create_package_missing_title(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-003",
        },
        json={
            "chapter_id": "chapter_03",
            "package_version": "pkg_ch03_20260701_03",
            "payload": {"test": "data"},
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_gray_release_success(client: AsyncClient, ops_token: str, content_packages):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.post(
        f"/api/v1/ops/content-packages/{packaged_package.content_package_id}/release",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-release-gray-001",
            "X-Trace-Id": "trace_release_gray_001",
        },
        json={
            "release_mode": "gray",
            "gray_scope": {"player_percent": 10},
            "reason": "灰度发布测试",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "gray"
    assert data["data"]["release_mode"] == "gray"
    assert data["trace_id"] == "trace_release_gray_001"


@pytest.mark.asyncio
async def test_full_release_success(client: AsyncClient, ops_token: str, content_packages):
    gray_package = next(p for p in content_packages if p.status == "gray")
    response = await client.post(
        f"/api/v1/ops/content-packages/{gray_package.content_package_id}/release",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-release-full-001",
            "X-Trace-Id": "trace_release_full_001",
        },
        json={
            "release_mode": "full",
            "reason": "全量发布测试",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "live"
    assert data["data"]["release_mode"] == "full"
    assert data["trace_id"] == "trace_release_full_001"


@pytest.mark.asyncio
async def test_invalid_transition_packaged_to_live(client: AsyncClient, ops_token: str, content_packages):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.post(
        f"/api/v1/ops/content-packages/{packaged_package.content_package_id}/release",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-release-invalid-001",
        },
        json={
            "release_mode": "full",
            "reason": "直接全量发布（应失败）",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "INVALID_PACKAGE_STATE"


@pytest.mark.asyncio
async def test_gray_rollback_success(client: AsyncClient, ops_token: str, content_packages):
    gray_package = next(p for p in content_packages if p.status == "gray")
    response = await client.post(
        f"/api/v1/ops/content-packages/{gray_package.content_package_id}/rollback",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-rollback-gray-001",
            "X-Trace-Id": "trace_rollback_gray_001",
        },
        json={
            "target_version": "pkg_ch01_20260701_01",
            "reason": "灰度回滚测试",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "rolled_back"
    assert data["data"]["target_version"] == "pkg_ch01_20260701_01"
    assert data["trace_id"] == "trace_rollback_gray_001"


@pytest.mark.asyncio
async def test_live_rollback_success(client: AsyncClient, ops_token: str, content_packages):
    live_package = next(p for p in content_packages if p.status == "live")
    response = await client.post(
        f"/api/v1/ops/content-packages/{live_package.content_package_id}/rollback",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-rollback-live-001",
            "X-Trace-Id": "trace_rollback_live_001",
        },
        json={
            "target_version": "pkg_ch01_20260625_01",
            "reason": "全量回滚测试",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "rolled_back"
    assert data["data"]["target_version"] == "pkg_ch01_20260625_01"
    assert data["trace_id"] == "trace_rollback_live_001"


@pytest.mark.asyncio
async def test_rolled_back_cannot_release(client: AsyncClient, ops_token: str, content_packages):
    rolled_back_package = next(p for p in content_packages if p.status == "rolled_back")
    response = await client.post(
        f"/api/v1/ops/content-packages/{rolled_back_package.content_package_id}/release",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-release-rolled-back-001",
        },
        json={
            "release_mode": "gray",
            "reason": "尝试重新发布已回滚的包（应失败）",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "INVALID_PACKAGE_STATE"


@pytest.mark.asyncio
async def test_release_reason_required(client: AsyncClient, ops_token: str, content_packages):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.post(
        f"/api/v1/ops/content-packages/{packaged_package.content_package_id}/release",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-release-no-reason-001",
        },
        json={
            "release_mode": "gray",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_rollback_reason_required(client: AsyncClient, ops_token: str, content_packages):
    gray_package = next(p for p in content_packages if p.status == "gray")
    response = await client.post(
        f"/api/v1/ops/content-packages/{gray_package.content_package_id}/rollback",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-rollback-no-reason-001",
        },
        json={
            "target_version": "v1.0.0",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_release_package_not_found(client: AsyncClient, ops_token: str):
    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/ops/content-packages/{fake_id}/release",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-release-not-found-001",
        },
        json={
            "release_mode": "gray",
            "reason": "测试不存在的包",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "PACKAGE_NOT_FOUND"


@pytest.mark.asyncio
async def test_rollback_package_not_found(client: AsyncClient, ops_token: str):
    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/ops/content-packages/{fake_id}/rollback",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-rollback-not-found-001",
        },
        json={
            "target_version": "v1.0.0",
            "reason": "测试不存在的包",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "PACKAGE_NOT_FOUND"


@pytest.mark.asyncio
async def test_rollback_packaged_invalid(client: AsyncClient, ops_token: str, content_packages):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.post(
        f"/api/v1/ops/content-packages/{packaged_package.content_package_id}/rollback",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-rollback-packaged-001",
        },
        json={
            "target_version": "v1.0.0",
            "reason": "回滚未发布的包（应失败）",
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "INVALID_PACKAGE_STATE"


@pytest.mark.asyncio
async def test_release_envelope_format(client: AsyncClient, ops_token: str, content_packages):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.post(
        f"/api/v1/ops/content-packages/{packaged_package.content_package_id}/release",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-release-format-001",
        },
        json={
            "release_mode": "gray",
            "reason": "格式测试",
        },
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "trace_id" in data


@pytest.mark.asyncio
async def test_rollback_envelope_format(client: AsyncClient, ops_token: str, content_packages):
    gray_package = next(p for p in content_packages if p.status == "gray")
    response = await client.post(
        f"/api/v1/ops/content-packages/{gray_package.content_package_id}/rollback",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-rollback-format-001",
        },
        json={
            "target_version": "v1.0.0",
            "reason": "格式测试",
        },
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "trace_id" in data


@pytest.mark.asyncio
async def test_create_package_player_forbidden(client: AsyncClient, player_token: str):
    response = await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-create-player-001",
        },
        json={
            "chapter_id": "chapter_03",
            "package_version": "pkg_ch03_20260701_04",
            "title": "玩家创建测试",
            "payload": {"test": "data"},
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_release_package_player_forbidden(client: AsyncClient, player_token: str, content_packages):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.post(
        f"/api/v1/ops/content-packages/{packaged_package.content_package_id}/release",
        headers={
            "Authorization": f"Bearer {player_token}",
            "Idempotency-Key": "test-release-player-001",
        },
        json={
            "release_mode": "gray",
            "reason": "玩家发布测试",
        },
    )
    assert response.status_code == 403
