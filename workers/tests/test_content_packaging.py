import pytest
from unittest.mock import MagicMock, patch


def test_package_content_batch_task_exists():
    from workers.tasks.content_packaging import package_content_batch

    assert package_content_batch is not None
    assert hasattr(package_content_batch, "delay")


def test_package_content_batch_success(mock_audit_log):
    from workers.tasks.content_packaging import package_content_batch
    from workers.utils.tracing import generate_trace_id

    trace_id = generate_trace_id()

    request_response = MagicMock()
    request_response.raise_for_status = MagicMock()
    request_response.json = MagicMock(return_value={
        "data": {"request_id": "gen_20260704_001"},
        "request_id": "req_test",
    })

    objects_response = MagicMock()
    objects_response.raise_for_status = MagicMock()
    objects_response.json = MagicMock(return_value={
        "data": [
            {"object_id": "obj_01", "status": "approved", "type": "npc"},
            {"object_id": "obj_02", "status": "approved", "type": "quest"},
            {"object_id": "obj_03", "status": "pending_review", "type": "event"},
        ],
        "request_id": "req_test",
    })

    package_response = MagicMock()
    package_response.raise_for_status = MagicMock()
    package_response.json = MagicMock(return_value={
        "data": {"content_package_id": "pkg_20260704_001"},
        "request_id": "req_test",
    })

    mock_generation_client = MagicMock()
    mock_generation_client.get_sync = MagicMock(side_effect=[request_response, objects_response])

    mock_content_client = MagicMock()
    mock_content_client.post_sync = MagicMock(return_value=package_response)

    with patch("workers.tasks.content_packaging.GenerationServiceClient", return_value=mock_generation_client):
        with patch("workers.tasks.content_packaging.ContentServiceClient", return_value=mock_content_client):
            with patch("workers.tasks.content_packaging.write_audit_log"):
                result = package_content_batch.delay(
                    request_ids=["gen_20260704_001"],
                    chapter_id="chapter_01",
                    region_id="region_wasteland_01",
                    trace_id=trace_id,
                ).get()

    assert result == {
        "content_package_id": "pkg_20260704_001",
        "object_count": 2,
        "status": "packaged",
    }