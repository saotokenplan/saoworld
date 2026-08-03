"""WP4：自动审核通过 → 发布队列串联的 review 侧测试。

覆盖点：
- 自动审核通过且携带 content_package_id 时发布 review.auto.approved 事件
- 事件负载字段齐备且口径正确
- 未携带 content_package_id 时不发布事件（降级为仅审核）
- 非 approved 判定不发布事件
- 事件发布异常不影响审核主流程（容错）
- EventPublisher.publish_review_auto_approved 的事件包结构
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

AUTO_REVIEW_URL = "/api/v1/ops/review/auto"

# 高质量、字段完整的载荷，用于触发 approved 判定
GOOD_ITEM_PAYLOAD = {
    "item_key": "item_frost_fang_sword",
    "name": "霜牙短剑",
    "description": "一柄以寒霜之牙锻造的短剑，剑身覆有薄霜。",
    "item_type": "weapon",
    "rarity": "rare",
    "attack": 42,
    "defense": 0,
    "durability": 100,
    "level_requirement": 12,
}


def _auto_review_body(content_package_id: str | None = None, **overrides) -> dict:
    body = {
        "object_id": str(uuid.uuid4()),
        "object_type": "item",
        "object_payload": GOOD_ITEM_PAYLOAD,
        "quality_score": 0.95,
        "trace_id": "trace_wp4_auto_release",
    }
    if content_package_id is not None:
        body["content_package_id"] = content_package_id
    body.update(overrides)
    return body


async def _post_auto_review(client, ops_token: str, body: dict):
    return await client.post(
        AUTO_REVIEW_URL,
        json=body,
        headers={
            "Authorization": f"Bearer {ops_token}",
            "X-Trace-Id": "trace_wp4_header",
        },
    )


@pytest.mark.asyncio
async def test_auto_approved_publishes_event_with_content_package(client, ops_token):
    package_id = str(uuid.uuid4())
    body = _auto_review_body(content_package_id=package_id)

    mock_publisher = AsyncMock()
    with patch("app.api.routes.event_publisher", mock_publisher):
        response = await _post_auto_review(client, ops_token, body)

    assert response.status_code == 200
    assert response.json()["data"]["auto_result"] == "approved"

    mock_publisher.publish_review_auto_approved.assert_awaited_once()
    kwargs = mock_publisher.publish_review_auto_approved.await_args.kwargs
    assert kwargs["object_id"] == body["object_id"]
    assert kwargs["object_type"] == "item"
    assert kwargs["content_package_id"] == package_id
    assert kwargs["quality_score"] == 0.95
    assert kwargs["risk_level"] == "low"
    assert kwargs["trace_id"] == "trace_wp4_header"
    assert kwargs["approved_at"]


@pytest.mark.asyncio
async def test_auto_approved_without_content_package_does_not_publish(client, ops_token):
    body = _auto_review_body()

    mock_publisher = AsyncMock()
    with patch("app.api.routes.event_publisher", mock_publisher):
        response = await _post_auto_review(client, ops_token, body)

    assert response.status_code == 200
    assert response.json()["data"]["auto_result"] == "approved"
    mock_publisher.publish_review_auto_approved.assert_not_awaited()


@pytest.mark.asyncio
async def test_non_approved_result_does_not_publish(client, ops_token):
    # 低质量分 + 残缺字段 -> 不会得到 approved
    body = _auto_review_body(
        content_package_id=str(uuid.uuid4()),
        object_payload={"name": "", "description": ""},
        quality_score=0.1,
    )

    mock_publisher = AsyncMock()
    with patch("app.api.routes.event_publisher", mock_publisher):
        response = await _post_auto_review(client, ops_token, body)

    assert response.status_code == 200
    assert response.json()["data"]["auto_result"] != "approved"
    mock_publisher.publish_review_auto_approved.assert_not_awaited()


@pytest.mark.asyncio
async def test_publish_failure_does_not_break_review(client, ops_token):
    """事件发布失败必须被吞掉，审核主流程照常返回 200 并落库。"""
    body = _auto_review_body(content_package_id=str(uuid.uuid4()))

    mock_publisher = AsyncMock()
    mock_publisher.publish_review_auto_approved.side_effect = RuntimeError("redis down")

    with patch("app.api.routes.event_publisher", mock_publisher):
        response = await _post_auto_review(client, ops_token, body)

    assert response.status_code == 200
    assert response.json()["data"]["auto_result"] == "approved"
    mock_publisher.publish_review_auto_approved.assert_awaited_once()


@pytest.mark.asyncio
async def test_content_package_id_is_optional_in_schema():
    from app.schemas.review import AutoReviewRequest

    request = AutoReviewRequest(
        object_id=uuid.uuid4(),
        object_type="item",
        object_payload=GOOD_ITEM_PAYLOAD,
        trace_id="trace_x",
    )
    assert request.content_package_id is None


@pytest.mark.asyncio
async def test_publisher_builds_expected_event_envelope():
    from app.core.event_publisher import EventPublisher

    publisher = EventPublisher()
    captured: dict = {}

    async def fake_publish(event_type: str, payload: dict, trace_id: str = "") -> str:
        captured["event_type"] = event_type
        captured["payload"] = payload
        captured["trace_id"] = trace_id
        return "evt_fake"

    publisher.publish = fake_publish  # type: ignore[method-assign]

    event_id = await publisher.publish_review_auto_approved(
        object_id="obj_1",
        object_type="monster",
        content_package_id="pkg_1",
        approved_at="2026-08-03T21:18:00+00:00",
        quality_score=0.88,
        risk_level="low",
        trace_id="trace_1",
    )

    assert event_id == "evt_fake"
    assert captured["event_type"] == "review.auto.approved"
    assert captured["trace_id"] == "trace_1"
    assert captured["payload"] == {
        "object_id": "obj_1",
        "object_type": "monster",
        "content_package_id": "pkg_1",
        "quality_score": 0.88,
        "risk_level": "low",
        "release_mode": "gray",
        "approved_at": "2026-08-03T21:18:00+00:00",
    }
