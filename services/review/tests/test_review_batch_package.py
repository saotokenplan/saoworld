"""WP4：人工审核批次完成事件补齐内容包引用的 review 侧测试。

背景：`publish_review_batch_completed` 的负载此前不含 `content_package_id`，
导致 workers 侧 `handle_review_batch_completed` 守卫恒为假、全量复审链路断开。
本组用例锁定修复后的负载口径与向后兼容行为。

覆盖点：
- 批准路径携带 content_package_id / request_id 时正确进入事件负载
- 不传新字段时向后兼容（负载键存在但为 None / 空串）
- 拒绝路径同样透传内容包引用（approved_count 为 0，下游不会误触发）
- EventPublisher.publish_review_batch_completed 的事件包结构与键齐备性
- 事件发布异常不影响审核主流程（容错）
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


def _approve_url(object_id) -> str:
    return f"/api/v1/ops/review/{object_id}/approve"


def _reject_url(object_id) -> str:
    return f"/api/v1/ops/review/{object_id}/reject"


def _headers(token: str, idempotency_key: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key,
        "X-Trace-Id": "trace_wp4_batch_header",
    }


@pytest.mark.asyncio
async def test_approve_publishes_event_with_content_package(
    client: AsyncClient, reviewer_token: str, review_records
):
    """核心：批准路径携带内容包引用时，事件负载须带上该引用。"""
    obj_id = review_records[0].object_id
    package_id = str(uuid.uuid4())

    mock_publisher = AsyncMock()
    with patch("app.api.routes.event_publisher", mock_publisher):
        response = await client.post(
            _approve_url(obj_id),
            headers=_headers(reviewer_token, "test-wp4-batch-001"),
            json={
                "reason": "质量达标",
                "content_package_id": package_id,
                "request_id": "req_wp4_001",
            },
        )

    assert response.status_code == 200
    mock_publisher.publish_review_batch_completed.assert_awaited_once()

    kwargs = mock_publisher.publish_review_batch_completed.await_args.kwargs
    assert kwargs["content_package_id"] == package_id
    assert kwargs["request_id"] == "req_wp4_001"
    assert kwargs["approved_count"] > 0
    assert kwargs["rejected_count"] == 0


@pytest.mark.asyncio
async def test_approve_without_new_fields_is_backward_compatible(
    client: AsyncClient, reviewer_token: str, review_records
):
    """向后兼容：不传新字段时不报错，内容包引用为 None、请求 ID 为空串。"""
    obj_id = review_records[0].object_id

    mock_publisher = AsyncMock()
    with patch("app.api.routes.event_publisher", mock_publisher):
        response = await client.post(
            _approve_url(obj_id),
            headers=_headers(reviewer_token, "test-wp4-batch-002"),
            json={"reason": "沿用旧调用口径"},
        )

    assert response.status_code == 200
    kwargs = mock_publisher.publish_review_batch_completed.await_args.kwargs
    assert kwargs["content_package_id"] is None
    assert kwargs["request_id"] == ""


@pytest.mark.asyncio
async def test_reject_publishes_event_with_content_package(
    client: AsyncClient, reviewer_token: str, review_records
):
    """拒绝路径同样透传引用，但 approved_count 为 0，下游守卫不会触发复审。"""
    obj_id = review_records[0].object_id
    package_id = str(uuid.uuid4())

    mock_publisher = AsyncMock()
    with patch("app.api.routes.event_publisher", mock_publisher):
        response = await client.post(
            _reject_url(obj_id),
            headers=_headers(reviewer_token, "test-wp4-batch-003"),
            json={
                "reason": "数值失衡",
                "risk_level": "medium",
                "content_package_id": package_id,
                "request_id": "req_wp4_002",
            },
        )

    assert response.status_code == 200
    kwargs = mock_publisher.publish_review_batch_completed.await_args.kwargs
    assert kwargs["content_package_id"] == package_id
    assert kwargs["approved_count"] == 0
    assert kwargs["rejected_count"] > 0


@pytest.mark.asyncio
async def test_approve_event_publish_failure_does_not_break_main_flow(
    client: AsyncClient, reviewer_token: str, review_records
):
    """容错：事件发布异常不得影响审核主流程返回。"""
    obj_id = review_records[0].object_id

    mock_publisher = AsyncMock()
    mock_publisher.publish_review_batch_completed.side_effect = RuntimeError(
        "redis down"
    )

    with patch("app.api.routes.event_publisher", mock_publisher):
        response = await client.post(
            _approve_url(obj_id),
            headers=_headers(reviewer_token, "test-wp4-batch-004"),
            json={
                "reason": "质量达标",
                "content_package_id": str(uuid.uuid4()),
            },
        )

    assert response.status_code == 200
    assert response.json()["data"]["result"] == "approved"


@pytest.mark.asyncio
async def test_publish_review_batch_completed_event_envelope():
    """事件包结构：负载须含 content_package_id 键，供下游守卫读取。"""
    from app.core.event_publisher import EventPublisher

    publisher = EventPublisher()
    captured: dict = {}

    async def _fake_publish(event_type: str, payload: dict, trace_id: str = ""):
        captured["event_type"] = event_type
        captured["payload"] = payload
        captured["trace_id"] = trace_id
        return "evt_batch_1"

    with patch.object(publisher, "publish", _fake_publish):
        event_id = await publisher.publish_review_batch_completed(
            batch_id="batch_1",
            request_id="req_1",
            approved_count=2,
            rejected_count=0,
            needs_revision_count=0,
            completed_at="2026-08-03T22:43:00+00:00",
            content_package_id="pkg_1",
            trace_id="trace_1",
        )

    assert event_id == "evt_batch_1"
    assert captured["event_type"] == "review.batch.completed"
    assert captured["trace_id"] == "trace_1"

    payload = captured["payload"]
    for key in (
        "batch_id",
        "request_id",
        "content_package_id",
        "approved_count",
        "rejected_count",
        "needs_revision_count",
        "completed_at",
    ):
        assert key in payload
    assert payload["content_package_id"] == "pkg_1"


@pytest.mark.asyncio
async def test_publish_review_batch_completed_content_package_defaults_to_none():
    """未传内容包引用时键仍存在且为 None，保证下游 payload.get 语义稳定。"""
    from app.core.event_publisher import EventPublisher

    publisher = EventPublisher()
    captured: dict = {}

    async def _fake_publish(event_type: str, payload: dict, trace_id: str = ""):
        captured["payload"] = payload
        return "evt_batch_2"

    with patch.object(publisher, "publish", _fake_publish):
        await publisher.publish_review_batch_completed(
            batch_id="batch_2",
            request_id="",
            approved_count=1,
            rejected_count=0,
            needs_revision_count=0,
            completed_at="2026-08-03T22:43:00+00:00",
        )

    assert "content_package_id" in captured["payload"]
    assert captured["payload"]["content_package_id"] is None
