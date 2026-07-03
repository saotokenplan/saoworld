from datetime import datetime, timezone

from jose import JWTError, jwt  # type: ignore[import-untyped]

from app.core.config import settings
from app.schemas.auth import Role, TokenData


class AuthError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class InvalidTokenError(AuthError):
    def __init__(self, message: str = "无效的认证令牌"):
        super().__init__("INVALID_TOKEN", message)


class ExpiredTokenError(AuthError):
    def __init__(self, message: str = "认证令牌已过期"):
        super().__init__("TOKEN_EXPIRED", message)


class MissingTokenError(AuthError):
    def __init__(self, message: str = "缺少认证令牌"):
        super().__init__("MISSING_TOKEN", message)


def decode_jwt_token(token: str) -> TokenData:
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

    sub = payload.get("sub")
    if sub is None:
        raise InvalidTokenError("Token 缺少 sub 声明")

    role_str = payload.get("role", "player")
    try:
        role = Role(role_str)
    except ValueError:
        raise InvalidTokenError(f"无效的角色声明: {role_str}")

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
    from datetime import timedelta

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expire_minutes or settings.access_token_expire_minutes
    )

    if scopes is None:
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
