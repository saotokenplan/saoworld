import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AchievementDefinition, PlayerAchievement, Player


class AchievementDefinitionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_definitions(
        self,
        *,
        category: str | None = None,
        rarity: str | None = None,
        is_active: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[AchievementDefinition], int]:
        count_stmt = select(sa_func.count(AchievementDefinition.achievement_key))
        stmt: Select[tuple[AchievementDefinition]] = select(AchievementDefinition)

        if category is not None:
            count_stmt = count_stmt.where(AchievementDefinition.category == category)
            stmt = stmt.where(AchievementDefinition.category == category)
        if rarity is not None:
            count_stmt = count_stmt.where(AchievementDefinition.rarity == rarity)
            stmt = stmt.where(AchievementDefinition.rarity == rarity)
        if is_active is not None:
            count_stmt = count_stmt.where(AchievementDefinition.is_active == is_active)
            stmt = stmt.where(AchievementDefinition.is_active == is_active)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = stmt.order_by(AchievementDefinition.points.desc()).limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def get_definition(self, achievement_key: str) -> AchievementDefinition | None:
        stmt = select(AchievementDefinition).where(
            AchievementDefinition.achievement_key == achievement_key
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_definition(
        self,
        *,
        achievement_key: str,
        name: str,
        description: str,
        rarity: str,
        category: str,
        points: int = 10,
        icon: str | None = None,
        reward_jsonb: dict | None = None,
        condition_jsonb: dict | None = None,
    ) -> AchievementDefinition:
        existing = await self.get_definition(achievement_key)
        if existing is not None:
            raise ValueError("成就键已存在")

        definition = AchievementDefinition(
            achievement_key=achievement_key,
            name=name,
            description=description,
            icon=icon,
            rarity=rarity,
            category=category,
            points=points,
            reward_jsonb=reward_jsonb,
            condition_jsonb=condition_jsonb,
        )
        self.db.add(definition)
        await self.db.flush()
        return definition


class PlayerAchievementRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_player_achievements(
        self,
        player_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[PlayerAchievement], int]:
        count_stmt = select(sa_func.count(PlayerAchievement.player_achievement_id)).where(
            PlayerAchievement.player_id == player_id
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[PlayerAchievement]] = (
            select(PlayerAchievement)
            .where(PlayerAchievement.player_id == player_id)
            .order_by(PlayerAchievement.unlocked_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def get_player_achievement(
        self, player_id: uuid.UUID, achievement_key: str
    ) -> PlayerAchievement | None:
        stmt = select(PlayerAchievement).where(
            PlayerAchievement.player_id == player_id,
            PlayerAchievement.achievement_key == achievement_key,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def unlock_achievement(
        self,
        player_id: uuid.UUID,
        achievement_key: str,
        *,
        source: str = "system",
        source_id: str | None = None,
    ) -> PlayerAchievement:
        player = await self.db.get(Player, player_id)
        if player is None:
            raise ValueError("玩家不存在")

        definition = await self.db.get(AchievementDefinition, achievement_key)
        if definition is None:
            raise ValueError("成就不存在")
        if not definition.is_active:
            raise ValueError("成就未激活，无法解锁")

        existing = await self.get_player_achievement(player_id, achievement_key)
        if existing is not None:
            return existing

        achievement = PlayerAchievement(
            player_achievement_id=uuid.uuid4(),
            player_id=player_id,
            achievement_key=achievement_key,
            source=source,
            source_id=source_id,
        )
        self.db.add(achievement)
        await self.db.flush()
        return achievement

    async def claim_reward(
        self, player_id: uuid.UUID, achievement_key: str
    ) -> PlayerAchievement:
        achievement = await self.get_player_achievement(player_id, achievement_key)
        if achievement is None:
            raise ValueError("玩家未解锁该成就")
        if achievement.reward_claimed:
            raise ValueError("成就奖励已领取")

        achievement.reward_claimed = True
        achievement.claimed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return achievement
