import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.domain.models import AuditLog
from app.repositories.audit_repo import (
    ACTION_PACKAGE_CREATE,
    ACTION_PACKAGE_RELEASE,
    ACTION_PACKAGE_ROLLBACK,
    RESOURCE_CONTENT_PACKAGE,
)
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_create_package_audit_log(client: AsyncClient, ops_token: str):
    trace_id = "trace_audit_create_001"
    response = await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-create-001",
            "X-Trace-Id": trace_id,
        },
        json={
            "chapter_id": "chapter_audit",
            "package_version": "pkg_audit_001",
            "title": "审计测试内容包",
            "summary": "用于审计日志测试的内容包",
            "payload": {"test": "audit"},
        },
    )
    assert response.status_code == 201

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == ACTION_PACKAGE_CREATE)
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

        log = logs[-1]
        assert log.operator_id == "test_ops_user"
        assert log.operator_role == "ops"
        assert log.action == ACTION_PACKAGE_CREATE
        assert log.resource_type == RESOURCE_CONTENT_PACKAGE
        assert log.trace_id == trace_id
        assert log.result_status == 201
        assert log.resource_id is not None
        assert log.request_payload_jsonb is not None
        assert "chapter_id" in log.request_payload_jsonb
        assert log.request_payload_jsonb["chapter_id"] == "chapter_audit"


@pytest.mark.asyncio
async def test_release_package_audit_log(client: AsyncClient, ops_token: str, content_packages):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    trace_id = "trace_audit_release_001"

    response = await client.post(
        f"/api/v1/ops/content-packages/{packaged_package.content_package_id}/release",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-release-001",
            "X-Trace-Id": trace_id,
        },
        json={
            "release_mode": "gray",
            "gray_scope": {"player_percent": 10},
            "reason": "灰度发布审计测试",
        },
    )
    assert response.status_code == 200

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == ACTION_PACKAGE_RELEASE)
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

        log = logs[-1]
        assert log.operator_id == "test_ops_user"
        assert log.operator_role == "ops"
        assert log.action == ACTION_PACKAGE_RELEASE
        assert log.resource_type == RESOURCE_CONTENT_PACKAGE
        assert str(log.resource_id) == str(packaged_package.content_package_id)
        assert log.reason == "灰度发布审计测试"
        assert log.trace_id == trace_id
        assert log.result_status == 200
        assert log.request_payload_jsonb is not None
        assert log.request_payload_jsonb["from_status"] == "packaged"
        assert log.request_payload_jsonb["to_status"] == "gray"
        assert log.request_payload_jsonb["release_mode"] == "gray"


@pytest.mark.asyncio
async def test_rollback_package_audit_log(client: AsyncClient, ops_token: str, content_packages):
    gray_package = next(p for p in content_packages if p.status == "gray")
    trace_id = "trace_audit_rollback_001"

    response = await client.post(
        f"/api/v1/ops/content-packages/{gray_package.content_package_id}/rollback",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-rollback-001",
            "X-Trace-Id": trace_id,
        },
        json={
            "target_version": "pkg_rollback_target_001",
            "reason": "回滚审计测试",
        },
    )
    assert response.status_code == 200

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == ACTION_PACKAGE_ROLLBACK)
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

        log = logs[-1]
        assert log.operator_id == "test_ops_user"
        assert log.operator_role == "ops"
        assert log.action == ACTION_PACKAGE_ROLLBACK
        assert log.resource_type == RESOURCE_CONTENT_PACKAGE
        assert str(log.resource_id) == str(gray_package.content_package_id)
        assert log.reason == "回滚审计测试"
        assert log.trace_id == trace_id
        assert log.result_status == 200
        assert log.request_payload_jsonb is not None
        assert log.request_payload_jsonb["from_status"] == "gray"
        assert log.request_payload_jsonb["to_status"] == "rolled_back"
        assert log.request_payload_jsonb["target_version"] == "pkg_rollback_target_001"


@pytest.mark.asyncio
async def test_audit_log_has_created_at(client: AsyncClient, ops_token: str):
    await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-timestamp-001",
        },
        json={
            "chapter_id": "chapter_timestamp",
            "package_version": "pkg_timestamp_001",
            "title": "时间戳测试内容包",
            "payload": {"test": "timestamp"},
        },
    )

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == ACTION_PACKAGE_CREATE)
        )
        logs = result.scalars().all()
        assert len(logs) >= 1
        assert logs[-1].created_at is not None


@pytest.mark.asyncio
async def test_create_package_audit_log_no_trace_id(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/content-packages",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-no-trace-001",
        },
        json={
            "chapter_id": "chapter_no_trace",
            "package_version": "pkg_no_trace_001",
            "title": "无trace_id测试内容包",
            "payload": {"test": "no_trace"},
        },
    )
    assert response.status_code == 201

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == ACTION_PACKAGE_CREATE)
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

        log = logs[-1]
        assert log.trace_id.startswith("trace_")
