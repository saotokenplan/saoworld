import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.domain.models import AuditLog


@pytest.mark.asyncio
async def test_create_generation_request_creates_audit_log(
    client: AsyncClient, ops_token: str
):
    response = await client.post(
        "/api/v1/ops/generation/requests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-001",
            "X-Trace-Id": "trace_audit_001",
        },
        json={
            "template_id": "tpl_npc_v2",
            "input_payload": {"test": "data"},
            "trace_id": "trace_audit_001",
        },
    )
    assert response.status_code == 201

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb_generation?mode=memory&cache=shared&uri=true"
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            select(AuditLog).where(AuditLog.action == "generation_request_create")
        )
        audit_logs = list(result.scalars().all())
        assert len(audit_logs) >= 1
        audit = audit_logs[-1]
        assert audit.action == "generation_request_create"
        assert audit.operator_role == "ops"
        assert audit.resource_type == "generation_request"
        assert audit.result_status == 201


@pytest.mark.asyncio
async def test_update_request_status_creates_audit_log(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[0]
    response = await client.post(
        f"/api/v1/ops/generation/requests/{req.request_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-002",
            "X-Trace-Id": "trace_audit_002",
        },
        json={"status": "processing"},
    )
    assert response.status_code == 200

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb_generation?mode=memory&cache=shared&uri=true"
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == "generation_request_status_update"
            )
        )
        audit_logs = list(result.scalars().all())
        assert len(audit_logs) >= 1
        audit = audit_logs[-1]
        assert audit.action == "generation_request_status_update"
        assert str(audit.resource_id) == str(req.request_id)


@pytest.mark.asyncio
async def test_update_object_status_creates_audit_log(
    client: AsyncClient, ops_token: str, generated_objects
):
    obj = generated_objects[0]
    response = await client.post(
        f"/api/v1/ops/generation/objects/{obj.object_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-003",
            "X-Trace-Id": "trace_audit_003",
        },
        json={"status": "approved"},
    )
    assert response.status_code == 200

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb_generation?mode=memory&cache=shared&uri=true"
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == "generated_object_status_update"
            )
        )
        audit_logs = list(result.scalars().all())
        assert len(audit_logs) >= 1
        audit = audit_logs[-1]
        assert audit.action == "generated_object_status_update"
        assert str(audit.resource_id) == str(obj.object_id)
        assert audit.resource_type == "generated_object"


@pytest.mark.asyncio
async def test_audit_log_has_trace_id(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[0]
    trace_id = "trace_audit_test_004"
    response = await client.post(
        f"/api/v1/ops/generation/requests/{req.request_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-004",
            "X-Trace-Id": trace_id,
        },
        json={"status": "processing"},
    )
    assert response.status_code == 200

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb_generation?mode=memory&cache=shared&uri=true"
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == "generation_request_status_update"
            )
        )
        audit_logs = list(result.scalars().all())
        audit = audit_logs[-1]
        assert audit.trace_id == trace_id


@pytest.mark.asyncio
async def test_audit_log_operator_id(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[0]
    response = await client.post(
        f"/api/v1/ops/generation/requests/{req.request_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-005",
        },
        json={"status": "processing"},
    )
    assert response.status_code == 200

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    TEST_DATABASE_URL = "sqlite+aiosqlite:///file:testdb_generation?mode=memory&cache=shared&uri=true"
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.action == "generation_request_status_update"
            )
        )
        audit_logs = list(result.scalars().all())
        audit = audit_logs[-1]
        assert audit.operator_id == "test_ops_user"
        assert audit.operator_role == "ops"
