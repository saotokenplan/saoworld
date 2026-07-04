import json
import uuid

from workers.celery_app import app
from workers.clients.db_client import write_audit_log
from workers.clients.http_client import ContentServiceClient
from workers.config import settings
from workers.utils.logging import get_logger
from workers.utils.tracing import generate_trace_id


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_release.release_content_package")
def release_content_package(
    self,
    content_package_id: str,
    release_mode: str = "gray",
    gray_scope_jsonb: dict | None = None,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("release_content_package", trace_id)
    logger.info("task_started", content_package_id=content_package_id, release_mode=release_mode)

    try:
        content_client = ContentServiceClient(settings.content_service_url)

        release_payload = {
            "release_mode": release_mode,
        }
        if gray_scope_jsonb:
            release_payload["gray_scope_jsonb"] = gray_scope_jsonb

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
                details_jsonb=json.dumps(release_payload),
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