import uuid
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Player, PlayerContribution


class ContributionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_player_contribution(self, player_id: uuid.UUID) -> int:
        stmt: Select[tuple[int]] = select(Player.contribution_points).where(
            Player.player_id == player_id
        )
        result = await self.db.execute(stmt)
        points = result.scalar_one_or_none()
        return points if points is not None else 0

    async def add_contribution(
        self,
        player_id: uuid.UUID,
        amount: int,
        source: str,
        source_id: str | None = None,
        description: str | None = None,
    ) -> PlayerContribution:
        if amount <= 0:
            raise ValueError("贡献度增量必须大于 0")

        player = await self.db.get(Player, player_id)
        if player is None:
            raise ValueError("玩家不存在")

        player.contribution_points = (player.contribution_points or 0) + amount
        player.contribution_points = max(0, player.contribution_points)

        contribution = PlayerContribution(
            contribution_id=uuid.uuid4(),
            player_id=player_id,
            amount=amount,
            source=source,
            source_id=source_id,
            description=description,
        )
        self.db.add(contribution)
        await self.db.flush()
        return contribution

    async def list_contributions(
        self,
        player_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[PlayerContribution], int]:
        count_stmt = select(sa_func.count(PlayerContribution.contribution_id)).where(
            PlayerContribution.player_id == player_id
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[PlayerContribution]] = (
            select(PlayerContribution)
            .where(PlayerContribution.player_id == player_id)
            .order_by(PlayerContribution.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total
