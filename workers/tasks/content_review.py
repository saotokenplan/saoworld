import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

from workers.celery_app import app
from workers.clients.db_client import write_audit_log
from workers.clients.http_client import ReviewServiceClient, WorldServiceClient, ContentServiceClient
from workers.config import settings
from workers.utils.logging import get_logger
from workers.utils.tracing import generate_trace_id

_tools_path = Path(__file__).parent.parent.parent / "tools"
if str(_tools_path) not in sys.path:
    sys.path.insert(0, str(_tools_path))


def _get_checkers() -> dict[str, Any]:
    from content_check import (
        WorldConsistencyChecker,
        RewardBoundaryChecker,
        ContentSafetyChecker,
        DuplicationChecker,
    )
    from content_check.config import get_default_config

    config = get_default_config()

    return {
        "world_consistency": WorldConsistencyChecker(config.get("world_consistency", {})),
        "reward_boundary": RewardBoundaryChecker(config.get("reward_boundary", {})),
        "content_safety": ContentSafetyChecker(config.get("content_safety", {})),
        "duplication": DuplicationChecker(config.get("duplication", {})),
    }


def _map_result_status(check_status: str) -> str:
    status_map = {
        "passed": "approved",
        "needs_review": "manual_review",
        "failed": "rejected",
    }
    return status_map.get(check_status, "manual_review")


