import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog

ACTION_REGION_CREATE = "region_create"
ACTION_REGION_STATUS_UPDATE = "region_status_update"
ACTION_NPC_CREATE = "npc_create"
ACTION_QUEST_CREATE = "quest_create"
ACTION_ITEM_CREATE = "item_create"
ACTION_ITEM_UPDATE = "item_update"
ACTION_ITEM_DELETE = "item_delete"
ACTION_MONSTER_CREATE = "monster_create"

RESOURCE_REGION = "region"
RESOURCE_NPC = "npc"
RESOURCE_QUEST = "quest"
RESOURCE_ITEM_DEFINITION = "item_definition"
RESOURCE_MONSTER_DEFINITION = "monster_definition"


class AuditRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_audit_log(
        self,
        *,
        trace_id: str,
        operator_id: str,
        operator_role: str,
        action: str,
        resource_type: str,
        resource_id: uuid.UUID | None = None,
        reason: str | None = None,
        request_id: str | None = None,
        request_payload_jsonb: dict | None = None,
        result_status: int | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
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
