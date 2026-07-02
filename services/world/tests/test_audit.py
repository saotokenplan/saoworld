
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.domain.models import AuditLog
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_create_region_audit_log(client: AsyncClient, ops_token: str):
    response = await client.post(
        "/api/v1/ops/world/regions",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-001",
            "X-Trace-Id": "trace_audit_001",
        },
        json={
            "chapter_id": "ch_01",
            "title": "审计测试区域",
        },
    )
    assert response.status_code == 201

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == "region_create")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

        log = logs[-1]
        assert log.operator_id == "test_ops_user"
        assert log.operator_role == "ops"
        assert log.action == "region_create"
        assert log.resource_type == "region"
        assert log.trace_id == "trace_audit_001"
        assert log.result_status == 201
        assert log.resource_id is not None


@pytest.mark.asyncio
async def test_update_region_status_audit_log(
    client: AsyncClient, ops_token: str, visible_regions
):
    region = visible_regions[0]

    response = await client.post(
        f"/api/v1/ops/world/regions/{region.region_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-002",
            "X-Trace-Id": "trace_audit_002",
        },
        json={
            "status": "unstable",
            "reason": "剧情推进",
        },
    )
    assert response.status_code == 200

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == "region_status_update")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1

        log = logs[-1]
        assert log.operator_id == "test_ops_user"
        assert log.operator_role == "ops"
        assert log.action == "region_status_update"
        assert log.resource_type == "region"
        assert str(log.resource_id) == str(region.region_id)
        assert log.reason == "剧情推进"
        assert log.trace_id == "trace_audit_002"
        assert log.result_status == 200
        assert log.request_payload_jsonb is not None
        assert log.request_payload_jsonb["from_status"] == "active"
        assert log.request_payload_jsonb["to_status"] == "unstable"


@pytest.mark.asyncio
async def test_audit_log_has_created_at(client: AsyncClient, ops_token: str):
    await client.post(
        "/api/v1/ops/world/regions",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-003",
        },
        json={
            "chapter_id": "ch_01",
            "title": "时间戳测试区域",
        },
    )

    async with TestSessionLocal() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == "region_create")
        )
        logs = result.scalars().all()
        assert len(logs) >= 1
        assert logs[-1].created_at is not None
