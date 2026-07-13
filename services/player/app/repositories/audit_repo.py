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
ACTION_REPUTATION_UNLOCK = "reputation_unlock"
ACTION_CONTRIBUTION_ADD = "contribution_add"
ACTION_ACHIEVEMENT_CREATE = "achievement_create"
ACTION_ACHIEVEMENT_UNLOCK = "achievement_unlock"
ACTION_ACHIEVEMENT_REWARD_CLAIM = "achievement_reward_claim"
ACTION_EXPERIENCE_ADD = "experience_add"
ACTION_LEVEL_UP = "level_up"
ACTION_FRIEND_REQUEST_SEND = "friend_request_send"
ACTION_FRIEND_REQUEST_ACCEPT = "friend_request_accept"
ACTION_FRIEND_REQUEST_REJECT = "friend_request_reject"
ACTION_FRIEND_DELETE = "friend_delete"
ACTION_FRIEND_BLOCK = "friend_block"
ACTION_PRIVATE_MESSAGE_SEND = "private_message_send"
ACTION_PRIVATE_MESSAGE_READ = "private_message_read"
ACTION_PRIVATE_MESSAGE_DELETE = "private_message_delete"

# 公会相关动作
ACTION_GUILD_CREATE = "guild_create"
ACTION_GUILD_UPDATE = "guild_update"
ACTION_GUILD_DELETE = "guild_delete"
ACTION_GUILD_MEMBER_ADD = "guild_member_add"
ACTION_GUILD_MEMBER_REMOVE = "guild_member_remove"
ACTION_GUILD_MEMBER_LEAVE = "guild_member_leave"
ACTION_GUILD_TRANSFER_LEADER = "guild_transfer_leader"
ACTION_GUILD_MESSAGE_SEND = "guild_message_send"
ACTION_GUILD_MESSAGE_READ = "guild_message_read"
ACTION_GUILD_MESSAGE_DELETE = "guild_message_delete"

# 装备相关动作
ACTION_EQUIPMENT_EQUIP = "equipment_equip"
ACTION_EQUIPMENT_UNEQUIP = "equipment_unequip"

RESOURCE_PLAYER = "player"
RESOURCE_REGION = "region"
RESOURCE_QUEST = "quest"
RESOURCE_INVENTORY = "inventory"
RESOURCE_REPUTATION = "reputation"
RESOURCE_CONTRIBUTION = "contribution"
RESOURCE_ACHIEVEMENT = "achievement"
RESOURCE_PLAYER_ACHIEVEMENT = "player_achievement"
RESOURCE_EXPERIENCE = "experience"
RESOURCE_FRIENDSHIP = "friendship"
RESOURCE_PRIVATE_MESSAGE = "private_message"
RESOURCE_GUILD = "guild"
RESOURCE_GUILD_MEMBER = "guild_member"
RESOURCE_GUILD_MESSAGE = "guild_message"
RESOURCE_EQUIPMENT = "equipment"


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
