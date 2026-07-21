from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch


def _build_http_response(data: object) -> MagicMock:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json = MagicMock(return_value={"data": data})
    return response


def _build_check_result(
    *,
    status: str,
    score: int,
    issues: list[MagicMock] | None = None,
) -> MagicMock:
    issues = issues or []
    result = MagicMock()
    result.status = SimpleNamespace(value=status)
    result.score = score
    result.issues = issues
    result.issues_count = len(issues)
    result.to_dict.return_value = {
        "status": status,
        "score": score,
        "issues_count": len(issues),
        "issues": [issue.to_dict() for issue in issues],
    }
    return result


def test_run_world_consistency_review_task_exists():
    from workers.tasks.content_review import run_world_consistency_review

    assert run_world_consistency_review is not None
    assert hasattr(run_world_consistency_review, "delay")


def test_run_world_consistency_review_no_issues(mock_audit_log):
    from workers.tasks.content_review import run_world_consistency_review

    check_result = _build_check_result(status="passed", score=100)
    checker = MagicMock()
    checker.check.return_value = check_result

    mock_world_client = MagicMock()
    mock_world_client.get_sync.return_value = _build_http_response([])

    mock_content_client = MagicMock()
    mock_content_client.get_sync.return_value = _build_http_response({"payload_jsonb": {}})

    mock_review_client = MagicMock()
    mock_review_client.post_sync.return_value = _build_http_response({})

    with patch("workers.tasks.content_review._get_checkers", return_value={"world_consistency": checker}):
        with patch("workers.tasks.content_review.WorldServiceClient", return_value=mock_world_client):
            with patch("workers.tasks.content_review.ContentServiceClient", return_value=mock_content_client):
                with patch("workers.tasks.content_review.ReviewServiceClient", return_value=mock_review_client):
                    with patch("workers.tasks.content_review.write_audit_log", new=AsyncMock()):
                        result = run_world_consistency_review.delay(
                            content_package_id="pkg_test_01",
                            trace_id="trace_test_01",
                        ).get()

    assert result == {
        "content_package_id": "pkg_test_01",
        "result": "approved",
        "score": 100,
        "issues_count": 0,
        "review_type": "world_consistency",
    }
    mock_review_client.post_sync.assert_called_once()


def test_run_full_content_review_marks_manual_review_when_results_mixed():
    from workers.tasks.content_review import run_full_content_review

    with patch("workers.tasks.content_review.run_world_consistency_review", return_value={"result": "approved", "score": 100, "issues_count": 0}):
        with patch("workers.tasks.content_review.run_balance_review", return_value={"result": "approved", "score": 90, "issues_count": 1}):
            with patch("workers.tasks.content_review.run_safety_review", return_value={"result": "manual_review", "score": 70, "issues_count": 2}):
                with patch("workers.tasks.content_review.run_duplication_review", return_value={"result": "approved", "score": 80, "issues_count": 1}):
                    with patch("workers.tasks.content_review.write_audit_log", new=AsyncMock()):
                        result = run_full_content_review.delay(
                            content_package_id="pkg_test_01",
                            trace_id="trace_test_01",
                        ).get()

    assert result["overall_result"] == "manual_review"
    assert result["average_score"] == 85
    assert result["total_issues"] == 4
    assert result["checks_completed"] == 4


def test_run_full_content_review_marks_rejected_when_any_check_rejected():
    from workers.tasks.content_review import run_full_content_review

    with patch("workers.tasks.content_review.run_world_consistency_review", return_value={"result": "approved", "score": 100, "issues_count": 0}):
        with patch("workers.tasks.content_review.run_balance_review", return_value={"result": "approved", "score": 95, "issues_count": 0}):
            with patch("workers.tasks.content_review.run_safety_review", return_value={"result": "rejected", "score": 20, "issues_count": 3}):
                with patch("workers.tasks.content_review.run_duplication_review", return_value={"result": "approved", "score": 90, "issues_count": 0}):
                    with patch("workers.tasks.content_review.write_audit_log", new=AsyncMock()):
                        result = run_full_content_review.delay(
                            content_package_id="pkg_test_02",
                            trace_id="trace_test_02",
                        ).get()

    assert result["overall_result"] == "rejected"
    assert result["average_score"] == 76.25
    assert result["total_issues"] == 3


def test_run_balance_review_task_exists():
    from workers.tasks.content_review import run_balance_review

    assert run_balance_review is not None
    assert hasattr(run_balance_review, "delay")
