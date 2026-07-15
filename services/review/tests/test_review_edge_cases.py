"""Edge-case tests for the review-service.

Covers gaps not addressed by existing test files:
1. Invalid status transition tests (more transition paths)
2. Pagination edge cases (offset beyond total)
3. Duplicate review operations (approve/reject already-processed)
4. Risk level filtering
5. Review result validation
"""

import uuid

import pytest
from httpx import AsyncClient

from app.core.errors import ReviewErrorCodes


# ---------------------------------------------------------------------------
# 1. Invalid status transition tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_result_approved_to_rejected_returns_409(
    client: AsyncClient, reviewer_token: str, review_records
):
    """Approved 记录不允许再转为 rejected，应返回 INVALID_REVIEW_STATUS。"""
    review = review_records[2]  # result="approved"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-approved-to-rejected-001",
        },
        json={"result": "rejected"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ReviewErrorCodes.INVALID_REVIEW_STATUS


@pytest.mark.asyncio
async def test_update_result_rejected_to_approved_returns_409(
    client: AsyncClient, reviewer_token: str, review_records
):
    """Rejected 记录不允许再转为 approved，应返回 INVALID_REVIEW_STATUS。"""
    review = review_records[3]  # result="rejected"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-rejected-to-approved-001",
        },
        json={"result": "approved"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ReviewErrorCodes.INVALID_REVIEW_STATUS


@pytest.mark.asyncio
async def test_update_result_rejected_to_pending_returns_409(
    client: AsyncClient, reviewer_token: str, review_records
):
    """Rejected 是终态，不允许回到 pending。"""
    review = review_records[3]  # result="rejected"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-rejected-to-pending-001",
        },
        json={"result": "pending"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ReviewErrorCodes.INVALID_REVIEW_STATUS


@pytest.mark.asyncio
async def test_update_result_approved_to_manual_review_returns_409(
    client: AsyncClient, reviewer_token: str, review_records
):
    """Approved 是终态，不允许转到 manual_review。"""
    review = review_records[2]  # result="approved"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-approved-to-manual-001",
        },
        json={"result": "manual_review"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ReviewErrorCodes.INVALID_REVIEW_STATUS


@pytest.mark.asyncio
async def test_update_result_pending_to_manual_review_success(
    client: AsyncClient, reviewer_token: str, review_records
):
    """Pending 允许转到 manual_review，应返回 200。"""
    review = review_records[0]  # result="pending"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-pending-to-manual-001",
        },
        json={"result": "manual_review", "reason": "Needs further review"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["result"] == "manual_review"


@pytest.mark.asyncio
async def test_update_result_manual_review_to_approved_success(
    client: AsyncClient, reviewer_token: str, review_records
):
    """Manual_review 允许转到 approved，应返回 200。"""
    review = review_records[4]  # result="manual_review"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-manual-to-approved-001",
        },
        json={"result": "approved"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["result"] == "approved"


@pytest.mark.asyncio
async def test_update_result_manual_review_to_rejected_success(
    client: AsyncClient, reviewer_token: str, review_records
):
    """Manual_review 允许转到 rejected，应返回 200。"""
    review = review_records[4]  # result="manual_review"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-manual-to-rejected-001",
        },
        json={"result": "rejected", "risk_level": "critical"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["result"] == "rejected"


# ---------------------------------------------------------------------------
# 2. Pagination edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_records_offset_beyond_total_returns_empty(
    client: AsyncClient, ops_token: str, review_records
):
    """Offset 超出总记录数时，应返回空列表但 total 仍为实际总数。"""
    response = await client.get(
        "/api/v1/ops/review/records?offset=9999&limit=20",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["reviews"] == []
    assert data["data"]["total"] == 5
    assert data["meta"]["total"] == 5
    assert data["meta"]["offset"] == 9999


@pytest.mark.asyncio
async def test_list_records_offset_equals_total_returns_empty(
    client: AsyncClient, ops_token: str, review_records
):
    """Offset 等于总记录数时，应返回空列表。"""
    response = await client.get(
        "/api/v1/ops/review/records?offset=5&limit=20",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["reviews"] == []
    assert data["data"]["total"] == 5


@pytest.mark.asyncio
async def test_list_records_zero_limit_returns_empty(
    client: AsyncClient, ops_token: str, review_records
):
    """Limit=1 时只返回 1 条记录，total 不受影响。"""
    response = await client.get(
        "/api/v1/ops/review/records?limit=1&offset=0",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["reviews"]) == 1
    assert data["data"]["total"] == 5


@pytest.mark.asyncio
async def test_list_records_no_data_returns_empty(
    client: AsyncClient, ops_token: str
):
    """数据库无记录时查询应返回空列表和 total=0。"""
    response = await client.get(
        "/api/v1/ops/review/records",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["reviews"] == []
    assert data["data"]["total"] == 0


# ---------------------------------------------------------------------------
# 3. Duplicate review operations (approve/reject already-processed)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_already_approved_object_returns_409(
    client: AsyncClient, reviewer_token: str, review_records
):
    """对已经全部 approved 的对象再次 approve，应返回 INVALID_REVIEW_STATUS。"""
    # review_records[2] 是 result="approved"，且其 object_id 下只有这一条记录
    obj_id = review_records[2].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/approve",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-dup-approve-001",
        },
        json={"reason": "Duplicate approve"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ReviewErrorCodes.INVALID_REVIEW_STATUS


@pytest.mark.asyncio
async def test_reject_already_rejected_object_returns_409(
    client: AsyncClient, reviewer_token: str, review_records
):
    """对已经全部 rejected 的对象再次 reject，应返回 INVALID_REVIEW_STATUS。"""
    # review_records[3] 是 result="rejected"，其 object_id 下只有这一条记录
    obj_id = review_records[3].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/reject",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-dup-reject-001",
        },
        json={"reason": "Duplicate reject"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ReviewErrorCodes.INVALID_REVIEW_STATUS


@pytest.mark.asyncio
async def test_approve_after_reject_on_same_object_returns_409(
    client: AsyncClient, reviewer_token: str, review_records
):
    """对已 rejected 的对象执行 approve，应返回 INVALID_REVIEW_STATUS（终态不可变更）。"""
    obj_id = review_records[3].object_id  # result="rejected"
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/approve",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-reject-then-approve-001",
        },
        json={},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == ReviewErrorCodes.INVALID_REVIEW_STATUS


# ---------------------------------------------------------------------------
# 4. Risk level filtering
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_records_filter_risk_level_low(
    client: AsyncClient, ops_token: str, review_records
):
    """按 risk_level=low 过滤，只返回 low 级别的记录。"""
    response = await client.get(
        "/api/v1/ops/review/records?risk_level=low",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for review in data["data"]["reviews"]:
        assert review["risk_level"] == "low"


@pytest.mark.asyncio
async def test_list_records_filter_risk_level_medium(
    client: AsyncClient, ops_token: str, review_records
):
    """按 risk_level=medium 过滤，只返回 medium 级别的记录。"""
    response = await client.get(
        "/api/v1/ops/review/records?risk_level=medium",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] >= 1
    for review in data["data"]["reviews"]:
        assert review["risk_level"] == "medium"


@pytest.mark.asyncio
async def test_list_records_filter_risk_level_critical(
    client: AsyncClient, ops_token: str, review_records
):
    """按 risk_level=critical 过滤，无匹配时返回空列表。"""
    response = await client.get(
        "/api/v1/ops/review/records?risk_level=critical",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["reviews"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_list_records_filter_risk_level_with_result_combined(
    client: AsyncClient, ops_token: str, review_records
):
    """同时按 risk_level 和 result 过滤，应只返回同时满足条件的记录。"""
    response = await client.get(
        "/api/v1/ops/review/records?risk_level=low&result=approved",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for review in data["data"]["reviews"]:
        assert review["risk_level"] == "low"
        assert review["result"] == "approved"


# ---------------------------------------------------------------------------
# 5. Review result validation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_result_with_invalid_result_value_returns_422(
    client: AsyncClient, reviewer_token: str, review_records
):
    """传入非法 result 值（不在枚举内），Pydantic 校验应返回 422。"""
    review = review_records[0]  # result="pending"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-invalid-result-001",
        },
        json={"result": "invalid_status"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_result_with_invalid_risk_level_returns_422(
    client: AsyncClient, reviewer_token: str, review_records
):
    """传入非法 risk_level 值，Pydantic 校验应返回 422。"""
    review = review_records[0]  # result="pending"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-invalid-risk-001",
        },
        json={"result": "approved", "risk_level": "super_high"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_review_with_invalid_result_returns_422(
    client: AsyncClient, ops_token: str
):
    """创建审核记录时传入非法 result 值，应返回 422。"""
    obj_id = uuid.uuid4()
    response = await client.post(
        "/api/v1/ops/review/records",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "edge-create-invalid-result-001",
        },
        json={
            "object_id": str(obj_id),
            "object_type": "npc",
            "review_type": "consistency",
            "trace_id": "trace_edge_test",
            "result": "nonexistent",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_review_with_invalid_risk_level_returns_422(
    client: AsyncClient, ops_token: str
):
    """创建审核记录时传入非法 risk_level 值，应返回 422。"""
    obj_id = uuid.uuid4()
    response = await client.post(
        "/api/v1/ops/review/records",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "edge-create-invalid-risk-001",
        },
        json={
            "object_id": str(obj_id),
            "object_type": "quest",
            "review_type": "balance",
            "trace_id": "trace_edge_test",
            "risk_level": "extreme",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_reject_with_invalid_risk_level_returns_422(
    client: AsyncClient, reviewer_token: str, review_records
):
    """Reject 接口传入非法 risk_level 值，应返回 422。"""
    obj_id = review_records[0].object_id
    response = await client.post(
        f"/api/v1/ops/review/{obj_id}/reject",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-reject-invalid-risk-001",
        },
        json={"reason": "test", "risk_level": "ultra"},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_result_changes_risk_level(
    client: AsyncClient, reviewer_token: str, ops_token: str, review_records
):
    """更新 result 时同时更新 risk_level，应正确持久化。"""
    review = review_records[0]  # result="pending", risk_level="low"
    response = await client.post(
        f"/api/v1/ops/review/records/{review.review_id}/result",
        headers={
            "Authorization": f"Bearer {reviewer_token}",
            "Idempotency-Key": "edge-update-risk-001",
        },
        json={"result": "rejected", "risk_level": "critical", "reason": "Elevated risk"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["result"] == "rejected"
    assert data["data"]["risk_level"] == "critical"

    # 验证持久化：重新查询详情（GET detail 需要 ops 角色）
    detail_resp = await client.get(
        f"/api/v1/ops/review/records/{review.review_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["data"]["risk_level"] == "critical"
