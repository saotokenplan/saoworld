import logging

from workers.events.schemas import Event, EventType
from workers.tasks.content_generation import generate_content_batch
from workers.tasks.content_review import run_full_content_review
from workers.tasks.content_packaging import package_content_batch

logger = logging.getLogger(__name__)


async def handle_vote_result_finalized(event: Event) -> None:
    logger.info(f"Handling vote result finalized event: {event.event_id}")
    payload = event.payload
    vote_cycle_id = payload.get("vote_cycle_id")
    winning_candidate_id = payload.get("winning_candidate_id")

    if vote_cycle_id:
        logger.info(f"Triggering content generation for vote cycle: {vote_cycle_id}")
        generate_content_batch.delay(
            vote_cycle_id=vote_cycle_id,
            winning_candidate_id=winning_candidate_id,
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


event_handlers = {
    EventType.VOTE_RESULT_FINALIZED: handle_vote_result_finalized,
    EventType.GENERATION_BATCH_COMPLETED: handle_generation_batch_completed,
    EventType.REVIEW_BATCH_COMPLETED: handle_review_batch_completed,
    EventType.CONTENT_PACKAGE_RELEASED: handle_content_package_released,
    EventType.CONTENT_PACKAGE_ROLLED_BACK: handle_content_package_rolled_back,
}