from typing import NoReturn

from fastapi import HTTPException, status

from app.schemas.ops import ErrorDetail, ErrorResponse


class OpsErrorCodes:
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    DASHBOARD_NOT_FOUND = "DASHBOARD_NOT_FOUND"
    INSIGHT_NOT_FOUND = "INSIGHT_NOT_FOUND"
    REQUIREMENT_NOT_FOUND = "REQUIREMENT_NOT_FOUND"
    EVENT_NOT_FOUND = "EVENT_NOT_FOUND"
    EVENT_NAME_EXISTS = "EVENT_NAME_EXISTS"
    INVALID_EVENT_STATUS = "INVALID_EVENT_STATUS"
    EVENT_TIME_OVERLAP = "EVENT_TIME_OVERLAP"
    INVALID_EVENT_CONFIG = "INVALID_EVENT_CONFIG"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AUDIT_WRITE_FAILED = "AUDIT_WRITE_FAILED"
    TRACE_ID_MISSING = "TRACE_ID_MISSING"
    TASK_DISPATCH_FAILED = "TASK_DISPATCH_FAILED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    UPSTREAM_SERVICE_ERROR = "UPSTREAM_SERVICE_ERROR"
    VOTE_CYCLE_CREATE_FAILED = "VOTE_CYCLE_CREATE_FAILED"
    CONTENT_RELEASE_FAILED = "CONTENT_RELEASE_FAILED"
    CONTENT_ROLLBACK_FAILED = "CONTENT_ROLLBACK_FAILED"
    REVIEW_APPROVE_FAILED = "REVIEW_APPROVE_FAILED"
    REVIEW_REJECT_FAILED = "REVIEW_REJECT_FAILED"


def raise_ops_error(
    code: str,
    message: str,
    request_id: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: list[ErrorDetail] | None = None,
) -> NoReturn:
    raise HTTPException(
        status_code=status_code,
        detail=ErrorResponse(
            code=code,
            message=message,
            request_id=request_id,
            details=details or [],
        ).model_dump(),
    )
