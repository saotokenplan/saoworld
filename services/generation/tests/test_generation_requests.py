import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_generation_requests_success(
    client: AsyncClient, ops_token: str, generation_requests
):
    response = await client.get(
        "/api/v1/ops/generation/requests",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["total"] == 5
    assert len(data["data"]["requests"]) == 5
    assert data["meta"]["total"] == 5
    assert data["meta"]["limit"] == 20
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_list_generation_requests_with_status_filter(
    client: AsyncClient, ops_token: str, generation_requests
):
    response = await client.get(
        "/api/v1/ops/generation/requests?status=pending",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["requests"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_list_generation_requests_pagination(
    client: AsyncClient, ops_token: str, generation_requests
):
    response = await client.get(
        "/api/v1/ops/generation/requests?limit=2&offset=0",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["requests"]) == 2
    assert data["meta"]["limit"] == 2
    assert data["meta"]["offset"] == 0
    assert data["meta"]["total"] == 5


@pytest.mark.asyncio
async def test_get_generation_request_detail_success(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[0]
    response = await client.get(
        f"/api/v1/ops/generation/requests/{req.request_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["request_id"] == str(req.request_id)
    assert data["data"]["template_id"] == req.template_id
    assert data["data"]["status"] == req.status


@pytest.mark.asyncio
async def test_get_generation_request_not_found(
    client: AsyncClient, ops_token: str
):
    import uuid

    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/ops/generation/requests/{fake_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "REQUEST_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_generation_request_success(
    client: AsyncClient, ops_token: str
):
    response = await client.post(
        "/api/v1/ops/generation/requests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-req-001",
        },
        json={
            "template_id": "tpl_npc_v2",
            "input_payload": {"region": "wasteland", "count": 5},
            "trace_id": "trace_test_create_001",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "request_id" in data["data"]
    assert data["data"]["template_id"] == "tpl_npc_v2"
    assert data["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_create_generation_request_with_vote_cycle(
    client: AsyncClient, ops_token: str
):
    import uuid

    vc_id = uuid.uuid4()
    sc_id = uuid.uuid4()
    response = await client.post(
        "/api/v1/ops/generation/requests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-req-002",
        },
        json={
            "vote_cycle_id": str(vc_id),
            "source_candidate_id": str(sc_id),
            "template_id": "tpl_quest_v1",
            "input_payload": {"type": "main"},
            "trace_id": "trace_test_create_002",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["template_id"] == "tpl_quest_v1"


@pytest.mark.asyncio
async def test_create_generation_request_validation_error(
    client: AsyncClient, ops_token: str
):
    response = await client.post(
        "/api/v1/ops/generation/requests",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-req-003",
        },
        json={
            "template_id": "",
            "input_payload": {},
            "trace_id": "",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_request_status_pending_to_processing(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[0]
    assert req.status == "pending"
    response = await client.post(
        f"/api/v1/ops/generation/requests/{req.request_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-001",
        },
        json={"status": "processing"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "processing"


@pytest.mark.asyncio
async def test_update_request_status_processing_to_succeeded(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[1]
    assert req.status == "processing"
    response = await client.post(
        f"/api/v1/ops/generation/requests/{req.request_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-002",
        },
        json={"status": "succeeded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "succeeded"


@pytest.mark.asyncio
async def test_update_request_status_failed_retryable_to_pending(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[3]
    assert req.status == "failed_retryable"
    assert req.retry_count == 1
    response = await client.post(
        f"/api/v1/ops/generation/requests/{req.request_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-003",
        },
        json={"status": "pending"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_update_request_status_invalid_transition(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[2]
    assert req.status == "succeeded"
    response = await client.post(
        f"/api/v1/ops/generation/requests/{req.request_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-004",
        },
        json={"status": "pending"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "INVALID_REQUEST_STATUS"


@pytest.mark.asyncio
async def test_update_request_status_not_found(
    client: AsyncClient, ops_token: str
):
    import uuid

    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/ops/generation/requests/{fake_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-005",
        },
        json={"status": "processing"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "REQUEST_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_request_status_with_error_message(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[1]
    response = await client.post(
        f"/api/v1/ops/generation/requests/{req.request_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-006",
        },
        json={"status": "failed_retryable", "error_message": "Connection timeout"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "failed_retryable"


@pytest.mark.asyncio
async def test_generation_request_envelope_format(
    client: AsyncClient, ops_token: str, generation_requests
):
    response = await client.get(
        "/api/v1/ops/generation/requests",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["request_id"].startswith("req_")


@pytest.mark.asyncio
async def test_max_retries_exceeded(
    client: AsyncClient, ops_token: str, generation_requests
):
    req = generation_requests[4]
    assert req.status == "failed_permanent"
    assert req.retry_count == 3
    response = await client.post(
        f"/api/v1/ops/generation/requests/{req.request_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-status-maxretries",
        },
        json={"status": "pending"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == "INVALID_REQUEST_STATUS"
