import uuid
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Player


class PlayerRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_player_by_id(self, player_id: uuid.UUID) -> Player | None:
        stmt: Select[tuple[Player]] = select(Player).where(Player.player_id == player_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_player(self, display_name: str, chapter_id: str | None = None) -> Player:
        player = Player(
            player_id=uuid.uuid4(),
            display_name=display_name,
            chapter_id=chapter_id,
        )
        self.db.add(player)
        await self.db.flush()
        return player

    async def update_player(
        self,
        player_id: uuid.UUID,
        display_name: str | None = None,
        chapter_id: str | None = None,
    ) -> Player | None:
        from datetime import datetime, timezone

        stmt: Select[tuple[Player]] = select(Player).where(Player.player_id == player_id)
        result = await self.db.execute(stmt)
        player = result.scalar_one_or_none()
        if player is None:
            return None

        if display_name is not None:
            player.display_name = display_name
        if chapter_id is not None:
            player.chapter_id = chapter_id
        player.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return player

    async def list_players(self, limit: int = 20, offset: int = 0) -> tuple[Sequence[Player], int]:
        count_stmt = select(sa_func.count(Player.player_id))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(Player)
            .order_by(Player.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def add_experience(
        self,
        player_id: uuid.UUID,
        amount: int,
    ) -> tuple[Player, list[int]]:
        from datetime import datetime, timezone
        from app.schemas.player import (
            get_level_from_experience,
            MAX_PLAYER_LEVEL,
            calculate_level_up_rewards,
        )
        from app.repositories.contribution_repo import ContributionRepository

        stmt: Select[tuple[Player]] = select(Player).where(Player.player_id == player_id)
        result = await self.db.execute(stmt)
        player = result.scalar_one_or_none()
        if player is None:
            raise ValueError("Player not found")

        old_level = player.level
        old_exp = player.experience_points or 0
        new_exp = old_exp + amount

        player.experience_points = new_exp
        new_level = get_level_from_experience(new_exp)
        new_level = min(new_level, MAX_PLAYER_LEVEL)

        levels_gained: list[int] = []
        if new_level > old_level:
            player.level = new_level
            contribution_repo = ContributionRepository(self.db)
            for level in range(old_level + 1, new_level + 1):
                levels_gained.append(level)
                rewards = calculate_level_up_rewards(level)
                if rewards.get("contribution_points", 0) > 0:
                    await contribution_repo.add_contribution(
                        player_id=player_id,
                        amount=rewards["contribution_points"],
                        source="system",
                        source_id=f"level_up_{level}",
                        description=f"升级到 {level} 级奖励",
                    )

        player.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return player, levels_gained

    async def grant_rewards(
        self,
        player_id: uuid.UUID,
        rewards_jsonb: dict | None,
    ) -> Player | None:
        from datetime import datetime, timezone

        stmt: Select[tuple[Player]] = select(Player).where(Player.player_id == player_id)
        result = await self.db.execute(stmt)
        player = result.scalar_one_or_none()
        if player is None:
            return None

        if rewards_jsonb is None:
            return player

        progress = player.progress_jsonb or {}
        resources = progress.get("resources", {})
        stats = progress.get("stats", {})

        gold = rewards_jsonb.get("gold", 0)
        experience = rewards_jsonb.get("experience", 0)
        reputation = rewards_jsonb.get("reputation", {})

        if gold > 0:
            resources["gold"] = resources.get("gold", 0) + gold
        if experience > 0:
            stats["experience"] = stats.get("experience", 0) + experience
        if isinstance(reputation, dict):
            current_rep = progress.get("reputation_snapshot", {})
            for faction, amount in reputation.items():
                current_rep[faction] = current_rep.get(faction, 0) + amount
            player.reputation_snapshot = current_rep

        progress["resources"] = resources
        progress["stats"] = stats
        player.progress_jsonb = progress
        player.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return player
