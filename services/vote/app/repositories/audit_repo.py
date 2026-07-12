"""审计日志 Repository。"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog

# 审计操作类型常量
ACTION_VOTE_SUBMIT = "vote_submit"
ACTION_VOTE_CYCLE_CREATE = "vote_cycle_create"
ACTION_VOTE_CYCLE_TRANSITION = "vote_cycle_transition"
ACTION_DISCUSSION_CREATE = "discussion_create"
ACTION_DISCUSSION_LIKE = "discussion_like"
ACTION_REPLY_CREATE = "reply_create"
ACTION_DISCUSSION_DELETE = "discussion_delete"
ACTION_REPLY_DELETE = "reply_delete"

# 资源类型常量
RESOURCE_VOTE = "vote"
RESOURCE_VOTE_CYCLE = "vote_cycle"
RESOURCE_DISCUSSION = "discussion"
RESOURCE_DISCUSSION_REPLY = "discussion_reply"


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
        """写入一条审计日志记录。"""
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
