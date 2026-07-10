"""依赖注入工具函数。"""

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
    """从 Authorization 头中提取 Bearer Token。

    Args:
        authorization: Authorization 请求头

    Returns:
        str: 提取的 Token 字符串

    Raises:
        MissingTokenError: 缺少 Token
        InvalidTokenError: Token 格式无效
    """
    if authorization is None:
        raise MissingTokenError()

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidTokenError("Authorization 头格式无效，应为 'Bearer <token>'")

    return parts[1]


async def get_current_user(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> UserPayload:
    """获取当前登录用户信息。

    Args:
        authorization: Authorization 请求头

    Returns:
        UserPayload: 当前用户信息

    Raises:
        HTTPException: 认证失败
    """
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
    """要求用户具备指定的 Scope。

    Args:
        required_scope: 需要的 Scope

    Returns:
        Depends: FastAPI 依赖注入
    """
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


def require_any_scope(required_scopes: list[str | Scope]) -> Any:
    """要求用户具备指定 Scope 列表中的任意一个。

    Args:
        required_scopes: 需要的 Scope 列表

    Returns:
        Depends: FastAPI 依赖注入
    """
    scope_strs = [
        s if isinstance(s, str) else s.value for s in required_scopes
    ]

    async def scope_checker(
        user: UserPayload = Depends(get_current_user),
    ) -> UserPayload:
        if not any(user.has_scope(s) for s in scope_strs):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": f"缺少必要的权限: {', '.join(scope_strs)}",
                },
            )
        return user

    return Depends(scope_checker)


def require_role(required_role: Role) -> Any:
    """要求用户具备指定的角色。

    Args:
        required_role: 需要的角色

    Returns:
        Depends: FastAPI 依赖注入
    """
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


# 预定义的依赖项
RequireOpsRole = require_role(Role.OPS)
RequirePlayerRole = require_role(Role.PLAYER)
RequirePlayerReadScope = require_scope(Scope.WORLD_READ)
RequireQuestsReadScope = require_scope(Scope.QUESTS_READ)
RequireQuestsWriteScope = require_scope(Scope.QUESTS_WRITE)
RequireOpsPlayersWriteScope = require_scope(Scope.OPS_PLAYERS_WRITE)
RequireContributionReadScope = require_any_scope([Scope.QUESTS_READ, Scope.VOTES_SUBMIT])
RequireAchievementsReadScope = require_scope(Scope.ACHIEVEMENTS_READ)
RequireAchievementsUnlockScope = require_scope(Scope.ACHIEVEMENTS_UNLOCK)
RequireOpsAchievementsWriteScope = require_scope(Scope.OPS_ACHIEVEMENTS_WRITE)