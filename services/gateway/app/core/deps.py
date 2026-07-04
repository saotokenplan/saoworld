
from fastapi import Depends, Request



async def get_current_user(request: Request) -> dict[str, object] | None:
    if hasattr(request.state, "user"):
        return request.state.user  # type: ignore[no-any-return]
    return None


async def require_authenticated_user(user: dict = Depends(get_current_user)) -> dict:
    if not user:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail={"code": "UNAUTHORIZED", "message": "需要认证"},
        )
    return user


async def require_scope(scope: str):
    async def _require_scope(user: dict = Depends(require_authenticated_user)) -> dict:
        if scope not in user.get("scopes", []):
            from fastapi import HTTPException

            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": f"缺少必要的权限: {scope}"},
            )
        return user

    return _require_scope