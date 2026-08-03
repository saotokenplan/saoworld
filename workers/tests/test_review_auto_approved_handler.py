"""WP4：自动审核通过 → 发布队列串联的处理器测试。

覆盖点：
- 事件类型与事件模型已注册
- 低风险内容自动入队（触发 release_content_package）
- 高风险内容不自动入队（留人工确认）
- 缺失 content_package_id 时不入队
- release_mode 可由事件负载覆盖
- 既有 handler 不再因 stdlib logger 关键字参数而抛 TypeError
"""

from unittest.mock import MagicMock, patch

import pytest

from workers.events.handlers import (
    event_handlers,
    handle_review_auto_approved,
    handle_vote_result_finalized,
)
from workers.events.schemas import Event, EventType, ReviewAutoApprovedEvent


def _make_event(**payload_overrides) -> Event:
    payload = {
        "object_id": "obj_001",
        "object_type": "npc",
        "content_package_id": "pkg_001",
        "quality_score": 0.93,
        "risk_level": "low",
        "release_mode": "gray",
        "approved_at": "2026-08-03T21:18:00+00:00",
    }
    payload.update(payload_overrides)
    return Event(
        event_type=EventType.REVIEW_AUTO_APPROVED,
        trace_id="trace_wp4_001",
        producer="review-service",
        payload=payload,
    )


def test_review_auto_approved_event_type_registered():
    assert EventType.REVIEW_AUTO_APPROVED.value == "review.auto.approved"
    assert EventType.REVIEW_AUTO_APPROVED in event_handlers
    assert event_handlers[EventType.REVIEW_AUTO_APPROVED] is handle_review_auto_approved


def test_review_auto_approved_event_model_defaults():
    event = ReviewAutoApprovedEvent()

    assert event.event_type == EventType.REVIEW_AUTO_APPROVED
    for key in (
        "object_id",
        "object_type",
        "content_package_id",
        "quality_score",
        "risk_level",
        "release_mode",
        "approved_at",
    ):
        assert key in event.payload
    assert event.payload["risk_level"] == "low"
    assert event.payload["release_mode"] == "gray"


@pytest.mark.asyncio
async def test_low_risk_triggers_release():
    mock_task = MagicMock()

    with patch("workers.events.handlers.release_content_package", mock_task):
        await handle_review_auto_approved(_make_event())

    mock_task.delay.assert_called_once_with(
        content_package_id="pkg_001",
        release_mode="gray",
        trace_id="trace_wp4_001",
    )


@pytest.mark.asyncio
async def test_release_mode_can_be_overridden_by_payload():
    mock_task = MagicMock()

    with patch("workers.events.handlers.release_content_package", mock_task):
        await handle_review_auto_approved(_make_event(release_mode="full"))

    assert mock_task.delay.call_args.kwargs["release_mode"] == "full"


@pytest.mark.asyncio
@pytest.mark.parametrize("risk_level", ["medium", "high"])
async def test_non_low_risk_requires_manual_confirmation(risk_level):
    mock_task = MagicMock()

    with patch("workers.events.handlers.release_content_package", mock_task):
        await handle_review_auto_approved(_make_event(risk_level=risk_level))

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_missing_content_package_id_skips_release():
    mock_task = MagicMock()

    with patch("workers.events.handlers.release_content_package", mock_task):
        await handle_review_auto_approved(_make_event(content_package_id=""))

    mock_task.delay.assert_not_called()


@pytest.mark.asyncio
async def test_empty_release_mode_falls_back_to_gray():
    mock_task = MagicMock()

    with patch("workers.events.handlers.release_content_package", mock_task):
        await handle_review_auto_approved(_make_event(release_mode=None))

    assert mock_task.delay.call_args.kwargs["release_mode"] == "gray"


@pytest.mark.asyncio
async def test_vote_result_handler_logging_does_not_raise():
    """回归：本模块 logger 为标准库 Logger，不得以关键字参数传上下文。"""
    mock_task = MagicMock()
    event = Event(
        event_type=EventType.VOTE_RESULT_FINALIZED,
        trace_id="trace_vote_001",
        payload={
            "vote_cycle_id": "vc_001",
            "winning_candidate_id": "cand_001",
            "generated_params": {"template_type": "npc", "count": 2},
            "region_scope": ["region_001"],
            "chapter_id": "ch_001",
        },
    )

    with patch("workers.events.handlers.generate_content_batch", mock_task):
        await handle_vote_result_finalized(event)

    mock_task.delay.assert_called_once()
