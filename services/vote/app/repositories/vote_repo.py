import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

    async def create_vote_cycle(
        self,
        chapter_id: str,
        starts_at: datetime,
        ends_at: datetime,
        created_by: str,
        created_reason: str,
        candidates_data: list[dict],
    ) -> VoteCycle:
        cycle_id = uuid.uuid4()
        cycle = VoteCycle(
            vote_cycle_id=cycle_id,
            chapter_id=chapter_id,
            status="draft",
            starts_at=starts_at,
            ends_at=ends_at,
            created_by=created_by,
            created_reason=created_reason,
        )
        for c_data in candidates_data:
            candidate = VoteCandidate(
                candidate_id=uuid.uuid4(),
                vote_cycle_id=cycle_id,
                title=c_data["title"],
                summary=c_data["summary"],
                description=c_data.get("description"),
                region_scope=c_data.get("region_scope", []),
                risk_tags=c_data.get("risk_tags", []),
                status="active",
            )
            self.db.add(candidate)
        self.db.add(cycle)
        await self.db.flush()

        stmt = (
            select(VoteCycle)
            .options(selectinload(VoteCycle.candidates))
            .where(VoteCycle.vote_cycle_id == cycle_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def open_vote_cycle(self, vote_cycle_id: uuid.UUID) -> VoteCycle | None:
        stmt = select(VoteCycle).where(VoteCycle.vote_cycle_id == vote_cycle_id)
        result = await self.db.execute(stmt)
        cycle = result.scalar_one_or_none()
        if cycle is None:
            return None
        cycle.status = "open"
        await self.db.flush()
        return cycle

    async def get_vote_history(
        self, player_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[tuple[Vote, VoteCandidate]], int]:
        from sqlalchemy import func as sa_func

        count_stmt = select(sa_func.count(Vote.vote_id)).where(Vote.player_id == player_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(Vote, VoteCandidate)
            .join(VoteCandidate, Vote.candidate_id == VoteCandidate.candidate_id)
            .where(Vote.player_id == player_id)
            .order_by(Vote.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        rows = result.all()
        return rows, total
