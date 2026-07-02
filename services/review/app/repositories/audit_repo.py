import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuditLog

ACTION_REVIEW_RECORD_CREATE = "review_record_create"
ACTION_REVIEW_APPROVE = "review_approve"
ACTION_REVIEW_REJECT = "review_reject"
ACTION_REVIEW_RESULT_UPDATE = "review_result_update"

RESOURCE_REVIEW_RECORD = "review_record"


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