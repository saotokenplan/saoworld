from typing import NoReturn

from fastapi import HTTPException, status

from app.schemas.player import ErrorDetail, ErrorResponse


class PlayerErrorCodes:
    PLAYER_NOT_FOUND = "PLAYER_NOT_FOUND"
    INVALID_PLAYER_ID = "INVALID_PLAYER_ID"
    INVALID_QUEST_STATUS = "INVALID_QUEST_STATUS"
    REGION_NOT_FOUND = "REGION_NOT_FOUND"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AUDIT_WRITE_FAILED = "AUDIT_WRITE_FAILED"
    TRACE_ID_MISSING = "TRACE_ID_MISSING"
    TASK_DISPATCH_FAILED = "TASK_DISPATCH_FAILED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"


def raise_player_error(
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
