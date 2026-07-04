import json
import uuid

from workers.celery_app import app
from workers.clients.db_client import write_audit_log
from workers.clients.http_client import GenerationServiceClient
from workers.config import settings
from workers.utils.logging import get_logger
from workers.utils.tracing import generate_trace_id


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_generation.generate_content_batch")
def generate_content_batch(
    self,
    template_type: str,
    count: int = 1,
    region_id: str | None = None,
    chapter_id: str | None = None,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("generate_content_batch", trace_id)
    logger.info("task_started", template_type=template_type, count=count, region_id=region_id)

    try:
        client = GenerationServiceClient(settings.generation_service_url)

        payload = {
            "template_type": template_type,
            "count": count,
        }
        if region_id:
            payload["region_id"] = region_id
        if chapter_id:
            payload["chapter_id"] = chapter_id

        response = client.post_sync("/api/v1/generation/requests", json=payload)
        response.raise_for_status()
        result = response.json()

        request_id = result["data"]["request_id"]
        logger.info("generation_request_created", request_id=request_id)

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="generation.batch_started",
                resource_type="generation_request",
                resource_id=request_id,
                details_jsonb=json.dumps(payload),
            )

        asyncio.run(_write_audit())

        return {"request_id": request_id, "status": "started"}

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)