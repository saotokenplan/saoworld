"""WP4：人工审核批次完成 → 全量复审串联的处理器测试。

背景：生产侧 `services/review` 的 `publish_review_batch_completed` 此前从不写入
`content_package_id`，导致 `handle_review_batch_completed` 的守卫
`content_package_id and approved_count > 0` 恒为假，处理器长期为死代码。
本组用例锁定修复后的行为口径。

覆盖点：
- 事件类型与事件模型已注册，默认负载含 content_package_id 键
- 携带内容包引用且有通过项时触发全量复审（死代码复活）
- 缺失 / 为空的内容包引用不触发（降级为仅审核）
- approved_count 为 0（如纯拒绝批次）不触发
- trace_id 正确透传
- handle_player_event 不再因 stdlib logger 关键字参数而抛 TypeError
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workers.events.handlers import (
    event_handlers,
    handle_player_event,
    handle_review_batch_completed,
)
from workers.events.schemas import Event, EventType, ReviewBatchCompletedEvent


def _make_event(**payload_overrides) -> Event:
    payload = {
        "batch_id": "batch_001",
        "request_id": "req_001",
        "content_package_id": "pkg_001",
        "approved_count": 3,
        "rejected_count": 0,
        "needs_revision_count": 0,
        "completed_at": "2026-08-03T22:43:00+00:00",
    }
    payload.update(payload_overrides)
    return Event(
        event_type=EventType.REVIEW_BATCH_COMPLETED,
        trace_id="trace_wp4_batch_001",
        producer="review-service",
        payload=payload,
    )


def test_review_batch_completed_event_type_registered():
    assert EventType.REVIEW_BATCH_COMPLETED.value == "review.batch.completed"
    assert EventType.REVIEW_BATCH_COMPLETED in event_handlers
    assert (
        event_handlers[EventType.REVIEW_BATCH_COMPLETED]
        is handle_review_batch_completed
    )


def test_event_model_default_payload_contains_content_package_id():
    """事件模型默认负载须与生产侧口径对齐，含 content_package_id 键。"""
    event = ReviewBatchCompletedEvent()

    assert event.event_type == EventType.REVIEW_BATCH_COMPLETED
    for key in (
        "batch_id",
        "request_id",
        "content_package_id",
        "approved_count",
        "rejected_count",
        "needs_revision_count",
        "completed_at",
    ):
        assert key in event.payload
    assert event.payload["content_package_id"] is None


@pytest.mark.asyncio
async def test_approved_batch_with_package_triggers_full_review():
    """核心回归：守卫可达，复审链路打通。"""
    mock_task = MagicMock()

    with patch("workers.events.handlers.run_full_content_review", mock_task):
        await handle_review_batch_completed(_make_event())

    mock_task.delay.assert_called_once_with(
        content_package_id="pkg_001",
        trace_id="trace_wp4_batch_001",
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("missing_value", [None, ""])
async def test_missing_content_package_id_skips_full_review(missing_value):
    mock_task = MagicMock()

    with patch("workers.events.handlers.run_full_content_review", mock_task):
        await handle_review_batch_completed(
            _make_event(content_package_id=missing_value)
        )

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_payload_without_content_package_key_skips_full_review():
    """老版本生产者发出的负载不含该键时，须安全降级而非抛错。"""
    mock_task = MagicMock()
    event = Event(
        event_type=EventType.REVIEW_BATCH_COMPLETED,
        trace_id="trace_legacy",
        payload={
            "batch_id": "batch_legacy",
            "request_id": "",
            "approved_count": 5,
            "rejected_count": 0,
            "needs_revision_count": 0,
            "completed_at": "2026-08-03T22:43:00+00:00",
        },
    )

    with patch("workers.events.handlers.run_full_content_review", mock_task):
        await handle_review_batch_completed(event)

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_rejected_only_batch_does_not_trigger_full_review():
    """纯拒绝批次 approved_count 为 0，即便带内容包引用也不复审。"""
    mock_task = MagicMock()

    with patch("workers.events.handlers.run_full_content_review", mock_task):
        await handle_review_batch_completed(
            _make_event(approved_count=0, rejected_count=4)
        )

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_trace_id_is_propagated():
    mock_task = MagicMock()
    event = _make_event()
    event.trace_id = "trace_custom_999"

    with patch("workers.events.handlers.run_full_content_review", mock_task):
        await handle_review_batch_completed(event)

    assert mock_task.delay.call_args.kwargs["trace_id"] == "trace_custom_999"


@pytest.mark.asyncio
async def test_player_event_handler_logging_does_not_raise():
    """回归：handle_player_event 的 logger 调用不得使用 structlog 风格关键字参数。"""
    event_data = {"event_type": "player.enter_region", "player_id": "p_001"}

    with patch(
        "workers.events.handlers.store_player_event", AsyncMock()
    ) as mock_store:
        await handle_player_event(event_data)

    mock_store.assert_awaited_once_with(event_data)


@pytest.mark.asyncio
async def test_player_event_handler_error_logging_does_not_mask_exception():
    """回归：异常分支的 logger.error 亦不得因关键字参数抛 TypeError 掩盖原始异常。"""
    event_data = {"event_type": "player.enter_region", "player_id": "p_002"}

    with patch(
        "workers.events.handlers.store_player_event",
        AsyncMock(side_effect=ValueError("boom")),
    ):
        with pytest.raises(ValueError, match="boom"):
            await handle_player_event(event_data)
