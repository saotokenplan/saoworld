from unittest.mock import patch

from workers.tasks.scheduled_tasks import daily_content_review, daily_gate_scan, sync_metrics_gauge


def test_daily_gate_scan_task_exists():
    assert daily_gate_scan is not None


def test_sync_metrics_gauge_task_exists():
    assert sync_metrics_gauge is not None


def test_daily_content_review_task_exists():
    assert daily_content_review is not None


def test_daily_content_review_skips_without_content_package_id():
    result = daily_content_review.delay().get()

    assert result == {
        "status": "skipped",
        "reason": "content_package_id_required",
    }


def test_daily_content_review_runs_full_review_when_content_package_id_provided():
    with patch("workers.tasks.scheduled_tasks.run_full_content_review", return_value={"overall_result": "approved"}) as mock_review:
        result = daily_content_review.delay(content_package_id="pkg_test_01").get()

    assert result == {
        "status": "success",
        "result": "{'overall_result': 'approved'}",
        "content_package_id": "pkg_test_01",
    }
    mock_review.assert_called_once_with(content_package_id="pkg_test_01", trace_id="daily_review")


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
