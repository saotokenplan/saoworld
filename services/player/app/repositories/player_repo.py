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