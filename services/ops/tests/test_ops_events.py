import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.errors import OpsErrorCodes
from app.core.event_engine import EventEngine


def _make_event_payload(**overrides):
    base = {
        "event_name": f"test_event_{uuid.uuid4().hex[:8]}",
        "event_type": "double_reward",
        "start_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        "end_at": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        "target_scope": "all",
        "description": "Test event",
        "multiplier_config_jsonb": {"exp": 2.0, "contribution": 1.5},
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_create_event_success(async_client, test_token):
    payload = _make_event_payload()
    response = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["event_name"] == payload["event_name"]
    assert data["data"]["event_type"] == "double_reward"
    assert data["data"]["status"] == "draft"
    assert "event_id" in data["data"]


@pytest.mark.asyncio
async def test_create_event_duplicate_name(async_client, test_token):
    payload = _make_event_payload()
    response1 = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response1.status_code == 200

    response2 = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response2.status_code == 409
    data = response2.json()
    assert data["code"] == OpsErrorCodes.EVENT_NAME_EXISTS


@pytest.mark.asyncio
async def test_list_events(async_client, test_token):
    for i in range(3):
        payload = _make_event_payload(event_name=f"list_test_{i}")
        await async_client.post(
            "/api/v1/ops/events",
            json=payload,
            headers={"Authorization": f"Bearer {test_token}"},
        )

    response = await async_client.get(
        "/api/v1/ops/events",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] >= 3
    assert len(data["data"]) >= 3


@pytest.mark.asyncio
async def test_list_events_with_filters(async_client, test_token):
    for i in range(2):
        payload = _make_event_payload(event_name=f"filter_test_{i}", event_type="sale")
        await async_client.post(
            "/api/v1/ops/events",
            json=payload,
            headers={"Authorization": f"Bearer {test_token}"},
        )

    response = await async_client.get(
        "/api/v1/ops/events?event_type=sale",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] >= 2
    for item in data["data"]:
        assert item["event_type"] == "sale"


@pytest.mark.asyncio
async def test_get_event_detail(async_client, test_token):
    payload = _make_event_payload()
    create_resp = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    event_id = create_resp.json()["data"]["event_id"]

    response = await async_client.get(
        f"/api/v1/ops/events/{event_id}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["event_id"] == event_id
    assert data["data"]["event_name"] == payload["event_name"]


@pytest.mark.asyncio
async def test_get_event_not_found(async_client, test_token):
    fake_id = uuid.uuid4()
    response = await async_client.get(
        f"/api/v1/ops/events/{fake_id}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == OpsErrorCodes.EVENT_NOT_FOUND


@pytest.mark.asyncio
async def test_update_event(async_client, test_token):
    payload = _make_event_payload()
    create_resp = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    event_id = create_resp.json()["data"]["event_id"]

    update_data = {"description": "Updated description"}
    response = await async_client.put(
        f"/api/v1/ops/events/{event_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["description"] == "Updated description"


@pytest.mark.asyncio
async def test_event_status_transitions(async_client, test_token):
    payload = _make_event_payload()
    create_resp = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    event_id = create_resp.json()["data"]["event_id"]

    activate_resp = await async_client.post(
        f"/api/v1/ops/events/{event_id}/activate",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert activate_resp.status_code == 200
    assert activate_resp.json()["data"]["status"] == "active"

    pause_resp = await async_client.post(
        f"/api/v1/ops/events/{event_id}/pause",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert pause_resp.status_code == 200
    assert pause_resp.json()["data"]["status"] == "paused"

    end_resp = await async_client.post(
        f"/api/v1/ops/events/{event_id}/end",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert end_resp.status_code == 200
    assert end_resp.json()["data"]["status"] == "ended"


@pytest.mark.asyncio
async def test_invalid_status_transition(async_client, test_token):
    payload = _make_event_payload()
    create_resp = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    event_id = create_resp.json()["data"]["event_id"]

    pause_resp = await async_client.post(
        f"/api/v1/ops/events/{event_id}/pause",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert pause_resp.status_code == 409
    data = pause_resp.json()
    assert data["code"] == OpsErrorCodes.INVALID_EVENT_STATUS


@pytest.mark.asyncio
async def test_delete_event(async_client, test_token):
    payload = _make_event_payload()
    create_resp = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    event_id = create_resp.json()["data"]["event_id"]

    delete_resp = await async_client.delete(
        f"/api/v1/ops/events/{event_id}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["data"]["deleted"] is True

    get_resp = await async_client.get(
        f"/api/v1/ops/events/{event_id}",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["data"]["status"] == "archived"


@pytest.mark.asyncio
async def test_get_active_events_ops(async_client, test_token):
    payload = _make_event_payload()
    create_resp = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    event_id = create_resp.json()["data"]["event_id"]

    await async_client.post(
        f"/api/v1/ops/events/{event_id}/activate",
        headers={"Authorization": f"Bearer {test_token}"},
    )

    response = await async_client.get(
        "/api/v1/ops/events/active",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert any(e["event_id"] == event_id for e in data["data"])


def test_event_engine_is_active():
    from app.domain.models import OpsEvent

    now = datetime.now(timezone.utc)
    event = OpsEvent(
        event_id=uuid.uuid4(),
        event_name="test",
        event_type="double_reward",
        status="active",
        start_at=now - timedelta(hours=1),
        end_at=now + timedelta(hours=1),
        target_scope="all",
        created_by="test",
    )

    assert EventEngine.is_event_active(event, now) is True

    event.status = "draft"
    assert EventEngine.is_event_active(event, now) is False

    event.status = "active"
    event.end_at = now - timedelta(hours=1)
    assert EventEngine.is_event_active(event, now) is False


def test_event_engine_multiplier():
    from app.domain.models import OpsEvent

    now = datetime.now(timezone.utc)
    events = [
        OpsEvent(
            event_id=uuid.uuid4(),
            event_name="ev1",
            event_type="double_reward",
            status="active",
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(hours=1),
            target_scope="all",
            multiplier_config_jsonb={"exp": 2.0, "stack_mode": "additive"},
            created_by="test",
        ),
        OpsEvent(
            event_id=uuid.uuid4(),
            event_name="ev2",
            event_type="double_reward",
            status="active",
            start_at=now - timedelta(hours=1),
            end_at=now + timedelta(hours=1),
            target_scope="all",
            multiplier_config_jsonb={"exp": 1.5, "stack_mode": "additive"},
            created_by="test",
        ),
    ]

    mult = EventEngine.calculate_reward_multiplier(events, "exp")
    assert mult == 2.5


def test_event_engine_validate_config_valid():
    valid_data = {
        "event_name": "test",
        "event_type": "double_reward",
        "start_at": datetime.now(timezone.utc),
        "end_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "target_scope": "all",
    }
    valid, errors = EventEngine.validate_event_config(valid_data)
    assert valid is True
    assert len(errors) == 0


def test_event_engine_validate_config_invalid():
    invalid_data = {
        "event_name": "",
        "event_type": "invalid_type",
        "start_at": datetime.now(timezone.utc) + timedelta(hours=2),
        "end_at": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    valid, errors = EventEngine.validate_event_config(invalid_data)
    assert valid is False
    assert len(errors) > 0


def test_event_engine_boundary_time():
    from app.domain.models import OpsEvent

    start = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)

    event = OpsEvent(
        event_id=uuid.uuid4(),
        event_name="test",
        event_type="double_reward",
        status="active",
        start_at=start,
        end_at=end,
        target_scope="all",
        created_by="test",
    )

    assert EventEngine.is_event_active(event, start) is True
    assert EventEngine.is_event_active(event, end) is True
    assert EventEngine.is_event_active(event, start - timedelta(seconds=1)) is False
    assert EventEngine.is_event_active(event, end + timedelta(seconds=1)) is False


@pytest.mark.asyncio
async def test_player_get_active_events(async_client, player_token, test_token):
    payload = _make_event_payload()
    create_resp = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={"Authorization": f"Bearer {test_token}"},
    )
    event_id = create_resp.json()["data"]["event_id"]

    await async_client.post(
        f"/api/v1/ops/events/{event_id}/activate",
        headers={"Authorization": f"Bearer {test_token}"},
    )

    response = await async_client.get(
        "/api/v1/player/events/active",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_player_events_unauthorized(async_client):
    response = await async_client.get("/api/v1/player/events/active")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_event_audit_log(async_client, test_token):
    payload = _make_event_payload()
    response = await async_client.post(
        "/api/v1/ops/events",
        json=payload,
        headers={
            "Authorization": f"Bearer {test_token}",
            "X-Trace-Id": "trace_test_audit",
        },
    )
    assert response.status_code == 200

    audit_resp = await async_client.get(
        "/api/v1/ops/actions?action_type=event_create",
        headers={"Authorization": f"Bearer {test_token}"},
    )
    assert audit_resp.status_code == 200
