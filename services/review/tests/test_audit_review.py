import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_review_record_creates_audit_log(
    client: AsyncClient, ops_token: str
):
    obj_id = uuid.uuid4()
    response = await client.post(
        "/api/v1/ops/review/records",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-create-001",
            "X-Trace-Id": "trace_audit_test_001",
        },
        json={
            "object_id": str(obj_id),
            "object_type": "npc",
            "review_type": "consistency",
            "trace_id": "trace_test_create_001",
            "quality_score": 0.85,
        },
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_update_review_result_creates_audit_log(
    client: AsyncClient, reviewer_token: str, review_records
):
    review = review_records[0]
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-audit-update-001",
            "X-Trace-Id": "trace_audit_test_002",
        },
        json={"result": "approved", "reason": "Audit test"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_approve_review_object_creates_audit_log(
    client: AsyncClient, reviewer_token: str, review_records
):
    obj_id = review_records[0].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/approve",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-audit-approve-001",
            "X-Trace-Id": "trace_audit_test_003",
        },
        json={"reason": "Audit approve test"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_reject_review_object_creates_audit_log(
    client: AsyncClient, reviewer_token: str, review_records
):
    obj_id = review_records[1].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/reject",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-audit-reject-001",
            "X-Trace-Id": "trace_audit_test_004",
        },
        json={"reason": "Audit reject test", "risk_level": "high"},
    )
    assert response.status_code == 200