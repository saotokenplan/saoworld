from typing import NoReturn

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas.base import ErrorResponse, ErrorDetail


class GatewayErrorCodes:
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_SCOPE = "INSUFFICIENT_SCOPE"
    RATE_LIMITED = "RATE_LIMITED"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    GATEWAY_TIMEOUT = "GATEWAY_TIMEOUT"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
    AUDIT_WRITE_FAILED = "AUDIT_WRITE_FAILED"
    TRACE_ID_MISSING = "TRACE_ID_MISSING"
    TASK_DISPATCH_FAILED = "TASK_DISPATCH_FAILED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"


def raise_gateway_error(
    code: str,
    message: str,
    status_code: int = 400,
    details: list[ErrorDetail] | None = None,
) -> NoReturn:
    error_response = ErrorResponse(
        code=code,
        message=message,
        request_id="",
        details=details or [],
    )
    raise HTTPException(
        status_code=status_code,
        detail=error_response.model_dump(),
    )


async def gateway_error_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict):
        if "code" in detail and "message" in detail:
            return JSONResponse(
                status_code=exc.status_code,
                content=detail,
            )
    error_response = ErrorResponse(
        code=f"HTTP_{exc.status_code}",
        message=str(exc.detail),
        request_id=getattr(request.state, "request_id", ""),
        details=[],
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
    )
