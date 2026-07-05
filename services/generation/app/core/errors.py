from typing import NoReturn

from fastapi import HTTPException, status

from app.schemas.generation import ErrorDetail, ErrorResponse


class GenerationErrorCodes:
    REQUEST_NOT_FOUND = "REQUEST_NOT_FOUND"
    GENERATION_REQUEST_NOT_FOUND = "GENERATION_REQUEST_NOT_FOUND"
    OBJECT_NOT_FOUND = "OBJECT_NOT_FOUND"
    GENERATED_OBJECT_NOT_FOUND = "GENERATED_OBJECT_NOT_FOUND"
    INVALID_REQUEST_STATUS = "INVALID_REQUEST_STATUS"
    INVALID_OBJECT_STATUS = "INVALID_OBJECT_STATUS"
    MAX_RETRIES_EXCEEDED = "MAX_RETRIES_EXCEEDED"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AUDIT_WRITE_FAILED = "AUDIT_WRITE_FAILED"
    TRACE_ID_MISSING = "TRACE_ID_MISSING"
    TASK_DISPATCH_FAILED = "TASK_DISPATCH_FAILED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"


def raise_generation_error(
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
