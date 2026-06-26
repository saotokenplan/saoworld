import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Vote, VoteCandidate, VoteCycle


class VoteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_current_open_cycle(self) -> VoteCycle | None:
        now = datetime.now(timezone.utc)
        stmt: Select[tuple[VoteCycle]] = (
            select(VoteCycle)
            .where(VoteCycle.status == "open")
            .where(VoteCycle.starts_at <= now)
            .where(VoteCycle.ends_at > now)
            .order_by(VoteCycle.starts_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_candidates_for_cycle(self, vote_cycle_id: uuid.UUID) -> Sequence[VoteCandidate]:
        stmt: Select[tuple[VoteCandidate]] = (
            select(VoteCandidate)
            .where(VoteCandidate.vote_cycle_id == vote_cycle_id)
            .where(VoteCandidate.status == "active")
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_candidate_by_id(self, candidate_id: uuid.UUID) -> VoteCandidate | None:
        stmt: Select[tuple[VoteCandidate]] = select(VoteCandidate).where(
            VoteCandidate.candidate_id == candidate_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_player_voted(self, vote_cycle_id: uuid.UUID, player_id: uuid.UUID) -> Vote | None:
        stmt: Select[tuple[Vote]] = select(Vote).where(
            Vote.vote_cycle_id == vote_cycle_id, Vote.player_id == player_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def vote_exists_by_idempotency_key(self, idempotency_key: str) -> Vote | None:
        stmt: Select[tuple[Vote]] = select(Vote).where(Vote.idempotency_key == idempotency_key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_vote(
        self,
        vote_cycle_id: uuid.UUID,
        player_id: uuid.UUID,
        candidate_id: uuid.UUID,
        weight: float,
        device_fingerprint_hash: str,
        idempotency_key: str,
    ) -> Vote:
        vote = Vote(
            vote_cycle_id=vote_cycle_id,
            player_id=player_id,
            candidate_id=candidate_id,
            weight=weight,
            device_fingerprint_hash=device_fingerprint_hash,
            idempotency_key=idempotency_key,
        )
        self.db.add(vote)
        await self.db.flush()
        return vote
