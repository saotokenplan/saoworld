"""公会任务仓储层。"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Sequence

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import GuildQuest, GuildQuestProgress


class GuildQuestRepository:
    """公会任务仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_quest(
        self,
        guild_id: uuid.UUID,
        quest_key: str,
        name: str,
        description: str,
        quest_type: str,
        objectives_jsonb: dict | None = None,
        rewards_jsonb: dict | None = None,
        progress_target: int = 100,
        time_limit_minutes: int = 1440,
        created_by: uuid.UUID = uuid.UUID(int=0),
    ) -> GuildQuest:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=time_limit_minutes)

        quest = GuildQuest(
            guild_quest_id=uuid.uuid4(),
            guild_id=guild_id,
            quest_key=quest_key,
            name=name,
            description=description,
            quest_type=quest_type,
            status="active",
            objectives_jsonb=objectives_jsonb,
            rewards_jsonb=rewards_jsonb,
            progress_target=progress_target,
            current_progress=0,
            time_limit_minutes=time_limit_minutes,
            expires_at=expires_at,
            created_by=created_by,
            schema_version=1,
        )
        self.db.add(quest)
        await self.db.flush()
        return quest

    async def get_quest_by_id(self, guild_quest_id: uuid.UUID) -> GuildQuest | None:
        stmt = select(GuildQuest).where(GuildQuest.guild_quest_id == guild_quest_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_quest_by_key(self, guild_id: uuid.UUID, quest_key: str) -> GuildQuest | None:
        stmt = select(GuildQuest).where(
            and_(GuildQuest.guild_id == guild_id, GuildQuest.quest_key == quest_key)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_guild_quests(
        self, guild_id: uuid.UUID, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[GuildQuest], int]:
        base_filter = GuildQuest.guild_id == guild_id
        if status is not None:
            base_filter = and_(base_filter, GuildQuest.status == status)

        count_stmt = select(func.count(GuildQuest.guild_quest_id)).where(base_filter)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            select(GuildQuest)
            .where(base_filter)
            .order_by(GuildQuest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        quests = result.scalars().all()

        return quests, total

    async def update_progress(self, guild_quest_id: uuid.UUID, contribution: int) -> GuildQuest | None:
        quest = await self.get_quest_by_id(guild_quest_id)
        if quest is None or quest.status != "active":
            return None

        quest.current_progress = min(quest.progress_target, quest.current_progress + contribution)

        if quest.current_progress >= quest.progress_target:
            quest.status = "completed"

        await self.db.flush()
        return quest

    async def complete_quest(self, guild_quest_id: uuid.UUID) -> GuildQuest | None:
        quest = await self.get_quest_by_id(guild_quest_id)
        if quest is None:
            return None

        quest.status = "completed"
        quest.current_progress = quest.progress_target
        await self.db.flush()
        return quest

    async def expire_quest(self, guild_quest_id: uuid.UUID) -> GuildQuest | None:
        quest = await self.get_quest_by_id(guild_quest_id)
        if quest is None:
            return None

        if quest.status == "active":
            quest.status = "expired"
            await self.db.flush()
        return quest

    async def delete_quest(self, guild_quest_id: uuid.UUID) -> bool:
        quest = await self.get_quest_by_id(guild_quest_id)
        if quest is None:
            return False

        await self.db.delete(quest)
        await self.db.flush()
        return True

    async def update_quest(
        self,
        guild_quest_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        objectives_jsonb: dict | None = None,
        rewards_jsonb: dict | None = None,
        status: str | None = None,
    ) -> GuildQuest | None:
        quest = await self.get_quest_by_id(guild_quest_id)
        if quest is None:
            return None

        if name is not None:
            quest.name = name
        if description is not None:
            quest.description = description
        if objectives_jsonb is not None:
            quest.objectives_jsonb = objectives_jsonb
        if rewards_jsonb is not None:
            quest.rewards_jsonb = rewards_jsonb
        if status is not None:
            quest.status = status

        await self.db.flush()
        return quest


class GuildQuestProgressRepository:
    """公会任务进度仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record_contribution(
        self, guild_quest_id: uuid.UUID, player_id: uuid.UUID, contribution: int
    ) -> GuildQuestProgress:
        stmt = select(GuildQuestProgress).where(
            and_(
                GuildQuestProgress.guild_quest_id == guild_quest_id,
                GuildQuestProgress.player_id == player_id,
            )
        )
        result = await self.db.execute(stmt)
        progress = result.scalar_one_or_none()

        if progress is None:
            progress = GuildQuestProgress(
                progress_id=uuid.uuid4(),
                guild_quest_id=guild_quest_id,
                player_id=player_id,
                contribution=contribution,
            )
            self.db.add(progress)
        else:
            progress.contribution += contribution

        await self.db.flush()
        return progress

    async def get_progress(self, guild_quest_id: uuid.UUID, player_id: uuid.UUID) -> GuildQuestProgress | None:
        stmt = select(GuildQuestProgress).where(
            and_(
                GuildQuestProgress.guild_quest_id == guild_quest_id,
                GuildQuestProgress.player_id == player_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_quest_progress_list(
        self, guild_quest_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[GuildQuestProgress], int]:
        count_stmt = select(func.count(GuildQuestProgress.progress_id)).where(
            GuildQuestProgress.guild_quest_id == guild_quest_id
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            select(GuildQuestProgress)
            .where(GuildQuestProgress.guild_quest_id == guild_quest_id)
            .order_by(GuildQuestProgress.contribution.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        progress_list = result.scalars().all()

        return progress_list, total

    async def claim_reward(self, guild_quest_id: uuid.UUID, player_id: uuid.UUID) -> GuildQuestProgress | None:
        progress = await self.get_progress(guild_quest_id, player_id)
        if progress is None or progress.claimed_reward:
            return None

        progress.claimed_reward = True
        progress.claimed_at = datetime.now(timezone.utc)
        await self.db.flush()
        return progress

    async def get_player_contributions(self, player_id: uuid.UUID) -> Sequence[GuildQuestProgress]:
        stmt = select(GuildQuestProgress).where(GuildQuestProgress.player_id == player_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()