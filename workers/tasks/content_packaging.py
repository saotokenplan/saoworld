import json
import uuid

from workers.celery_app import app
from workers.clients.db_client import write_audit_log
from workers.clients.http_client import ContentServiceClient, GenerationServiceClient
from workers.config import settings
from workers.utils.logging import get_logger
from workers.utils.tracing import generate_trace_id


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_packaging.package_content_batch")
def package_content_batch(
    self,
    request_ids: list[str],
    chapter_id: str | None = None,
    region_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("package_content_batch", trace_id)
    logger.info("task_started", request_ids=request_ids)

    try:
        generation_client = GenerationServiceClient(settings.generation_service_url)
        content_client = ContentServiceClient(settings.content_service_url)

        all_objects = []
        for request_id in request_ids:
            response = generation_client.get_sync(f"/api/v1/generation/requests/{request_id}")
            response.raise_for_status()
            request_data = response.json()["data"]

            response = generation_client.get_sync(f"/api/v1/generation/requests/{request_id}/objects")
            response.raise_for_status()
            objects = response.json()["data"]

            all_objects.extend([obj for obj in objects if obj.get("status") == "approved"])

        package_payload = {
            "chapter_id": chapter_id,
            "region_id": region_id,
            "schema_version": 1,
            "content_jsonb": {
                "objects": all_objects,
                "request_ids": request_ids,
            },
        }

        response = content_client.post_sync("/api/v1/content/packages", json=package_payload)
        response.raise_for_status()
        result = response.json()

        content_package_id = result["data"]["content_package_id"]
        logger.info("content_package_created", content_package_id=content_package_id)

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="content.package_created",
                resource_type="content_package",
                resource_id=content_package_id,
                details_jsonb=json.dumps(package_payload),
            )

        asyncio.run(_write_audit())

        return {
            "content_package_id": content_package_id,
            "object_count": len(all_objects),
            "status": "packaged",
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)