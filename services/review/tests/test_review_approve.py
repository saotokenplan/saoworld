import uuid

import pytest
from httpx import AsyncClient

from app.core.errors import ReviewErrorCodes


@pytest.mark.asyncio
async def test_approve_review_object_success(
    client: AsyncClient, reviewer_token: str, review_records
):
    obj_id = review_records[0].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/approve",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-approve-001",
        },
        json={"reason": "All checks passed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["object_id"] == str(obj_id)
    assert data["data"]["result"] == "approved"


@pytest.mark.asyncio
async def test_approve_review_object_no_reviews_found(
    client: AsyncClient, reviewer_token: str
):
    fake_obj_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/ops/review/{fake_obj_id}/approve",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-approve-002",
        },
        json={},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == ReviewErrorCodes.NO_REVIEWS_FOUND


@pytest.mark.asyncio
async def test_approve_review_object_invalid_status(
    client: AsyncClient, reviewer_token: str, review_records
):
    obj_id = review_records[2].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/approve",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-approve-003",
        },
        json={},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ReviewErrorCodes.INVALID_REVIEW_STATUS


@pytest.mark.asyncio
async def test_reject_review_object_success(
    client: AsyncClient, reviewer_token: str, review_records
):
    obj_id = review_records[0].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/reject",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-reject-001",
        },
        json={"reason": "Content violation", "risk_level": "high"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["object_id"] == str(obj_id)
    assert data["data"]["result"] == "rejected"
    assert data["data"]["risk_level"] == "high"


@pytest.mark.asyncio
async def test_reject_review_object_no_reviews_found(
    client: AsyncClient, reviewer_token: str
):
    fake_obj_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/ops/review/{fake_obj_id}/reject",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-reject-002",
        },
        json={},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == ReviewErrorCodes.NO_REVIEWS_FOUND


@pytest.mark.asyncio
async def test_reject_review_object_invalid_status(
    client: AsyncClient, reviewer_token: str, review_records
):
    obj_id = review_records[3].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/reject",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-reject-003",
        },
        json={},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ReviewErrorCodes.INVALID_REVIEW_STATUS


@pytest.mark.asyncio
async def test_ops_can_approve_review_object(
    client: AsyncClient, ops_token: str, review_records
):
    obj_id = review_records[0].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/approve",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-ops-approve-001",
        },
        json={"reason": "Ops approval"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_ops_can_reject_review_object(
    client: AsyncClient, ops_token: str, review_records
):
    obj_id = review_records[1].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/reject",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-ops-reject-001",
        },
        json={"reason": "Ops rejection"},
    )
    assert response.status_code == 200