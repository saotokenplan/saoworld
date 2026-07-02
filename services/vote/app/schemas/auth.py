"""认证相关的 Pydantic Schema。"""

from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    """用户角色枚举。"""

    PLAYER = "player"
    OPS = "ops"
    REVIEWER = "reviewer"
    SYSTEM = "system"


class Scope(str, Enum):
    """权限 Scope 枚举。"""

    # 玩家权限
    WORLD_READ = "world:read"
    QUESTS_READ = "quests:read"
    VOTES_READ = "votes:read"
    VOTES_SUBMIT = "votes:submit"
    VOTES_HISTORY_READ = "votes:history:read"
    CONTENT_READ = "content:read"

    # 运营权限
    OPS_VOTE_CYCLES_WRITE = "ops:vote-cycles:write"
    CONTENT_RELEASE = "content:release"
    CONTENT_ROLLBACK = "content:rollback"

    # 审核权限
    REVIEW_APPROVE = "review:approve"


# 角色 -> Scope 映射
ROLE_SCOPES: dict[Role, list[Scope]] = {
    Role.PLAYER: [
        Scope.WORLD_READ,
        Scope.QUESTS_READ,
        Scope.VOTES_READ,
        Scope.VOTES_SUBMIT,
        Scope.VOTES_HISTORY_READ,
        Scope.CONTENT_READ,
    ],
    Role.OPS: [
        Scope.VOTES_HISTORY_READ,
        Scope.CONTENT_READ,
        Scope.OPS_VOTE_CYCLES_WRITE,
        Scope.CONTENT_RELEASE,
        Scope.CONTENT_ROLLBACK,
    ],
    Role.REVIEWER: [
        Scope.CONTENT_READ,
        Scope.REVIEW_APPROVE,
    ],
    Role.SYSTEM: [
        # system 角色具备所有权限
        Scope.WORLD_READ,
        Scope.QUESTS_READ,
        Scope.VOTES_READ,
        Scope.VOTES_HISTORY_READ,
        Scope.CONTENT_READ,
        Scope.OPS_VOTE_CYCLES_WRITE,
        Scope.CONTENT_RELEASE,
        Scope.CONTENT_ROLLBACK,
        Scope.REVIEW_APPROVE,
    ],
}


class TokenData(BaseModel):
    """JWT Token 解析后的数据。"""

    sub: str = Field(..., description="用户ID（subject）")
    role: Role = Field(..., description="用户角色")
    scopes: list[str] = Field(default_factory=list, description="用户具备的 Scope 列表")
    exp: float | None = Field(default=None, description="过期时间戳")


class UserPayload(BaseModel):
    """当前用户信息，用于依赖注入。"""

    user_id: str = Field(..., description="用户ID")
    role: Role = Field(..., description="用户角色")
    scopes: list[str] = Field(default_factory=list, description="用户具备的 Scope 列表")

    def has_scope(self, scope: str | Scope) -> bool:
        """检查用户是否具备指定 Scope。"""
        scope_str = scope.value if isinstance(scope, Scope) else scope
        return scope_str in self.scopes

    def has_role(self, role: Role) -> bool:
        """检查用户是否具备指定角色。"""
        return self.role == role