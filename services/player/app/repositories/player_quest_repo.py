import uuid
from typing import Any, Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import PlayerQuest


class PlayerQuestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_player_quests(
        self, player_id: uuid.UUID, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[PlayerQuest], int]:
        count_stmt = select(sa_func.count(PlayerQuest.player_quest_id)).where(
            PlayerQuest.player_id == player_id
        )
        if status is not None:
            count_stmt = count_stmt.where(PlayerQuest.status == status)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[PlayerQuest]] = select(PlayerQuest).where(
            PlayerQuest.player_id == player_id
        )
        if status is not None:
            stmt = stmt.where(PlayerQuest.status == status)
        stmt = stmt.order_by(PlayerQuest.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def get_player_quest(self, player_id: uuid.UUID, quest_id: str) -> PlayerQuest | None:
        stmt: Select[tuple[PlayerQuest]] = select(PlayerQuest).where(
            PlayerQuest.player_id == player_id,
            PlayerQuest.quest_id == quest_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_player_quest(
        self,
        player_id: uuid.UUID,
        quest_id: str,
        status: str = "available",
        objectives_jsonb: dict[str, Any] | None = None,
        rewards_jsonb: dict[str, Any] | None = None,
    ) -> PlayerQuest:
        player_quest = PlayerQuest(
            player_quest_id=uuid.uuid4(),
            player_id=player_id,
            quest_id=quest_id,
            status=status,
            objectives_jsonb=objectives_jsonb,
            rewards_jsonb=rewards_jsonb,
        )
        self.db.add(player_quest)
        await self.db.flush()
        return player_quest

    async def update_player_quest_status(
        self, player_quest_id: uuid.UUID, status: str
    ) -> PlayerQuest | None:
        stmt: Select[tuple[PlayerQuest]] = select(PlayerQuest).where(
            PlayerQuest.player_quest_id == player_quest_id
        )
        result = await self.db.execute(stmt)
        player_quest = result.scalar_one_or_none()
        if player_quest is None:
            return None

        player_quest.status = status
        await self.db.flush()
        return player_quest