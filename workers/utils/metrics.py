import logging

from prometheus_client import Gauge

logger = logging.getLogger(__name__)

VOTE_CYCLES_BY_STATUS = Gauge(
    "vote_cycles_by_status",
    "Number of vote cycles by status",
    ["status"],
)

CONTENT_PACKAGES_BY_STATUS = Gauge(
    "content_packages_by_status",
    "Number of content packages by status",
    ["status"],
)

GENERATION_REQUESTS_BY_STATUS = Gauge(
    "generation_requests_by_status",
    "Number of generation requests by status",
    ["status"],
)


def sync_gauge_metrics() -> None:
    logger.info("Syncing gauge metrics")

    try:
        from workers.clients.http_client import VoteServiceClient
        from workers.config import settings

        client = VoteServiceClient(settings.vote_service_url)
        client.get_sync("/api/v1/health")
    except Exception as e:
        logger.warning(f"Metrics sync skipped (no database connection): {e}")

    VOTE_CYCLES_BY_STATUS.labels(status="draft").set(0)
    VOTE_CYCLES_BY_STATUS.labels(status="scheduled").set(0)
    VOTE_CYCLES_BY_STATUS.labels(status="open").set(0)
    VOTE_CYCLES_BY_STATUS.labels(status="closed").set(0)
    VOTE_CYCLES_BY_STATUS.labels(status="finalized").set(0)

    CONTENT_PACKAGES_BY_STATUS.labels(status="packaged").set(0)
    CONTENT_PACKAGES_BY_STATUS.labels(status="gray").set(0)
    CONTENT_PACKAGES_BY_STATUS.labels(status="live").set(0)
    CONTENT_PACKAGES_BY_STATUS.labels(status="archived").set(0)
    CONTENT_PACKAGES_BY_STATUS.labels(status="rolled_back").set(0)

    GENERATION_REQUESTS_BY_STATUS.labels(status="pending").set(0)
    GENERATION_REQUESTS_BY_STATUS.labels(status="processing").set(0)
    GENERATION_REQUESTS_BY_STATUS.labels(status="succeeded").set(0)
    GENERATION_REQUESTS_BY_STATUS.labels(status="failed_retryable").set(0)
    GENERATION_REQUESTS_BY_STATUS.labels(status="failed_permanent").set(0)
