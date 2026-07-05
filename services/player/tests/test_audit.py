import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.models import AuditLog
from app.repositories.audit_repo import (
    ACTION_PLAYER_CREATE,
    ACTION_PLAYER_UPDATE,
    ACTION_REGION_UNLOCK,
    RESOURCE_PLAYER,
    RESOURCE_REGION,
)
from tests.conftest import TestSessionLocal


@pytest.mark.asyncio
async def test_create_player_creates_audit_log(client: AsyncClient, ops_token: str):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-create-001",
        },
        json={"display_name": "AuditTestPlayer"},
    )
    assert response.status_code == 201
    data = response.json()
    player_id = data["data"]["player_id"]

    async with TestSessionLocal() as session:
        logs = await _get_audit_logs(session, player_id)
        assert len(logs) >= 1
        create_log = next((log for log in logs if log.action == ACTION_PLAYER_CREATE), None)
        assert create_log is not None
        assert create_log.resource_type == RESOURCE_PLAYER
        assert create_log.resource_id == uuid.UUID(player_id)
        assert create_log.result_status == 201


@pytest.mark.asyncio
async def test_update_player_creates_audit_log(client: AsyncClient, ops_token: str, test_player):
    response = await client.put(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-update-001",
        },
        json={"display_name": "AuditUpdatedPlayer"},
    )
    assert response.status_code == 200

    async with TestSessionLocal() as session:
        logs = await _get_audit_logs(session, str(test_player.player_id))
        update_log = next((log for log in logs if log.action == ACTION_PLAYER_UPDATE), None)
        assert update_log is not None
        assert update_log.resource_type == RESOURCE_PLAYER
        assert update_log.resource_id == test_player.player_id
        assert update_log.result_status == 200


@pytest.mark.asyncio
async def test_unlock_region_creates_audit_log(client: AsyncClient, ops_token: str, test_player):
    response = await client.post(
        f"{settings.api_v1_prefix}/ops/players/{test_player.player_id}/regions/region_test_01/unlock",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-audit-unlock-001",
        },
    )
    assert response.status_code == 200

    async with TestSessionLocal() as session:
        logs = await _get_audit_logs_by_action(session, ACTION_REGION_UNLOCK)
        unlock_log = next((log for log in logs if str(test_player.player_id) in str(log.request_payload_jsonb)), None)
        assert unlock_log is not None
        assert unlock_log.resource_type == RESOURCE_REGION
        assert unlock_log.result_status == 200


async def _get_audit_logs(session: AsyncSession, resource_id: str) -> list[AuditLog]:
    from sqlalchemy import select

    stmt = select(AuditLog).where(AuditLog.resource_id == uuid.UUID(resource_id))
    result = await session.execute(stmt)
    return result.scalars().all()


async def _get_audit_logs_by_action(session: AsyncSession, action: str) -> list[AuditLog]:
    from sqlalchemy import select

    stmt = select(AuditLog).where(AuditLog.action == action)
    result = await session.execute(stmt)
    return result.scalars().all()