def _map_risk_level(issues: list[dict[str, Any]]) -> str:
    severities = [i.get("severity", "low") for i in issues]
    if "critical" in severities:
        return "critical"
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    return "low"


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_review.run_world_consistency_review")
def run_world_consistency_review(
    self,
    content_package_id: str,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("run_world_consistency_review", trace_id)
    logger.info("task_started", content_package_id=content_package_id)

    try:
        checkers = _get_checkers()
        world_client = WorldServiceClient(settings.world_service_url)
        content_client = ContentServiceClient(settings.content_service_url)
        review_client = ReviewServiceClient(settings.review_service_url)

        regions_resp = world_client.get_sync("/api/v1/world/regions")
        regions_resp.raise_for_status()
        regions_data = regions_resp.json()["data"]

        package_resp = content_client.get_sync(f"/api/v1/content/packages/{content_package_id}")
        package_resp.raise_for_status()
        package_data = package_resp.json()["data"]

        content_payload = package_data.get("payload_jsonb", {})
        if not content_payload and "content_data" in package_data:
            content_payload = package_data["content_data"]

        regions_map = {}
        for r in regions_data:
            regions_map[r.get("region_id")] = r

        context = {
            "regions": regions_map,
            "factions": {},
            "faction_relations": [],
            "chapters": [],
        }

        checker = checkers["world_consistency"]
        check_result = checker.check(content_payload, context)

        review_payload = {
            "object_id": content_package_id,
            "object_type": "content_package",
            "review_type": "world_consistency",
            "result": _map_result_status(check_result.status.value),
            "risk_level": _map_risk_level([i.to_dict() for i in check_result.issues]),
            "quality_score": check_result.score / 100.0,
            "detail_jsonb": check_result.to_dict(),
        }

        response = review_client.post_sync(
            "/api/v1/ops/review/records",
            json=review_payload,
            headers={
                "Idempotency-Key": f"review_wc_{content_package_id}_{trace_id}",
                "X-Trace-Id": trace_id,
            },
        )
        response.raise_for_status()

        async def _write_audit() -> None:
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="review.world_consistency_completed",
                resource_type="content_package",
                resource_id=content_package_id if _is_uuid(content_package_id) else None,
                details_jsonb=json.dumps(check_result.to_dict()),
            )

        asyncio.run(_write_audit())

        logger.info(
            "task_completed",
            content_package_id=content_package_id,
            result=check_result.status.value,
            score=check_result.score,
            issues_count=check_result.issues_count,
        )

        return {
            "content_package_id": content_package_id,
            "result": _map_result_status(check_result.status.value),
            "score": check_result.score,
            "issues_count": check_result.issues_count,
            "review_type": "world_consistency",
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_review.run_balance_review")
def run_balance_review(
    self,
    content_package_id: str,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("run_balance_review", trace_id)
    logger.info("task_started", content_package_id=content_package_id)

    try:
        checkers = _get_checkers()
        content_client = ContentServiceClient(settings.content_service_url)
        review_client = ReviewServiceClient(settings.review_service_url)

        package_resp = content_client.get_sync(f"/api/v1/content/packages/{content_package_id}")
        package_resp.raise_for_status()
        package_data = package_resp.json()["data"]

        content_payload = package_data.get("payload_jsonb", {})
        if not content_payload and "content_data" in package_data:
            content_payload = package_data["content_data"]

        context: dict[str, Any] = {}

        checker = checkers["reward_boundary"]
        check_result = checker.check(content_payload, context)

        review_payload = {
            "object_id": content_package_id,
            "object_type": "content_package",
            "review_type": "balance",
            "result": _map_result_status(check_result.status.value),
            "risk_level": _map_risk_level([i.to_dict() for i in check_result.issues]),
            "quality_score": check_result.score / 100.0,
            "detail_jsonb": check_result.to_dict(),
        }

        response = review_client.post_sync(
            "/api/v1/ops/review/records",
            json=review_payload,
            headers={
                "Idempotency-Key": f"review_balance_{content_package_id}_{trace_id}",
                "X-Trace-Id": trace_id,
            },
        )
        response.raise_for_status()

        async def _write_audit() -> None:
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="review.balance_completed",
                resource_type="content_package",
                resource_id=content_package_id if _is_uuid(content_package_id) else None,
                details_jsonb=json.dumps(check_result.to_dict()),
            )

        asyncio.run(_write_audit())

        mapped_result = _map_result_status(check_result.status.value)
        logger.info(
            "task_completed",
            content_package_id=content_package_id,
            result=mapped_result,
            score=check_result.score,
            issues_count=check_result.issues_count,
        )

        return {
            "content_package_id": content_package_id,
            "result": mapped_result,
            "score": check_result.score,
            "issues_count": check_result.issues_count,
            "review_type": "balance",
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_review.run_safety_review")
def run_safety_review(
    self,
    content_package_id: str,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("run_safety_review", trace_id)
    logger.info("task_started", content_package_id=content_package_id)

    try:
        checkers = _get_checkers()
        content_client = ContentServiceClient(settings.content_service_url)
        review_client = ReviewServiceClient(settings.review_service_url)

        package_resp = content_client.get_sync(f"/api/v1/content/packages/{content_package_id}")
        package_resp.raise_for_status()
        package_data = package_resp.json()["data"]

        content_payload = package_data.get("payload_jsonb", {})
        if not content_payload and "content_data" in package_data:
            content_payload = package_data["content_data"]

        checker = checkers["content_safety"]
        check_result = checker.check(content_payload)

        review_payload = {
            "object_id": content_package_id,
            "object_type": "content_package",
            "review_type": "safety",
            "result": _map_result_status(check_result.status.value),
            "risk_level": _map_risk_level([i.to_dict() for i in check_result.issues]),
            "quality_score": check_result.score / 100.0,
            "detail_jsonb": check_result.to_dict(),
        }

        response = review_client.post_sync(
            "/api/v1/ops/review/records",
            json=review_payload,
            headers={
                "Idempotency-Key": f"review_safety_{content_package_id}_{trace_id}",
                "X-Trace-Id": trace_id,
            },
        )
        response.raise_for_status()

        async def _write_audit() -> None:
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="review.safety_completed",
                resource_type="content_package",
                resource_id=content_package_id if _is_uuid(content_package_id) else None,
                details_jsonb=json.dumps(check_result.to_dict()),
            )

        asyncio.run(_write_audit())

        mapped_result = _map_result_status(check_result.status.value)
        logger.info(
            "task_completed",
            content_package_id=content_package_id,
            result=mapped_result,
            score=check_result.score,
            issues_count=check_result.issues_count,
        )

        return {
            "content_package_id": content_package_id,
            "result": mapped_result,
            "score": check_result.score,
            "issues_count": check_result.issues_count,
            "review_type": "safety",
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=3, retry_backoff=2, name="workers.tasks.content_review.run_duplication_review")
def run_duplication_review(
    self,
    content_package_id: str,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("run_duplication_review", trace_id)
    logger.info("task_started", content_package_id=content_package_id)

    try:
        checkers = _get_checkers()
        content_client = ContentServiceClient(settings.content_service_url)
        review_client = ReviewServiceClient(settings.review_service_url)

        package_resp = content_client.get_sync(f"/api/v1/content/packages/{content_package_id}")
        package_resp.raise_for_status()
        package_data = package_resp.json()["data"]

        content_payload = package_data.get("payload_jsonb", {})
        if not content_payload and "content_data" in package_data:
            content_payload = package_data["content_data"]

        existing_content: dict[str, Any] = {}
        try:
            history_resp = content_client.get_sync("/api/v1/content/updates", params={"limit": 100})
            if history_resp.status_code == 200:
                history_data = history_resp.json().get("data", [])
                all_npcs = []
                all_quests = []
                for pkg in history_data:
                    pkg_payload = pkg.get("payload_jsonb", {})
                    if "npcs" in pkg_payload:
                        all_npcs.extend(pkg_payload["npcs"])
                    if "quests" in pkg_payload:
                        all_quests.extend(pkg_payload["quests"])
                existing_content = {"npcs": all_npcs, "quests": all_quests}
        except Exception:
            pass

        context = {"existing_content": existing_content}

        checker = checkers["duplication"]
        check_result = checker.check(content_payload, context)

        review_payload = {
            "object_id": content_package_id,
            "object_type": "content_package",
            "review_type": "duplication",
            "result": _map_result_status(check_result.status.value),
            "risk_level": _map_risk_level([i.to_dict() for i in check_result.issues]),
            "quality_score": check_result.score / 100.0,
            "detail_jsonb": check_result.to_dict(),
        }

        response = review_client.post_sync(
            "/api/v1/ops/review/records",
            json=review_payload,
            headers={
                "Idempotency-Key": f"review_duplication_{content_package_id}_{trace_id}",
                "X-Trace-Id": trace_id,
            },
        )
        response.raise_for_status()

        async def _write_audit() -> None:
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="review.duplication_completed",
                resource_type="content_package",
                resource_id=content_package_id if _is_uuid(content_package_id) else None,
                details_jsonb=json.dumps(check_result.to_dict()),
            )

        asyncio.run(_write_audit())

        mapped_result = _map_result_status(check_result.status.value)
        logger.info(
            "task_completed",
            content_package_id=content_package_id,
            result=mapped_result,
            score=check_result.score,
            issues_count=check_result.issues_count,
        )

        return {
            "content_package_id": content_package_id,
            "result": mapped_result,
            "score": check_result.score,
            "issues_count": check_result.issues_count,
            "review_type": "duplication",
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


@app.task(bind=True, max_retries=2, retry_backoff=3, name="workers.tasks.content_review.run_full_content_review")
def run_full_content_review(
    self,
    content_package_id: str,
    trace_id: str | None = None,
) -> dict[str, Any]:
    if trace_id is None:
        trace_id = generate_trace_id()

    logger = get_logger("run_full_content_review", trace_id)
    logger.info("task_started", content_package_id=content_package_id)

    try:
        results: list[dict[str, Any]] = []

        results.append(run_world_consistency_review(content_package_id, trace_id))
        results.append(run_balance_review(content_package_id, trace_id))
        results.append(run_safety_review(content_package_id, trace_id))
        results.append(run_duplication_review(content_package_id, trace_id))

        total_score = sum(r.get("score", 0) for r in results) / len(results) if results else 0
        all_passed = all(r.get("result") == "passed" for r in results)
        any_failed = any(r.get("result") == "failed" for r in results)

        if any_failed:
            overall_result = "failed"
        elif all_passed:
            overall_result = "passed"
        else:
            overall_result = "needs_review"

        total_issues = sum(r.get("issues_count", 0) for r in results)

        async def _write_audit() -> None:
            await write_audit_log(
                audit_log_id=str(uuid.uuid4()),
                trace_id=trace_id,
                operator_id="system",
                operator_role="system",
                action="review.full_content_review_completed",
                resource_type="content_package",
                resource_id=content_package_id if _is_uuid(content_package_id) else None,
                details_jsonb=json.dumps({
                    "overall_result": overall_result,
                    "average_score": total_score,
                    "total_issues": total_issues,
                    "individual_results": results,
                }),
            )

        asyncio.run(_write_audit())

        logger.info(
            "task_completed",
            content_package_id=content_package_id,
            overall_result=overall_result,
            average_score=total_score,
            total_issues=total_issues,
        )

        return {
            "content_package_id": content_package_id,
            "overall_result": overall_result,
            "average_score": total_score,
            "total_issues": total_issues,
            "checks_completed": len(results),
            "results": results,
        }

    except Exception as e:
        logger.error("task_failed", error=str(e))
        raise self.retry(exc=e)


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
