import logging

from workers.celery_app import app
from workers.tasks.gate_scan import daily_gate_scan
from workers.tasks.content_review import run_world_consistency_review

logger = logging.getLogger(__name__)


@app.task(bind=True, queue="scheduled")
def daily_gate_scan(self) -> dict[str, str]:
    logger.info("Running scheduled daily gate scan")
    try:
        result = daily_gate_scan()
        return {"status": "success", "result": str(result)}
    except Exception as e:
        logger.error(f"Daily gate scan failed: {e}")
        return {"status": "failed", "error": str(e)}


@app.task(bind=True, queue="scheduled")
def sync_metrics_gauge(self) -> dict[str, str]:
    logger.info("Running scheduled metrics gauge sync")
    try:
        from workers.utils.metrics import sync_gauge_metrics

        sync_gauge_metrics()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Metrics gauge sync failed: {e}")
        return {"status": "failed", "error": str(e)}


@app.task(bind=True, queue="scheduled")
def daily_content_review(self) -> dict[str, str]:
    logger.info("Running scheduled daily content review")
    try:
        result = run_world_consistency_review(request_id="daily_review")
        return {"status": "success", "result": str(result)}
    except Exception as e:
        logger.error(f"Daily content review failed: {e}")
        return {"status": "failed", "error": str(e)}