"""赛季奖励发放仓储层。"""

import uuid
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import SeasonRewardGrant


class SeasonRewardRepository:
    """赛季奖励发放记录仓储层（append-only 风格，支持幂等）。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_grant(
        self,
        season_id: uuid.UUID,
        player_id: uuid.UUID,
        final_rank: int,
        final_tier: str,
        final_division: int,
        final_rating_points: int,
        reward_payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        trace_id: str | None = None,
        status: str = "granted",
    ) -> SeasonRewardGrant:
        """创建一条奖励发放记录。

        默认 status 为 granted（同步发放场景）；异步发放可传 status=pending，
        后续通过 update_grant_status 标记为 granted。
        """
        grant = SeasonRewardGrant(
            grant_id=uuid.uuid4(),
            season_id=season_id,
            player_id=player_id,
            final_rank=final_rank,
            final_tier=final_tier,
            final_division=final_division,
            final_rating_points=final_rating_points,
            reward_payload_jsonb=reward_payload,
            status=status,
            granted_at=datetime.now() if status == "granted" else None,
            idempotency_key=idempotency_key or f"sr_{season_id}_{player_id}",
            trace_id=trace_id,
        )
        self.db.add(grant)
        await self.db.flush()
        return grant

    async def get_grant_by_id(
        self, grant_id: uuid.UUID
    ) -> SeasonRewardGrant | None:
        result = await self.db.execute(
            select(SeasonRewardGrant).where(
                SeasonRewardGrant.grant_id == grant_id
            )
        )
        return result.scalar_one_or_none()

    async def get_grant_by_season_player(
        self, season_id: uuid.UUID, player_id: uuid.UUID
    ) -> SeasonRewardGrant | None:
        result = await self.db.execute(
            select(SeasonRewardGrant).where(
                and_(
                    SeasonRewardGrant.season_id == season_id,
                    SeasonRewardGrant.player_id == player_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_grant_by_idempotency_key(
        self, idempotency_key: str
    ) -> SeasonRewardGrant | None:
        result = await self.db.execute(
            select(SeasonRewardGrant).where(
                SeasonRewardGrant.idempotency_key == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    async def list_grants_by_season(
        self,
        season_id: uuid.UUID,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[SeasonRewardGrant], int]:
        query = select(SeasonRewardGrant).where(
            SeasonRewardGrant.season_id == season_id
        )
        count_query = select(func.count()).select_from(SeasonRewardGrant).where(
            SeasonRewardGrant.season_id == season_id
        )

        if status:
            query = query.where(SeasonRewardGrant.status == status)
            count_query = count_query.where(SeasonRewardGrant.status == status)

        query = (
            query.order_by(SeasonRewardGrant.final_rank.asc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one() or 0
        return result.scalars().all(), total

    async def list_grants_by_player(
        self,
        player_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[SeasonRewardGrant], int]:
        query = (
            select(SeasonRewardGrant)
            .where(SeasonRewardGrant.player_id == player_id)
            .order_by(SeasonRewardGrant.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        count_query = select(func.count()).select_from(SeasonRewardGrant).where(
            SeasonRewardGrant.player_id == player_id
        )

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one() or 0
        return result.scalars().all(), total

    async def update_grant_status(
        self,
        grant_id: uuid.UUID,
        status: str,
        granted_at: datetime | None = None,
    ) -> SeasonRewardGrant | None:
        grant = await self.get_grant_by_id(grant_id)
        if grant is None:
            return None
        grant.status = status
        if status == "granted":
            grant.granted_at = granted_at or datetime.now()
        grant.updated_at = datetime.now()
        await self.db.flush()
        return grant

    async def count_grants_by_season(
        self, season_id: uuid.UUID
    ) -> int:
        query = select(func.count()).select_from(SeasonRewardGrant).where(
            SeasonRewardGrant.season_id == season_id
        )
        result = await self.db.scalar(query)
        return int(result or 0)
