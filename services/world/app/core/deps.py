from typing import Any

from fastapi import Depends, Header, HTTPException, status

from app.core.auth import (
    ExpiredTokenError,
    InvalidTokenError,
    MissingTokenError,
    decode_jwt_token,
)
from app.schemas.auth import Role, Scope, UserPayload


def extract_bearer_token(authorization: str | None) -> str:
    if authorization is None:
        raise MissingTokenError()

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidTokenError("Authorization 头格式无效，应为 'Bearer <token>'")

    return parts[1]


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> UserPayload:
    try:
        token = extract_bearer_token(authorization)
        token_data = decode_jwt_token(token)
    except MissingTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ExpiredTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": e.code,
                "message": e.message,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserPayload(
        user_id=token_data.sub,
        role=token_data.role,
        scopes=token_data.scopes,
    )


def require_scope(required_scope: str | Scope) -> Any:
    scope_str = required_scope if isinstance(required_scope, str) else required_scope.value

    async def scope_checker(
        user: UserPayload = Depends(get_current_user),
    ) -> UserPayload:
        if not user.has_scope(scope_str):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": f"缺少必要的权限: {scope_str}",
                },
            )
        return user

    return Depends(scope_checker)


def require_role(required_role: Role) -> Any:
    async def role_checker(
        user: UserPayload = Depends(get_current_user),
    ) -> UserPayload:
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": f"缺少必要的角色: {required_role.value}",
                },
            )
        return user

    return Depends(role_checker)


RequireWorldReadScope = require_scope(Scope.WORLD_READ)
RequireOpsRole = require_role(Role.OPS)
