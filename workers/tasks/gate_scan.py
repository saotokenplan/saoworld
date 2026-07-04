import json
import uuid

from workers.celery_app import app
from workers.clients.db_client import write_audit_log
from workers.clients.http_client import GenerationServiceClient, ReviewServiceClient
from workers.config import settings
from workers.utils.logging import get_logger
from workers.utils.tracing import generate_trace_id


@app.task(bind=True, max_retries=1, name="workers.tasks.gate_scan.daily_gate_scan")
def daily_gate_scan(
    self,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("daily_gate_scan", trace_id)
    logger.info("task_started")

    try:
        generation_client = GenerationServiceClient(settings.generation_service_url)
        review_client = ReviewServiceClient(settings.review_service_url)

        response = generation_client.get_sync("/api/v1/generation/objects", params={"status": "pending_review"})
        response.raise_for_status()
        pending_objects = response.json()["data"]

        scan_results = {
            "pending_count": len(pending_objects),
            "scanned_count": 0,
            "auto_rejected_count": 0,
            "auto_approved_count": 0,
            "manual_review_count": 0,
        }

        for obj in pending_objects:
            quality_score = obj.get("quality_score", 0)
            risk_level = obj.get("risk_level", "low")

            if quality_score < 0.5:
                result = "rejected"
                scan_results["auto_rejected_count"] += 1
            elif risk_level in ["high", "critical"]:
                result = "manual_review"
                scan_results["manual_review_count"] += 1
            elif quality_score >= 0.75:
                result = "approved"
                scan_results["auto_approved_count"] += 1
            else:
                result = "manual_review"
                scan_results["manual_review_count"] += 1

            review_payload = {
                "object_id": obj["object_id"],
                "result": result,
                "risk_level": risk_level,
                "score": quality_score,
                "gate_scan": True,
            }

            review_client.post_sync("/api/v1/reviews/objects", json=review_payload)
            scan_results["scanned_count"] += 1

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="gate.daily_scan_completed",
                details_jsonb=json.dumps(scan_results),
            )

        asyncio.run(_write_audit())

        logger.info("task_completed", **scan_results)
        return scan_results

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)