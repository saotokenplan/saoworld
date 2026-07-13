import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog

ACTION_DASHBOARD_VIEW = "dashboard_view"
ACTION_OPS_ACTION_QUERY = "ops_action_query"
ACTION_SYSTEM_STATUS_QUERY = "system_status_query"
ACTION_ANALYTICS_QUERY = "analytics_query"
ACTION_INSIGHT_QUERY = "insight_query"
ACTION_REQUIREMENT_QUERY = "requirement_query"
ACTION_REQUIREMENT_APPROVE = "requirement_approve"
ACTION_VOTE_CYCLE_CREATE = "vote_cycle_create"
ACTION_VOTE_CYCLE_SCHEDULE = "vote_cycle_schedule"
ACTION_VOTE_CYCLE_OPEN = "vote_cycle_open"
ACTION_VOTE_CYCLE_CLOSE = "vote_cycle_close"
ACTION_VOTE_CYCLE_FINALIZE = "vote_cycle_finalize"
ACTION_CONTENT_RELEASE = "content_release"
ACTION_CONTENT_ROLLBACK = "content_rollback"
ACTION_REVIEW_APPROVE = "review_approve"
ACTION_REVIEW_REJECT = "review_reject"

RESOURCE_DASHBOARD = "dashboard"
RESOURCE_OPS_ACTION = "ops_action"
RESOURCE_SYSTEM = "system"
RESOURCE_ANALYTICS = "analytics"
RESOURCE_INSIGHT = "insight"
RESOURCE_REQUIREMENT = "requirement"
RESOURCE_VOTE_CYCLE = "vote_cycle"
RESOURCE_CONTENT_PACKAGE = "content_package"
RESOURCE_REVIEW_OBJECT = "review_object"


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
