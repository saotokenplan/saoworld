from unittest.mock import MagicMock, patch


def test_generate_content_batch_task_exists():
    from workers.tasks.content_generation import generate_content_batch

    assert generate_content_batch is not None
    assert hasattr(generate_content_batch, "delay")


def test_generate_content_batch_success(mock_audit_log):
    from workers.tasks.content_generation import generate_content_batch
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": {"request_id": "gen_20260704_001"},
        "request_id": "req_test",
    })

    mock_client = MagicMock()
    mock_client.post_sync = MagicMock(return_value=mock_response)

    with patch("workers.tasks.content_generation.GenerationServiceClient", return_value=mock_client):
        with patch("workers.tasks.content_generation.write_audit_log"):
            result = generate_content_batch.delay(
                template_type="npc",
                count=5,
                region_id="region_wasteland_01",
                chapter_id="chapter_01",
                trace_id=trace_id,
            ).get()

    assert result == {"request_id": "gen_20260704_001", "status": "started"}
    mock_client.post_sync.assert_called_once_with(
        "/api/v1/generation/requests",
        json={
            "template_type": "npc",
            "count": 5,
            "region_id": "region_wasteland_01",
            "chapter_id": "chapter_01",
        },
    )