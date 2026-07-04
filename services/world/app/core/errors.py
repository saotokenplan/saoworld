from fastapi import HTTPException, status

from app.schemas.world import ErrorDetail, ErrorResponse


class WorldErrorCodes:
    REGION_NOT_FOUND = "REGION_NOT_FOUND"
    INVALID_REGION_STATUS = "INVALID_REGION_STATUS"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def raise_world_error(
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
