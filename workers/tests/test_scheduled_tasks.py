
from workers.tasks.scheduled_tasks import daily_gate_scan, sync_metrics_gauge, daily_content_review


def test_daily_gate_scan_task_exists():
    assert daily_gate_scan is not None


def test_sync_metrics_gauge_task_exists():
    assert sync_metrics_gauge is not None


def test_daily_content_review_task_exists():
    assert daily_content_review is not None


def test_sync_gauge_metrics_function():
    from workers.utils.metrics import (
        sync_gauge_metrics,
        VOTE_CYCLES_BY_STATUS,
        CONTENT_PACKAGES_BY_STATUS,
        GENERATION_REQUESTS_BY_STATUS,
    )

    sync_gauge_metrics()

    assert VOTE_CYCLES_BY_STATUS.labels(status="draft")._value.get() == 0
    assert VOTE_CYCLES_BY_STATUS.labels(status="open")._value.get() == 0
    assert CONTENT_PACKAGES_BY_STATUS.labels(status="packaged")._value.get() == 0
    assert CONTENT_PACKAGES_BY_STATUS.labels(status="live")._value.get() == 0
    assert GENERATION_REQUESTS_BY_STATUS.labels(status="pending")._value.get() == 0
    assert GENERATION_REQUESTS_BY_STATUS.labels(status="succeeded")._value.get() == 0
