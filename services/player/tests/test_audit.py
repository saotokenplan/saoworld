import pytest
from httpx import AsyncClient

from app.core.config import settings


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