from fastapi import HTTPException, status

from app.schemas.player import ErrorDetail, ErrorResponse


class PlayerErrorCodes:
    PLAYER_NOT_FOUND = "PLAYER_NOT_FOUND"
    INVALID_PLAYER_ID = "INVALID_PLAYER_ID"
    INVALID_QUEST_STATUS = "INVALID_QUEST_STATUS"
    REGION_NOT_FOUND = "REGION_NOT_FOUND"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def raise_player_error(
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
