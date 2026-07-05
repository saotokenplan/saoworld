import pytest
from httpx import AsyncClient

from app.core.errors import GenerationErrorCodes


@pytest.mark.asyncio
async def test_list_generated_objects_success(
    client: AsyncClient, ops_token: str, generated_objects
):
    response = await client.get(
        "/api/v1/ops/generation/objects",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["data"]["total"] == 4
    assert len(data["data"]["objects"]) == 4
    assert data["meta"]["total"] == 4
    assert data["meta"]["limit"] == 20
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_list_generated_objects_with_status_filter(
    client: AsyncClient, ops_token: str, generated_objects
):
    response = await client.get(
        "/api/v1/ops/generation/objects?status=approved",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["objects"][0]["status"] == "approved"


@pytest.mark.asyncio
async def test_list_generated_objects_with_type_filter(
    client: AsyncClient, ops_token: str, generated_objects
):
    response = await client.get(
        "/api/v1/ops/generation/objects?object_type=npc",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 2
    for obj in data["data"]["objects"]:
        assert obj["object_type"] == "npc"


@pytest.mark.asyncio
async def test_list_generated_objects_pagination(
    client: AsyncClient, ops_token: str, generated_objects
):
    response = await client.get(
        "/api/v1/ops/generation/objects?limit=2&offset=0",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["objects"]) == 2
    assert data["meta"]["limit"] == 2
    assert data["meta"]["offset"] == 0
    assert data["meta"]["total"] == 4


@pytest.mark.asyncio
async def test_get_generated_object_detail_success(
    client: AsyncClient, ops_token: str, generated_objects
):
    obj = generated_objects[0]
    response = await client.get(
        f"/api/v1/ops/generation/objects/{obj.object_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["object_id"] == str(obj.object_id)
    assert data["data"]["object_type"] == obj.object_type
    assert data["data"]["status"] == obj.status
    assert data["data"]["quality_score"] == obj.quality_score


@pytest.mark.asyncio
async def test_get_generated_object_not_found(
    client: AsyncClient, ops_token: str
):
    import uuid

    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/ops/generation/objects/{fake_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == GenerationErrorCodes.OBJECT_NOT_FOUND


@pytest.mark.asyncio
async def test_update_object_status_pending_to_approved(
    client: AsyncClient, ops_token: str, generated_objects
):
    obj = generated_objects[0]
    assert obj.status == "pending_review"
    response = await client.post(
        f"/api/v1/ops/generation/objects/{obj.object_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-obj-status-001",
        },
        json={"status": "approved"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "approved"


@pytest.mark.asyncio
async def test_update_object_status_pending_to_rejected(
    client: AsyncClient, ops_token: str, generated_objects
):
    obj = generated_objects[0]
    response = await client.post(
        f"/api/v1/ops/generation/objects/{obj.object_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-obj-status-002",
        },
        json={"status": "rejected"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "rejected"


@pytest.mark.asyncio
async def test_update_object_status_pending_to_needs_revision(
    client: AsyncClient, ops_token: str, generated_objects
):
    obj = generated_objects[0]
    response = await client.post(
        f"/api/v1/ops/generation/objects/{obj.object_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-obj-status-003",
        },
        json={"status": "needs_revision"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "needs_revision"


@pytest.mark.asyncio
async def test_update_object_status_needs_revision_to_pending(
    client: AsyncClient, ops_token: str, generated_objects
):
    obj = generated_objects[3]
    assert obj.status == "needs_revision"
    response = await client.post(
        f"/api/v1/ops/generation/objects/{obj.object_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-obj-status-004",
        },
        json={"status": "pending_review"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "pending_review"


@pytest.mark.asyncio
async def test_update_object_status_invalid_transition(
    client: AsyncClient, ops_token: str, generated_objects
):
    obj = generated_objects[1]
    assert obj.status == "approved"
    response = await client.post(
        f"/api/v1/ops/generation/objects/{obj.object_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-obj-status-005",
        },
        json={"status": "pending_review"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == GenerationErrorCodes.INVALID_OBJECT_STATUS


@pytest.mark.asyncio
async def test_update_object_status_not_found(
    client: AsyncClient, ops_token: str
):
    import uuid

    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/ops/generation/objects/{fake_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-obj-status-006",
        },
        json={"status": "approved"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == GenerationErrorCodes.OBJECT_NOT_FOUND


@pytest.mark.asyncio
async def test_generated_object_envelope_format(
    client: AsyncClient, ops_token: str, generated_objects
):
    response = await client.get(
        "/api/v1/ops/generation/objects",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["request_id"].startswith("req_")


@pytest.mark.asyncio
async def test_generated_object_payload_schema_version(
    client: AsyncClient, ops_token: str, generated_objects
):
    obj = generated_objects[0]
    response = await client.get(
        f"/api/v1/ops/generation/objects/{obj.object_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["schema_version"] == 1
    assert isinstance(data["data"]["object_payload"], dict)
