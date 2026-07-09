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
    call_args = mock_client.post_sync.call_args
    assert call_args[0][0] == "/api/v1/ops/generation/requests"
    payload = call_args[1]["json"]
    assert payload["template_id"] == "tpl_npc_v1"
    assert payload["input_payload"]["template_type"] == "npc"
    assert payload["input_payload"]["count"] == 5
    assert payload["input_payload"]["region_id"] == "region_wasteland_01"
    assert payload["input_payload"]["chapter_id"] == "chapter_01"
    assert payload["trace_id"] == trace_id


def test_generate_content_batch_with_generated_params(mock_audit_log):
    from workers.tasks.content_generation import generate_content_batch
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = MagicMock(return_value={
        "data": {"request_id": "gen_20260704_002"},
        "request_id": "req_test",
    })

    mock_client = MagicMock()
    mock_client.post_sync = MagicMock(return_value=mock_response)

    generated_params = {
        "template_type": "quest",
        "count": 3,
        "region_id": "region_custom",
        "chapter_id": "chapter_02",
        "template_id": "tpl_quest_custom_v2",
        "custom_field": "custom_value",
    }

    with patch("workers.tasks.content_generation.GenerationServiceClient", return_value=mock_client):
        with patch("workers.tasks.content_generation.write_audit_log"):
            result = generate_content_batch.delay(
                vote_cycle_id="vc_001",
                winning_candidate_id="cand_001",
                generated_params=generated_params,
                trace_id=trace_id,
            ).get()

    assert result == {"request_id": "gen_20260704_002", "status": "started"}
    call_args = mock_client.post_sync.call_args
    assert call_args[0][0] == "/api/v1/ops/generation/requests"
    payload = call_args[1]["json"]
    assert payload["vote_cycle_id"] == "vc_001"
    assert payload["source_candidate_id"] == "cand_001"
    assert payload["template_id"] == "tpl_quest_custom_v2"
    assert payload["input_payload"]["template_type"] == "quest"
    assert payload["input_payload"]["count"] == 3
    assert payload["input_payload"]["region_id"] == "region_custom"
    assert payload["input_payload"]["chapter_id"] == "chapter_02"
    assert payload["input_payload"]["custom_field"] == "custom_value"
    assert payload["trace_id"] == trace_id