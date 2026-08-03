"""事件总线与事件发布器测试。

离线化说明（auto-20260803-2243）：本组用例此前直连 `localhost:6379`，
在无 Redis 的开发/CI 环境固定 5 failed，长期掩盖真实回归信号。
现改为在 **Redis 客户端边界** 打桩（patch `redis.from_url`），
`EventBus.publish` 的事件包构造、频道命名、序列化等真实逻辑仍被完整执行，
既消除环境依赖，又比原用例（仅断言返回值为非空字符串）覆盖更强。
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from workers.events.event_bus import EventBus
from workers.events.event_publisher import EventPublisher


@pytest.fixture
def fake_redis():
    """伪 Redis 客户端，记录 publish 调用。"""
    client = MagicMock()
    client.publish = AsyncMock(return_value=1)
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def publisher(fake_redis):
    """EventPublisher 绑定一个 Redis 已打桩的 EventBus。"""
    with patch(
        "workers.events.event_bus.redis.from_url", return_value=fake_redis
    ):
        yield EventPublisher(event_bus=EventBus("redis://localhost:6379/9"))


def _published(fake_redis) -> list[tuple[str, dict]]:
    """取出所有已发布的 (channel, event_dict)。"""
    return [
        (call.args[0], json.loads(call.args[1]))
        for call in fake_redis.publish.await_args_list
    ]


@pytest.mark.asyncio
async def test_event_bus_connect_disconnect(fake_redis):
    with patch(
        "workers.events.event_bus.redis.from_url", return_value=fake_redis
    ):
        event_bus = EventBus("redis://localhost:6379/9")
        await event_bus.connect()
        assert event_bus._redis is not None
        await event_bus.disconnect()
        assert event_bus._redis is None

    fake_redis.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_event_publisher_publish(publisher, fake_redis):
    event_id = await publisher.publish_vote_cycle_closed(
        vote_cycle_id="vc_test",
        chapter_id="ch_test",
        closed_at="2026-07-05T08:00:00Z",
        trace_id="trace_test",
    )
    assert isinstance(event_id, str)
    assert len(event_id) > 0

    (channel, event), = _published(fake_redis)
    assert channel == "event.vote.cycle.closed"
    assert event["trace_id"] == "trace_test"
    assert event["producer"] == "workers"
    assert event["payload"]["vote_cycle_id"] == "vc_test"
    assert event["payload"]["chapter_id"] == "ch_test"


@pytest.mark.asyncio
async def test_event_publisher_publish_vote_result(publisher, fake_redis):
    event_id = await publisher.publish_vote_result_finalized(
        vote_cycle_id="vc_test",
        winning_candidate_id="cand_test",
        winning_candidate_name="Test Candidate",
        total_votes=100,
        finalized_at="2026-07-05T08:00:00Z",
        trace_id="trace_test",
    )
    assert isinstance(event_id, str)
    assert len(event_id) > 0

    (channel, event), = _published(fake_redis)
    assert channel == "event.vote.result.finalized"
    assert event["payload"]["winning_candidate_id"] == "cand_test"
    assert event["payload"]["total_votes"] == 100


@pytest.mark.asyncio
async def test_event_publisher_publish_generation_events(publisher, fake_redis):
    event_id1 = await publisher.publish_generation_request_created(
        request_id="req_test",
        vote_cycle_id="vc_test",
        target_type="npc",
        region_id="region_test",
        created_at="2026-07-05T08:00:00Z",
    )
    assert isinstance(event_id1, str)

    event_id2 = await publisher.publish_generation_batch_completed(
        request_id="req_test",
        generated_objects=[{"id": "obj1"}],
        completed_at="2026-07-05T08:00:00Z",
        status="succeeded",
    )
    assert isinstance(event_id2, str)
    assert event_id1 != event_id2

    published = _published(fake_redis)
    assert [c for c, _ in published] == [
        "event.generation.request.created",
        "event.generation.batch.completed",
    ]
    assert published[1][1]["payload"]["status"] == "succeeded"


@pytest.mark.asyncio
async def test_event_publisher_publish_review_event(publisher, fake_redis):
    event_id = await publisher.publish_review_batch_completed(
        batch_id="batch_test",
        request_id="req_test",
        approved_count=5,
        rejected_count=1,
        needs_revision_count=0,
        completed_at="2026-07-05T08:00:00Z",
    )
    assert isinstance(event_id, str)

    (channel, event), = _published(fake_redis)
    assert channel == "event.review.batch.completed"
    assert event["payload"]["approved_count"] == 5
    assert event["payload"]["rejected_count"] == 1


@pytest.mark.asyncio
async def test_event_publisher_publish_content_events(publisher, fake_redis):
    event_id1 = await publisher.publish_content_package_released(
        content_package_id="pkg_test",
        release_mode="gray",
        gray_scope={"player_percent": 10},
        released_at="2026-07-05T08:00:00Z",
    )
    assert isinstance(event_id1, str)

    event_id2 = await publisher.publish_content_package_rolled_back(
        content_package_id="pkg_test",
        rollback_reason="Test rollback",
        rolled_back_at="2026-07-05T08:00:00Z",
    )
    assert isinstance(event_id2, str)

    published = _published(fake_redis)
    assert [c for c, _ in published] == [
        "event.content.package.released",
        "event.content.package.rolled_back",
    ]
    assert published[0][1]["payload"]["release_mode"] == "gray"
    assert published[1][1]["payload"]["rollback_reason"] == "Test rollback"
