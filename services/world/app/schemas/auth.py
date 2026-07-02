from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    PLAYER = "player"
    OPS = "ops"
    REVIEWER = "reviewer"
    SYSTEM = "system"


class Scope(str, Enum):
    WORLD_READ = "world:read"
    QUESTS_READ = "quests:read"
    VOTES_READ = "votes:read"
    VOTES_SUBMIT = "votes:submit"
    VOTES_HISTORY_READ = "votes:history:read"
    CONTENT_READ = "content:read"

    OPS_VOTE_CYCLES_WRITE = "ops:vote-cycles:write"
    OPS_WORLD_WRITE = "ops:world:write"
    CONTENT_RELEASE = "content:release"
    CONTENT_ROLLBACK = "content:rollback"

    REVIEW_APPROVE = "review:approve"


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
        Scope.WORLD_READ,
        Scope.VOTES_HISTORY_READ,
        Scope.CONTENT_READ,
        Scope.OPS_VOTE_CYCLES_WRITE,
        Scope.OPS_WORLD_WRITE,
        Scope.CONTENT_RELEASE,
        Scope.CONTENT_ROLLBACK,
    ],
    Role.REVIEWER: [
        Scope.CONTENT_READ,
        Scope.REVIEW_APPROVE,
    ],
    Role.SYSTEM: [
        Scope.WORLD_READ,
        Scope.QUESTS_READ,
        Scope.VOTES_READ,
        Scope.VOTES_HISTORY_READ,
        Scope.CONTENT_READ,
        Scope.OPS_VOTE_CYCLES_WRITE,
        Scope.OPS_WORLD_WRITE,
        Scope.CONTENT_RELEASE,
        Scope.CONTENT_ROLLBACK,
        Scope.REVIEW_APPROVE,
    ],
}


class TokenData(BaseModel):
    sub: str = Field(..., description="用户ID（subject）")
    role: Role = Field(..., description="用户角色")
    scopes: list[str] = Field(default_factory=list, description="用户具备的 Scope 列表")
    exp: float | None = Field(default=None, description="过期时间戳")


class UserPayload(BaseModel):
    user_id: str = Field(..., description="用户ID")
    role: Role = Field(..., description="用户角色")
    scopes: list[str] = Field(default_factory=list, description="用户具备的 Scope 列表")

    def has_scope(self, scope: str | Scope) -> bool:
        scope_str = scope.value if isinstance(scope, Scope) else scope
        return scope_str in self.scopes

    def has_role(self, role: Role) -> bool:
        return self.role == role
