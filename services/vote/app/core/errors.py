from fastapi import HTTPException, status

from app.schemas.vote import ErrorDetail, ErrorResponse


class VoteErrorCodes:
    VOTE_CYCLE_NOT_FOUND = "VOTE_CYCLE_NOT_FOUND"
    NO_OPEN_VOTE_CYCLE = "NO_OPEN_VOTE_CYCLE"
    INVALID_VOTE_STATE = "INVALID_VOTE_STATE"
    CANDIDATE_NOT_FOUND = "CANDIDATE_NOT_FOUND"
    CANDIDATE_NOT_ACTIVE = "CANDIDATE_NOT_ACTIVE"
    ALREADY_VOTED = "ALREADY_VOTED"
    DUPLICATE_VOTE = "DUPLICATE_VOTE"
    INVALID_PLAYER_ID = "INVALID_PLAYER_ID"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    VOTE_CYCLE_CONFLICT = "VOTE_CYCLE_CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    AUDIT_WRITE_FAILED = "AUDIT_WRITE_FAILED"
    TRACE_ID_MISSING = "TRACE_ID_MISSING"
    TASK_DISPATCH_FAILED = "TASK_DISPATCH_FAILED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"


def raise_vote_error(
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
