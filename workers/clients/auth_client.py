from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt

from workers.config import settings


def create_jwt_token(
    subject: str,
    role: str = "system",
    scopes: list[str] | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = datetime.now(timezone.utc) + expires_delta

    claims: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    if scopes:
        claims["scopes"] = scopes

    token: str = jwt.encode(claims, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token


def get_system_token(scopes: list[str]) -> str:
    return create_jwt_token(
        subject="system",
        role="system",
        scopes=scopes,
    )