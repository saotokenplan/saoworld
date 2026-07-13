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
    QUESTS_WRITE = "quests:write"
    VOTES_READ = "votes:read"
    VOTES_SUBMIT = "votes:submit"
    VOTES_HISTORY_READ = "votes:history:read"
    CONTENT_READ = "content:read"
    ACHIEVEMENTS_READ = "achievements:read"
    ACHIEVEMENTS_UNLOCK = "achievements:unlock"

    OPS_VOTE_CYCLES_WRITE = "ops:vote-cycles:write"
    OPS_PLAYERS_WRITE = "ops:players:write"
    OPS_ACHIEVEMENTS_WRITE = "ops:achievements:write"
    CONTENT_RELEASE = "content:release"
    CONTENT_ROLLBACK = "content:rollback"

    FRIENDS_READ = "friends:read"
    FRIENDS_WRITE = "friends:write"

    MESSAGES_READ = "messages:read"
    MESSAGES_WRITE = "messages:write"

    GUILD_READ = "guild:read"
    GUILD_WRITE = "guild:write"

    SOCIAL_READ = "social:read"

    REVIEW_APPROVE = "review:approve"


ROLE_SCOPES: dict[Role, list[Scope]] = {
    Role.PLAYER: [
        Scope.WORLD_READ,
        Scope.QUESTS_READ,
        Scope.QUESTS_WRITE,
        Scope.VOTES_READ,
        Scope.VOTES_SUBMIT,
        Scope.VOTES_HISTORY_READ,
        Scope.CONTENT_READ,
        Scope.ACHIEVEMENTS_READ,
        Scope.FRIENDS_READ,
        Scope.FRIENDS_WRITE,
        Scope.MESSAGES_READ,
        Scope.MESSAGES_WRITE,
        Scope.GUILD_READ,
        Scope.GUILD_WRITE,
        Scope.SOCIAL_READ,
    ],
    Role.OPS: [
        Scope.VOTES_HISTORY_READ,
        Scope.CONTENT_READ,
        Scope.OPS_VOTE_CYCLES_WRITE,
        Scope.OPS_PLAYERS_WRITE,
        Scope.OPS_ACHIEVEMENTS_WRITE,
        Scope.CONTENT_RELEASE,
        Scope.CONTENT_ROLLBACK,
        Scope.ACHIEVEMENTS_READ,
        Scope.ACHIEVEMENTS_UNLOCK,
    ],
    Role.REVIEWER: [
        Scope.CONTENT_READ,
        Scope.REVIEW_APPROVE,
        Scope.ACHIEVEMENTS_READ,
    ],
    Role.SYSTEM: [
        Scope.WORLD_READ,
        Scope.QUESTS_READ,
        Scope.QUESTS_WRITE,
        Scope.VOTES_READ,
        Scope.VOTES_HISTORY_READ,
        Scope.CONTENT_READ,
        Scope.OPS_VOTE_CYCLES_WRITE,
        Scope.OPS_PLAYERS_WRITE,
        Scope.OPS_ACHIEVEMENTS_WRITE,
        Scope.CONTENT_RELEASE,
        Scope.CONTENT_ROLLBACK,
        Scope.REVIEW_APPROVE,
        Scope.ACHIEVEMENTS_READ,
        Scope.ACHIEVEMENTS_UNLOCK,
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
