import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_review_records_success(
    client: AsyncClient, ops_token: str, review_records
):
    response = await client.get(
        "/api/v1/ops/review/records",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["total"] == 5
    assert len(data["data"]["reviews"]) == 5
    assert data["meta"]["total"] == 5
    assert data["meta"]["limit"] == 20
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_list_review_records_with_result_filter(
    client: AsyncClient, ops_token: str, review_records
):
    response = await client.get(
        "/api/v1/ops/review/records?result=pending",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 2
    for review in data["data"]["reviews"]:
        assert review["result"] == "pending"


@pytest.mark.asyncio
async def test_list_review_records_with_risk_level_filter(
    client: AsyncClient, ops_token: str, review_records
):
    response = await client.get(
        "/api/v1/ops/review/records?risk_level=high",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["reviews"][0]["risk_level"] == "high"


@pytest.mark.asyncio
async def test_list_review_records_with_object_type_filter(
    client: AsyncClient, ops_token: str, review_records
):
    response = await client.get(
        "/api/v1/ops/review/records?object_type=npc",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_list_review_records_pagination(
    client: AsyncClient, ops_token: str, review_records
):
    response = await client.get(
        "/api/v1/ops/review/records?limit=2&offset=0",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["reviews"]) == 2
    assert data["meta"]["limit"] == 2
    assert data["meta"]["offset"] == 0
    assert data["meta"]["total"] == 5


@pytest.mark.asyncio
async def test_get_review_record_detail_success(
    client: AsyncClient, ops_token: str, review_records
):
    review = review_records[0]
    response = await client.get(
        f"/api/v1/ops/review/records/{review.review_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["review_id"] == str(review.review_id)
    assert data["data"]["object_type"] == review.object_type
    assert data["data"]["result"] == review.result


@pytest.mark.asyncio
async def test_get_review_record_not_found(
    client: AsyncClient, ops_token: str
):
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/ops/review/records/{fake_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "REVIEW_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_review_record_success(
    client: AsyncClient, ops_token: str
):
    obj_id = uuid.uuid4()
    response = await client.post(
        "/api/v1/ops/review/records",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-review-001",
        },
        json={
            "object_id": str(obj_id),
            "object_type": "npc",
            "review_type": "consistency",
            "trace_id": "trace_test_create_001",
            "quality_score": 0.85,
            "detail": {"checks": ["faction_match"], "passed": True},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "review_id" in data["data"]
    assert data["data"]["object_id"] == str(obj_id)
    assert data["data"]["result"] == "pending"


@pytest.mark.asyncio
async def test_create_review_record_with_result_and_risk(
    client: AsyncClient, ops_token: str
):
    obj_id = uuid.uuid4()
    response = await client.post(
        "/api/v1/ops/review/records",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-review-002",
        },
        json={
            "object_id": str(obj_id),
            "object_type": "quest",
            "review_type": "balance",
            "trace_id": "trace_test_create_002",
            "quality_score": 0.9,
            "result": "approved",
            "risk_level": "low",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["result"] == "approved"


@pytest.mark.asyncio
async def test_create_review_record_validation_error(
    client: AsyncClient, ops_token: str
):
    response = await client.post(
        "/api/v1/ops/review/records",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-review-003",
        },
        json={
            "object_id": str(uuid.uuid4()),
            "object_type": "",
            "review_type": "",
            "trace_id": "",
            "quality_score": 1.5,
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_review_result_pending_to_approved(
    client: AsyncClient, reviewer_token: str, review_records
):
    review = review_records[0]
    assert review.result == "pending"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-update-result-001",
        },
        json={"result": "approved"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["result"] == "approved"
    assert data["data"]["risk_level"] == "low"


@pytest.mark.asyncio
async def test_update_review_result_pending_to_rejected(
    client: AsyncClient, reviewer_token: str, review_records
):
    review = review_records[1]
    assert review.result == "pending"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-update-result-002",
        },
        json={"result": "rejected", "risk_level": "high", "reason": "Safety concerns"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["result"] == "rejected"
    assert data["data"]["risk_level"] == "high"


@pytest.mark.asyncio
async def test_update_review_result_invalid_transition(
    client: AsyncClient, reviewer_token: str, review_records
):
    review = review_records[2]
    assert review.result == "approved"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-update-result-003",
        },
        json={"result": "pending"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "INVALID_REVIEW_STATUS"


@pytest.mark.asyncio
async def test_update_review_result_not_found(
    client: AsyncClient, reviewer_token: str
):
    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/ops/review/records/{fake_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "test-update-result-004",
        },
        json={"result": "approved"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "REVIEW_NOT_FOUND"


@pytest.mark.asyncio
async def test_review_record_envelope_format(
    client: AsyncClient, ops_token: str, review_records
):
    response = await client.get(
        "/api/v1/ops/review/records",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["request_id"].startswith("req_")