from fastapi import HTTPException, status

from app.schemas.content import ErrorDetail, ErrorResponse


class ContentErrorCodes:
    PACKAGE_NOT_FOUND = "PACKAGE_NOT_FOUND"
    CONTENT_PACKAGE_NOT_FOUND = "CONTENT_PACKAGE_NOT_FOUND"
    INVALID_PACKAGE_STATE = "INVALID_PACKAGE_STATE"
    CONTENT_PACKAGE_NOT_RELEASABLE = "CONTENT_PACKAGE_NOT_RELEASABLE"
    CONTENT_PACKAGE_NOT_ROLLBACKABLE = "CONTENT_PACKAGE_NOT_ROLLBACKABLE"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AUDIT_WRITE_FAILED = "AUDIT_WRITE_FAILED"
    TRACE_ID_MISSING = "TRACE_ID_MISSING"
    TASK_DISPATCH_FAILED = "TASK_DISPATCH_FAILED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"


def raise_content_error(
    code: str,
    message: str,
    request_id: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    details: list[ErrorDetail] | None = None,
) -> None:
    raise HTTPException(
        status_code=status_code,
        detail=ErrorResponse(
            code=code,
            message=message,
            request_id=request_id,
            details=details or [],
        ).model_dump(),
    )
