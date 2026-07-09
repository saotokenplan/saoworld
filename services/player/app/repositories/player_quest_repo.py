import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import PlayerQuest

VALID_TRANSITIONS: dict[str, set[str]] = {
    "available": {"active"},
    "active": {"completed", "failed"},
    "completed": set(),
    "failed": set(),
}


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

    async def get_player_quest_by_id(self, player_quest_id: uuid.UUID) -> PlayerQuest | None:
        stmt: Select[tuple[PlayerQuest]] = select(PlayerQuest).where(
            PlayerQuest.player_quest_id == player_quest_id
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

    def is_valid_transition(self, current_status: str, new_status: str) -> bool:
        allowed = VALID_TRANSITIONS.get(current_status, set())
        return new_status in allowed

    async def accept_quest(
        self, player_id: uuid.UUID, quest_id: str
    ) -> PlayerQuest | None:
        player_quest = await self.get_player_quest(player_id, quest_id)
        if player_quest is None:
            return None

        if player_quest.status != "available":
            return player_quest

        player_quest.status = "active"
        player_quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return player_quest

    async def update_objectives(
        self,
        player_id: uuid.UUID,
        quest_id: str,
        objectives_update: dict[str, Any],
    ) -> PlayerQuest | None:
        player_quest = await self.get_player_quest(player_id, quest_id)
        if player_quest is None:
            return None

        current_objectives = player_quest.objectives_jsonb or {}
        current_objectives.update(objectives_update)
        player_quest.objectives_jsonb = current_objectives
        player_quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return player_quest

    def all_objectives_completed(self, objectives_jsonb: dict[str, Any] | None) -> bool:
        if objectives_jsonb is None:
            return True
        objectives = objectives_jsonb.get("objectives", [])
        if not isinstance(objectives, list):
            return True
        for obj in objectives:
            if isinstance(obj, dict) and obj.get("completed") is not True:
                return False
        return True

    async def complete_quest(
        self, player_id: uuid.UUID, quest_id: str, check_objectives: bool = True
    ) -> PlayerQuest | None:
        player_quest = await self.get_player_quest(player_id, quest_id)
        if player_quest is None:
            return None

        if player_quest.status != "active":
            return player_quest

        if check_objectives and not self.all_objectives_completed(player_quest.objectives_jsonb):
            return None

        player_quest.status = "completed"
        player_quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return player_quest

    async def fail_quest(
        self, player_id: uuid.UUID, quest_id: str
    ) -> PlayerQuest | None:
        player_quest = await self.get_player_quest(player_id, quest_id)
        if player_quest is None:
            return None

        if player_quest.status != "active":
            return player_quest

        player_quest.status = "failed"
        player_quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return player_quest

    async def update_status(
        self, player_id: uuid.UUID, quest_id: str, new_status: str
    ) -> PlayerQuest | None:
        player_quest = await self.get_player_quest(player_id, quest_id)
        if player_quest is None:
            return None

        if not self.is_valid_transition(player_quest.status, new_status):
            return None

        player_quest.status = new_status
        player_quest.updated_at = datetime.now(timezone.utc)
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
        player_quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return player_quest