import logging

from workers.events.schemas import Event
from workers.tasks.content_generation import generate_content_batch
from workers.tasks.content_review import run_world_consistency_review
from workers.tasks.content_packaging import package_content_batch
from workers.tasks.content_release import release_content_package

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
        logger.info(f"Triggering review for generation request: {request_id}")
        run_world_consistency_review.delay(
            request_id=request_id,
            trace_id=event.trace_id,
        )


async def handle_review_batch_completed(event: Event) -> None:
    logger.info(f"Handling review batch completed event: {event.event_id}")
    payload = event.payload
    request_id = payload.get("request_id")
    approved_count = payload.get("approved_count", 0)
    rejected_count = payload.get("rejected_count", 0)

    if request_id and approved_count > 0:
        logger.info(f"Triggering packaging for review request: {request_id}")
        package_content_batch.delay(
            request_id=request_id,
            approved_only=True,
            trace_id=event.trace_id,
        )


async def handle_content_package_released(event: Event) -> None:
    logger.info(f"Handling content package released event: {event.event_id}")
    payload = event.payload
    content_package_id = payload.get("content_package_id")
    release_mode = payload.get("release_mode")

    if content_package_id and release_mode == "gray":
        logger.info(f"Content package {content_package_id} released to gray")


event_handlers = {
    "vote.result.finalized": handle_vote_result_finalized,
    "generation.batch.completed": handle_generation_batch_completed,
    "review.batch.completed": handle_review_batch_completed,
    "content.package.released": handle_content_package_released,
}