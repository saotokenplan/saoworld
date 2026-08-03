import logging

from workers.events.schemas import Event, EventType, PlayerBehaviorEventType
from workers.tasks.content_generation import generate_content_batch
from workers.tasks.content_release import release_content_package
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
        # 注意：本模块 logger 为标准库 logging.Logger，不接受 structlog 风格的
        # 任意关键字参数（会抛 TypeError），上下文一律内联进消息体。
        logger.info(
            f"Triggering content generation for vote cycle: {vote_cycle_id}, "
            f"generated_params={generated_params}, region_scope={region_scope}"
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
    """WP4：人工审核批次完成 → 全量复审串联。

    仅当负载携带内容包引用且本批存在通过项时触发复审。生产侧
    `services/review` 的 `publish_review_batch_completed` 此前从不写入
    `content_package_id`，导致守卫恒为假、本处理器长期为死代码；
    该键已于 auto-20260803-2243 补齐。缺引用时维持「仅审核不复审」降级行为。
    """
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


async def handle_review_auto_approved(event: Event) -> None:
    """WP4：自动审核通过 → 发布队列串联。

    仅当内容包引用存在且风险等级为 low 时自动入队；高风险内容按
    `docs/20-specs/content-generation-spec.md` 要求留人工确认，不自动发布。
    自动链路默认走灰度发布，全量发布仍需人工 `promote_to_full_release`。
    """
    logger.info(f"Handling review auto approved event: {event.event_id}")
    payload = event.payload
    content_package_id = payload.get("content_package_id")
    risk_level = payload.get("risk_level", "low")
    release_mode = payload.get("release_mode") or "gray"

    if not content_package_id:
        logger.warning(
            "Review auto approved event without content_package_id, skip release, "
            f"object_id={payload.get('object_id')}"
        )
        return

    if risk_level != "low":
        logger.info(
            f"Content package {content_package_id} risk_level={risk_level}, "
            "requires manual confirmation, skip auto release"
        )
        return

    logger.info(f"Triggering auto release for content package: {content_package_id}")
    release_content_package.delay(
        content_package_id=content_package_id,
        release_mode=release_mode,
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
        # 注意：本模块 logger 为标准库 logging.Logger，不接受 structlog 风格的
        # 任意关键字参数（会抛 TypeError），上下文一律内联进消息体。
        logger.info(
            "Player event stored successfully, "
            f"event_type={event_data.get('event_type')}, "
            f"player_id={event_data.get('player_id')}"
        )
    except Exception as exc:
        logger.error(
            "Failed to store player event, "
            f"error={exc}, event_type={event_data.get('event_type')}"
        )
        raise


event_handlers = {
    EventType.VOTE_RESULT_FINALIZED: handle_vote_result_finalized,
    EventType.GENERATION_BATCH_COMPLETED: handle_generation_batch_completed,
    EventType.REVIEW_BATCH_COMPLETED: handle_review_batch_completed,
    EventType.REVIEW_AUTO_APPROVED: handle_review_auto_approved,
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
