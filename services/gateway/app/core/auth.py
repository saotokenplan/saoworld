from typing import Optional

import structlog
from jose import JWTError, jwt
from fastapi import HTTPException, Request

from app.core.config import settings

logger = structlog.get_logger()


class JWTBearer:
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        if not authorization:
            if self.auto_error:
                raise HTTPException(
                    status_code=401,
                    detail={"code": "UNAUTHORIZED", "message": "未提供认证令牌"},
                )
            return None

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=401,
                    detail={"code": "INVALID_AUTH_SCHEME", "message": "无效的认证方案"},
                )
            return None

        return token


async def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )

        player_id = payload.get("player_id")
        if not player_id:
            raise HTTPException(
                status_code=401,
                detail={"code": "INVALID_TOKEN", "message": "无效的令牌"},
            )

        return {
            "player_id": player_id,
            "roles": payload.get("roles", []),
            "scopes": payload.get("scopes", []),
            "exp": payload.get("exp"),
        }
    except JWTError as exc:
        error_msg = str(exc)
        if "expired" in error_msg.lower():
            raise HTTPException(
                status_code=401,
                detail={"code": "TOKEN_EXPIRED", "message": "令牌已过期"},
            )
        logger.warning("jwt_verification_failed", error=error_msg)
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "令牌验证失败"},
        ) from exc


async def authenticate_request(request: Request) -> dict:
    jwt_bearer = JWTBearer()
    token = await jwt_bearer(request)
    assert token is not None
    return await verify_token(token)
