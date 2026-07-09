import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import PlayerRegion


class PlayerRegionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_player_regions(
        self, player_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[PlayerRegion], int]:
        count_stmt = select(sa_func.count(PlayerRegion.player_region_id)).where(
            PlayerRegion.player_id == player_id
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[PlayerRegion]] = (
            select(PlayerRegion)
            .where(PlayerRegion.player_id == player_id)
            .order_by(PlayerRegion.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def unlock_region(self, player_id: uuid.UUID, region_id: str) -> PlayerRegion:
        existing_stmt: Select[tuple[PlayerRegion]] = select(PlayerRegion).where(
            PlayerRegion.player_id == player_id,
            PlayerRegion.region_id == region_id,
        )
        result = await self.db.execute(existing_stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.unlocked_at = datetime.now(timezone.utc)
            await self.db.flush()
            return existing

        player_region = PlayerRegion(
            player_region_id=uuid.uuid4(),
            player_id=player_id,
            region_id=region_id,
            unlocked_at=datetime.now(timezone.utc),
            reputation=0,
        )
        self.db.add(player_region)
        await self.db.flush()
        return player_region

    async def update_region_reputation(
        self, player_id: uuid.UUID, region_id: str, reputation: int
    ) -> PlayerRegion | None:
        stmt: Select[tuple[PlayerRegion]] = select(PlayerRegion).where(
            PlayerRegion.player_id == player_id,
            PlayerRegion.region_id == region_id,
        )
        result = await self.db.execute(stmt)
        player_region = result.scalar_one_or_none()
        if player_region is None:
            return None

        player_region.reputation = reputation
        await self.db.flush()
        return player_region

    async def add_reputation(
        self, player_id: uuid.UUID, region_id: str, amount: int
    ) -> PlayerRegion:
        stmt: Select[tuple[PlayerRegion]] = select(PlayerRegion).where(
            PlayerRegion.player_id == player_id,
            PlayerRegion.region_id == region_id,
        )
        result = await self.db.execute(stmt)
        player_region = result.scalar_one_or_none()

        if player_region is None:
            player_region = PlayerRegion(
                player_region_id=uuid.uuid4(),
                player_id=player_id,
                region_id=region_id,
                reputation=amount,
            )
            self.db.add(player_region)
        else:
            player_region.reputation = player_region.reputation + amount

        await self.db.flush()
        return player_region

    async def get_region_reputation(
        self, player_id: uuid.UUID, region_id: str
    ) -> PlayerRegion | None:
        stmt: Select[tuple[PlayerRegion]] = select(PlayerRegion).where(
            PlayerRegion.player_id == player_id,
            PlayerRegion.region_id == region_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()