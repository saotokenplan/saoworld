import pytest

from workers.events.event_bus import EventBus
from workers.events.event_publisher import EventPublisher


@pytest.mark.asyncio
async def test_event_bus_connect_disconnect():
    event_bus = EventBus("redis://localhost:6379/9")
    await event_bus.connect()
    assert event_bus._redis is not None
    await event_bus.disconnect()


@pytest.mark.asyncio
async def test_event_publisher_publish():
    publisher = EventPublisher()
    event_id = await publisher.publish_vote_cycle_closed(
        vote_cycle_id="vc_test",
        chapter_id="ch_test",
        closed_at="2026-07-05T08:00:00Z",
        trace_id="trace_test",
    )
    assert isinstance(event_id, str)
    assert len(event_id) > 0


@pytest.mark.asyncio
async def test_event_publisher_publish_vote_result():
    publisher = EventPublisher()
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


@pytest.mark.asyncio
async def test_event_publisher_publish_generation_events():
    publisher = EventPublisher()

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


@pytest.mark.asyncio
async def test_event_publisher_publish_review_event():
    publisher = EventPublisher()
    event_id = await publisher.publish_review_batch_completed(
        batch_id="batch_test",
        request_id="req_test",
        approved_count=5,
        rejected_count=1,
        needs_revision_count=0,
        completed_at="2026-07-05T08:00:00Z",
    )
    assert isinstance(event_id, str)


@pytest.mark.asyncio
async def test_event_publisher_publish_content_events():
    publisher = EventPublisher()

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
