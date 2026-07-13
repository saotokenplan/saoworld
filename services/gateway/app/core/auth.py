from typing import Optional

import structlog
from jose import JWTError, jwt
from fastapi import HTTPException, Request

from app.core.config import settings

logger = structlog.get_logger()


PATH_SCOPE_RULES: dict[str, list[str]] = {
    "/api/v1/votes/current": ["votes:read"],
    "/api/v1/votes/current/progress": ["votes:read"],
    "/api/v1/votes/history": ["votes:history:read"],
    "/api/v1/votes/submit": ["votes:submit"],
    "/api/v1/votes/discussions": ["votes:discussions:read"],
    "/api/v1/ops/": ["ops:*"],
    "/api/v1/content/release": ["content:release"],
    "/api/v1/content/rollback": ["content:rollback"],
}


def get_required_scopes(path: str) -> list[str]:
    for prefix, scopes in PATH_SCOPE_RULES.items():
        if path.startswith(prefix):
            return scopes
    return []


def has_required_scope(user_scopes: list[str], required_scopes: list[str]) -> bool:
    user_scope_set = set(user_scopes)
    for required in required_scopes:
        if required == "*":
            return True
        if required.endswith(":*"):
            prefix = required[:-2]
            if any(s.startswith(prefix) for s in user_scope_set):
                return True
        if required in user_scope_set:
            return True
    return False


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

        player_id = payload.get("player_id") or payload.get("sub")
        if not player_id:
            raise HTTPException(
                status_code=401,
                detail={"code": "INVALID_TOKEN", "message": "无效的令牌"},
            )

        scopes_raw = payload.get("scope", payload.get("scopes", []))
        if isinstance(scopes_raw, str):
            scopes = scopes_raw.split() if scopes_raw else []
        else:
            scopes = list(scopes_raw)

        return {
            "player_id": player_id,
            "roles": payload.get("roles", []),
            "scopes": scopes,
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
    user = await verify_token(token)

    required_scopes = get_required_scopes(request.url.path)
    if required_scopes and not has_required_scope(user.get("scopes", []), required_scopes):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FORBIDDEN",
                "message": f"缺少必要的权限: {required_scopes}",
            },
        )

    return user
