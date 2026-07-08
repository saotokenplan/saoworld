from unittest.mock import MagicMock, patch


def test_daily_gate_scan_task_exists():
    from workers.tasks.gate_scan import daily_gate_scan

    assert daily_gate_scan is not None
    assert hasattr(daily_gate_scan, "delay")


def test_daily_gate_scan_empty(mock_audit_log):
    from workers.tasks.gate_scan import daily_gate_scan
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": [],
        "request_id": "req_test",
    })

    mock_generation_client = MagicMock()
    mock_generation_client.get_sync = MagicMock(return_value=mock_response)

    mock_review_client = MagicMock()
    mock_review_client.post_sync = MagicMock()

    with patch("workers.tasks.gate_scan.GenerationServiceClient", return_value=mock_generation_client):
        with patch("workers.tasks.gate_scan.ReviewServiceClient", return_value=mock_review_client):
            with patch("workers.tasks.gate_scan.write_audit_log"):
                result = daily_gate_scan.delay(trace_id=trace_id).get()

    assert result == {
        "pending_count": 0,
        "scanned_count": 0,
        "auto_rejected_count": 0,
        "auto_approved_count": 0,
        "manual_review_count": 0,
    }


def test_daily_gate_scan_with_objects(mock_audit_log):
    from workers.tasks.gate_scan import daily_gate_scan
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": [
            {"object_id": "obj_01", "quality_score": 0.85, "risk_level": "low"},
            {"object_id": "obj_02", "quality_score": 0.40, "risk_level": "low"},
            {"object_id": "obj_03", "quality_score": 0.60, "risk_level": "high"},
            {"object_id": "obj_04", "quality_score": 0.65, "risk_level": "medium"},
        ],
        "request_id": "req_test",
    })

    mock_generation_client = MagicMock()
    mock_generation_client.get_sync = MagicMock(return_value=mock_response)

    mock_review_client = MagicMock()
    mock_review_client.post_sync = MagicMock()

    with patch("workers.tasks.gate_scan.GenerationServiceClient", return_value=mock_generation_client):
        with patch("workers.tasks.gate_scan.ReviewServiceClient", return_value=mock_review_client):
            with patch("workers.tasks.gate_scan.write_audit_log"):
                result = daily_gate_scan.delay(trace_id=trace_id).get()

    assert result == {
        "pending_count": 4,
        "scanned_count": 4,
        "auto_rejected_count": 1,
        "auto_approved_count": 1,
        "manual_review_count": 2,
    }