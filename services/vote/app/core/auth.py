"""JWT 认证核心逻辑。"""

from datetime import datetime, timezone
from typing import Any

from jose import JWTError, jwt  # type: ignore[import-untyped]

from app.core.config import settings
from app.schemas.auth import Role, TokenData


class AuthError(Exception):
    """认证错误基类。"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidTokenError(AuthError):
    """无效 Token 错误。"""

    def __init__(self, message: str = "无效的认证令牌"):
        super().__init__("INVALID_TOKEN", message)


class ExpiredTokenError(AuthError):
    """过期 Token 错误。"""

    def __init__(self, message: str = "认证令牌已过期"):
        super().__init__("TOKEN_EXPIRED", message)


class MissingTokenError(AuthError):
    """缺少 Token 错误。"""

    def __init__(self, message: str = "缺少认证令牌"):
        super().__init__("MISSING_TOKEN", message)


def decode_jwt_token(token: str) -> TokenData:
    """解析并验证 JWT Token。

    Args:
        token: JWT Token 字符串

    Returns:
        TokenData: 解析后的 Token 数据

    Raises:
        InvalidTokenError: Token 格式无效或签名错误
        ExpiredTokenError: Token 已过期
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as e:
        if "expired" in str(e).lower():
            raise ExpiredTokenError()
        raise InvalidTokenError(f"Token 解析失败: {e}")

    # 提取必要字段
    sub = payload.get("sub")
    if sub is None:
        raise InvalidTokenError("Token 缺少 sub 声明")

    role_str = payload.get("role", "player")
    try:
        role = Role(role_str)
    except ValueError:
        raise InvalidTokenError(f"无效的角色声明: {role_str}")

    # Scope 可以是字符串列表或空字符串分隔的单个字符串
    scopes_raw = payload.get("scope", payload.get("scopes", []))
    if isinstance(scopes_raw, str):
        scopes = scopes_raw.split() if scopes_raw else []
    else:
        scopes = list(scopes_raw)

    exp = payload.get("exp")

    return TokenData(
        sub=sub,
        role=role,
        scopes=scopes,
        exp=exp,
    )


def create_test_token(
    user_id: str,
    role: Role,
    scopes: list[str] | None = None,
    expire_minutes: int | None = None,
) -> str:
    """创建测试用的 JWT Token（仅用于开发和测试）。

    Args:
        user_id: 用户ID
        role: 用户角色
        scopes: Scope 列表，如果为 None 则使用角色默认 Scope
        expire_minutes: 过期时间（分钟），如果为 None 则使用配置默认值

    Returns:
        str: JWT Token 字符串
    """
    from datetime import timedelta

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expire_minutes or settings.access_token_expire_minutes
    )

    if scopes is None:
        # 使用角色的默认 Scope
        from app.schemas.auth import ROLE_SCOPES
        role_scopes = ROLE_SCOPES.get(role, [])
        scopes = [s.value for s in role_scopes]

    payload = {
        "sub": user_id,
        "role": role.value,
        "scope": " ".join(scopes),
        "exp": expire.timestamp(),
        "iat": datetime.now(timezone.utc).timestamp(),
    }

    return str(jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    ))