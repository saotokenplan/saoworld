from fastapi import HTTPException, status

from app.schemas.review import ErrorDetail, ErrorResponse


class ReviewErrorCodes:
    REVIEW_NOT_FOUND = "REVIEW_NOT_FOUND"
    REVIEW_RECORD_NOT_FOUND = "REVIEW_RECORD_NOT_FOUND"
    INVALID_REVIEW_STATUS = "INVALID_REVIEW_STATUS"
    NO_REVIEWS_FOUND = "NO_REVIEWS_FOUND"
    REVIEW_OBJECT_NOT_FOUND = "REVIEW_OBJECT_NOT_FOUND"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def raise_review_error(
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
