import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog

ACTION_PLAYER_CREATE = "player_create"
ACTION_PLAYER_UPDATE = "player_update"
ACTION_REGION_UNLOCK = "region_unlock"
ACTION_QUEST_UPDATE = "quest_update"
ACTION_QUEST_ACCEPT = "quest_accept"
ACTION_QUEST_COMPLETE = "quest_complete"
ACTION_QUEST_FAIL = "quest_fail"
ACTION_QUEST_PROGRESS_UPDATE = "quest_progress_update"
ACTION_QUEST_CREATE = "quest_create"
ACTION_QUEST_STATUS_UPDATE = "quest_status_update"
ACTION_INVENTORY_ADD = "inventory_add"
ACTION_INVENTORY_REMOVE = "inventory_remove"
ACTION_INVENTORY_USE = "inventory_use"
ACTION_REPUTATION_ADD = "reputation_add"
ACTION_REPUTATION_REMOVE = "reputation_remove"
ACTION_REPUTATION_ADJUST = "reputation_adjust"

RESOURCE_PLAYER = "player"
RESOURCE_REGION = "region"
RESOURCE_QUEST = "quest"
RESOURCE_INVENTORY = "inventory"
RESOURCE_REPUTATION = "reputation"


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_audit_log(
        self,
        *,
        trace_id: str,
        request_id: str | None = None,
        operator_id: str,
        operator_role: str,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        reason: str | None = None,
        request_payload_jsonb: dict[str, Any] | None = None,
        result_status: int | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            audit_id=uuid.uuid4(),
            trace_id=trace_id,
            request_id=request_id,
            operator_id=operator_id,
            operator_role=operator_role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            reason=reason,
            request_payload_jsonb=request_payload_jsonb,
            result_status=result_status,
        )
        self.db.add(audit_log)
        await self.db.flush()
        return audit_log