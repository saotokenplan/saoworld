from typing import NoReturn

from fastapi import HTTPException, status

from app.schemas.world import ErrorDetail, ErrorResponse


class WorldErrorCodes:
    REGION_NOT_FOUND = "REGION_NOT_FOUND"
    INVALID_REGION_STATUS = "INVALID_REGION_STATUS"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AUDIT_WRITE_FAILED = "AUDIT_WRITE_FAILED"
    TRACE_ID_MISSING = "TRACE_ID_MISSING"
    TASK_DISPATCH_FAILED = "TASK_DISPATCH_FAILED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    SKELETON_NOT_FOUND = "SKELETON_NOT_FOUND"
    SKELETON_VERSION_EXISTS = "SKELETON_VERSION_EXISTS"
    NPC_NOT_FOUND = "NPC_NOT_FOUND"
    QUEST_NOT_FOUND = "QUEST_NOT_FOUND"
    NPC_KEY_EXISTS = "NPC_KEY_EXISTS"
    QUEST_KEY_EXISTS = "QUEST_KEY_EXISTS"
    INVALID_NPC_KEY = "INVALID_NPC_KEY"
    INVALID_QUEST_KEY = "INVALID_QUEST_KEY"
    INVALID_QUEST_TYPE = "INVALID_QUEST_TYPE"
    ITEM_NOT_FOUND = "ITEM_NOT_FOUND"
    ITEM_KEY_EXISTS = "ITEM_KEY_EXISTS"
    INVALID_ITEM_TYPE = "INVALID_ITEM_TYPE"
    INVALID_ITEM_SLOT = "INVALID_ITEM_SLOT"
    INVALID_ITEM_RARITY = "INVALID_ITEM_RARITY"


def raise_world_error(
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
