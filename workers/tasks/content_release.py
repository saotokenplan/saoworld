import json
import uuid
from typing import Any

from workers.celery_app import app
from workers.clients.db_client import write_audit_log
from workers.clients.http_client import ContentServiceClient
from workers.config import settings
from workers.utils.logging import get_logger
from workers.utils.tracing import generate_trace_id


def build_gray_scope(
    region_ids: list[str] | None = None,
    player_percent: int | None = None,
    player_ids: list[str] | None = None,
) -> dict[str, Any] | None:
    scope: dict[str, Any] = {}
    if region_ids:
        scope["region_ids"] = region_ids
    if player_percent is not None:
        scope["player_percent"] = player_percent
    if player_ids:
        scope["player_ids"] = player_ids
    return scope if scope else None


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_release.release_content_package")
def release_content_package(
    self,
    content_package_id: str,
    release_mode: str = "gray",
    gray_scope_jsonb: dict[str, Any] | None = None,
    region_ids: list[str] | None = None,
    player_percent: int | None = None,
    player_ids: list[str] | None = None,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("release_content_package", trace_id)
    logger.info("task_started", content_package_id=content_package_id, release_mode=release_mode)

    try:
        content_client = ContentServiceClient(settings.content_service_url)

        gray_scope: dict[str, Any] | None = gray_scope_jsonb
        if not gray_scope and release_mode == "gray":
            gray_scope = build_gray_scope(region_ids, player_percent, player_ids)

        release_payload: dict[str, Any] = {
            "release_mode": release_mode,
        }
        if gray_scope:
            release_payload["gray_scope"] = gray_scope

        response = content_client.post_sync(
            f"/api/v1/content/packages/{content_package_id}/release",
            json=release_payload,
        )
        response.raise_for_status()
        result = response.json()

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="content.package_released",
                resource_type="content_package",
                resource_id=content_package_id,
                details_jsonb=json.dumps({
                    "release_mode": release_mode,
                    "gray_scope": gray_scope,
                }),
            )

        asyncio.run(_write_audit())

        return {
            "content_package_id": content_package_id,
            "release_mode": release_mode,
            "status": result["data"]["status"],
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_release.rollback_content_package")
def rollback_content_package(
    self,
    content_package_id: str,
    reason: str,
    target_version: str | None = None,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("rollback_content_package", trace_id)
    logger.info("task_started", content_package_id=content_package_id, reason=reason)

    try:
        content_client = ContentServiceClient(settings.content_service_url)

        rollback_payload = {
            "reason": reason,
        }
        if target_version:
            rollback_payload["target_version"] = target_version

        response = content_client.post_sync(
            f"/api/v1/content/packages/{content_package_id}/rollback",
            json=rollback_payload,
        )
        response.raise_for_status()
        result = response.json()

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="content.package_rolled_back",
                resource_type="content_package",
                resource_id=content_package_id,
                details_jsonb=json.dumps(rollback_payload),
            )

        asyncio.run(_write_audit())

        return {
            "content_package_id": content_package_id,
            "status": result["data"]["status"],
            "reason": reason,
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_release.promote_to_full_release")
def promote_to_full_release(
    self,
    content_package_id: str,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("promote_to_full_release", trace_id)
    logger.info("task_started", content_package_id=content_package_id)

    try:
        result: dict[str, str] = release_content_package(
            content_package_id=content_package_id,
            release_mode="full",
            trace_id=trace_id,
        )
        return result

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)
