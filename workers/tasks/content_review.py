import json
import uuid

from workers.celery_app import app
from workers.clients.db_client import write_audit_log
from workers.clients.http_client import ReviewServiceClient, WorldServiceClient
from workers.config import settings
from workers.utils.logging import get_logger
from workers.utils.tracing import generate_trace_id


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_review.run_world_consistency_review")
def run_world_consistency_review(
    self,
    content_package_id: str,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("run_world_consistency_review", trace_id)
    logger.info("task_started", content_package_id=content_package_id)

    try:
        world_client = WorldServiceClient(settings.world_service_url)
        review_client = ReviewServiceClient(settings.review_service_url)

        response = world_client.get_sync("/api/v1/world/regions")
        response.raise_for_status()
        regions = response.json()["data"]

        consistency_issues = []
        for region in regions:
            if region.get("status") == "unstable":
                consistency_issues.append({
                    "type": "region_unstable",
                    "region_id": region["region_id"],
                    "message": f"Region {region['name']} is unstable",
                })

        review_payload = {
            "content_package_id": content_package_id,
            "review_type": "consistency",
            "issues": consistency_issues,
            "score": max(0, 100 - len(consistency_issues) * 10),
            "result": "approved" if len(consistency_issues) < 3 else "needs_revision",
        }

        response = review_client.post_sync("/api/v1/reviews", json=review_payload)
        response.raise_for_status()

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="review.consistency_completed",
                resource_type="content_package",
                resource_id=content_package_id,
                details_jsonb=json.dumps(review_payload),
            )

        asyncio.run(_write_audit())

        return {
            "content_package_id": content_package_id,
            "result": review_payload["result"],
            "score": review_payload["score"],
            "issues_count": len(consistency_issues),
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_review.run_balance_review")
def run_balance_review(
    self,
    content_package_id: str,
    trace_id: str | None = None,
) -> dict[str, str]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("run_balance_review", trace_id)
    logger.info("task_started", content_package_id=content_package_id)

    try:
        review_client = ReviewServiceClient(settings.review_service_url)

        balance_issues = []

        review_payload = {
            "content_package_id": content_package_id,
            "review_type": "balance",
            "issues": balance_issues,
            "score": 100,
            "result": "approved",
        }

        response = review_client.post_sync("/api/v1/reviews", json=review_payload)
        response.raise_for_status()

        import asyncio

        async def _write_audit():
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="review.balance_completed",
                resource_type="content_package",
                resource_id=content_package_id,
                details_jsonb=json.dumps(review_payload),
            )

        asyncio.run(_write_audit())

        return {
            "content_package_id": content_package_id,
            "result": review_payload["result"],
            "score": review_payload["score"],
            "issues_count": len(balance_issues),
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)