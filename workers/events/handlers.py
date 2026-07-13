import logging

from workers.events.schemas import Event, EventType, PlayerBehaviorEventType
from workers.tasks.content_generation import generate_content_batch
from workers.tasks.content_review import run_full_content_review
from workers.tasks.content_packaging import package_content_batch
from workers.tasks.player_event_ingestion import store_player_event

logger = logging.getLogger(__name__)


async def handle_vote_result_finalized(event: Event) -> None:
    logger.info(f"Handling vote result finalized event: {event.event_id}")
    payload = event.payload
    vote_cycle_id = payload.get("vote_cycle_id")
    winning_candidate_id = payload.get("winning_candidate_id")
    generated_params = payload.get("generated_params", {}) or {}
    region_scope = payload.get("region_scope", []) or []
    chapter_id = payload.get("chapter_id")

    if vote_cycle_id:
        logger.info(
            f"Triggering content generation for vote cycle: {vote_cycle_id}",
            generated_params=generated_params,
            region_scope=region_scope,
        )
        region_id = region_scope[0] if region_scope else None
        template_type = generated_params.get("template_type", "npc")
        count = generated_params.get("count", 1)
        generate_content_batch.delay(
            vote_cycle_id=vote_cycle_id,
            winning_candidate_id=winning_candidate_id,
            template_type=template_type,
            count=count,
            region_id=region_id,
            chapter_id=chapter_id,
            generated_params=generated_params,
            trace_id=event.trace_id,
        )


async def handle_generation_batch_completed(event: Event) -> None:
    logger.info(f"Handling generation batch completed event: {event.event_id}")
    payload = event.payload
    request_id = payload.get("request_id")
    status = payload.get("status")

    if request_id and status == "succeeded":
        logger.info(f"Triggering packaging for generation request: {request_id}")
        package_content_batch.delay(
            request_ids=[request_id],
            trace_id=event.trace_id,
        )


async def handle_review_batch_completed(event: Event) -> None:
    logger.info(f"Handling review batch completed event: {event.event_id}")
    payload = event.payload
    content_package_id = payload.get("content_package_id")
    approved_count = payload.get("approved_count", 0)

    if content_package_id and approved_count > 0:
        logger.info(f"Triggering full review for content package: {content_package_id}")
        run_full_content_review.delay(
            content_package_id=content_package_id,
            trace_id=event.trace_id,
        )


async def handle_content_package_released(event: Event) -> None:
    logger.info(f"Handling content package released event: {event.event_id}")
    payload = event.payload
    content_package_id = payload.get("content_package_id")
    release_mode = payload.get("release_mode")

    if content_package_id and release_mode == "gray":
        logger.info(f"Content package {content_package_id} released to gray")


async def handle_content_package_rolled_back(event: Event) -> None:
    logger.info(f"Handling content package rolled back event: {event.event_id}")
    payload = event.payload
    content_package_id = payload.get("content_package_id")
    rollback_reason = payload.get("rollback_reason")

    logger.info(f"Content package {content_package_id} rolled back: {rollback_reason}")


async def handle_player_event(event_data: dict) -> None:
    logger.info(f"Handling player event: {event_data.get('event_type')}")

    try:
        await store_player_event(event_data)
        logger.info(
            "Player event stored successfully",
            event_type=event_data.get("event_type"),
            player_id=event_data.get("player_id"),
        )
    except Exception as exc:
        logger.error(
            "Failed to store player event",
            error=str(exc),
            event_type=event_data.get("event_type"),
        )
        raise


event_handlers = {
    EventType.VOTE_RESULT_FINALIZED: handle_vote_result_finalized,
    EventType.GENERATION_BATCH_COMPLETED: handle_generation_batch_completed,
    EventType.REVIEW_BATCH_COMPLETED: handle_review_batch_completed,
    EventType.CONTENT_PACKAGE_RELEASED: handle_content_package_released,
    EventType.CONTENT_PACKAGE_ROLLED_BACK: handle_content_package_rolled_back,
}

player_behavior_event_types = {
    PlayerBehaviorEventType.PLAYER_ENTER_REGION.value,
    PlayerBehaviorEventType.PLAYER_LEAVE_REGION.value,
    PlayerBehaviorEventType.PLAYER_COMPLETE_QUEST.value,
    PlayerBehaviorEventType.PLAYER_INTERACT_NPC.value,
    PlayerBehaviorEventType.PLAYER_VOTE_SUBMIT.value,
    PlayerBehaviorEventType.PLAYER_VIEW_CONTENT.value,
    PlayerBehaviorEventType.PLAYER_SPEND_RESOURCE.value,
}