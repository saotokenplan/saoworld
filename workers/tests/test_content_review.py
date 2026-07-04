import pytest
from unittest.mock import MagicMock, patch


def test_run_world_consistency_review_task_exists():
    from workers.tasks.content_review import run_world_consistency_review

    assert run_world_consistency_review is not None
    assert hasattr(run_world_consistency_review, "delay")


def test_run_world_consistency_review_no_issues(mock_audit_log):
    from workers.tasks.content_review import run_world_consistency_review
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    world_response = MagicMock()
    world_response.raise_for_status = MagicMock()
    world_response.json = MagicMock(return_value={
        "data": [
            {"region_id": "region_01", "name": "Test Region", "status": "active"},
            {"region_id": "region_02", "name": "Test Region 2", "status": "active"},
        ],
        "request_id": "req_test",
    })

    review_response = MagicMock()
    review_response.raise_for_status = MagicMock()

    mock_world_client = MagicMock()
    mock_world_client.get_sync = MagicMock(return_value=world_response)

    mock_review_client = MagicMock()
    mock_review_client.post_sync = MagicMock(return_value=review_response)

    with patch("workers.tasks.content_review.WorldServiceClient", return_value=mock_world_client):
        with patch("workers.tasks.content_review.ReviewServiceClient", return_value=mock_review_client):
            with patch("workers.tasks.content_review.write_audit_log"):
                result = run_world_consistency_review.delay(
                    content_package_id="pkg_test_01",
                    trace_id=trace_id,
                ).get()

    assert result == {
        "content_package_id": "pkg_test_01",
        "result": "approved",
        "score": 100,
        "issues_count": 0,
    }


def test_run_world_consistency_review_with_unstable_regions(mock_audit_log):
    from workers.tasks.content_review import run_world_consistency_review
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    world_response = MagicMock()
    world_response.raise_for_status = MagicMock()
    world_response.json = MagicMock(return_value={
        "data": [
            {"region_id": "region_01", "name": "Test Region", "status": "unstable"},
            {"region_id": "region_02", "name": "Test Region 2", "status": "unstable"},
            {"region_id": "region_03", "name": "Test Region 3", "status": "active"},
        ],
        "request_id": "req_test",
    })

    review_response = MagicMock()
    review_response.raise_for_status = MagicMock()

    mock_world_client = MagicMock()
    mock_world_client.get_sync = MagicMock(return_value=world_response)

    mock_review_client = MagicMock()
    mock_review_client.post_sync = MagicMock(return_value=review_response)

    with patch("workers.tasks.content_review.WorldServiceClient", return_value=mock_world_client):
        with patch("workers.tasks.content_review.ReviewServiceClient", return_value=mock_review_client):
            with patch("workers.tasks.content_review.write_audit_log"):
                result = run_world_consistency_review.delay(
                    content_package_id="pkg_test_01",
                    trace_id=trace_id,
                ).get()

    assert result == {
        "content_package_id": "pkg_test_01",
        "result": "approved",
        "score": 80,
        "issues_count": 2,
    }


def test_run_balance_review_task_exists():
    from workers.tasks.content_review import run_balance_review

    assert run_balance_review is not None
    assert hasattr(run_balance_review, "delay")