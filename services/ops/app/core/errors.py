from fastapi import HTTPException, status

from app.schemas.ops import ErrorDetail, ErrorResponse


class OpsErrorCodes:
    ACTION_NOT_FOUND = "ACTION_NOT_FOUND"
    DASHBOARD_NOT_FOUND = "DASHBOARD_NOT_FOUND"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def raise_ops_error(
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
