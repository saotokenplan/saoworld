import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import Vote, VoteCandidate, VoteCycle

# 合法的状态迁移路径
VALID_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"scheduled"},
    "scheduled": {"open"},
    "open": {"closed"},
    "closed": {"finalized", "open"},
}


class VoteRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- 读取方法 ---

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

    async def get_all_candidates_for_cycle(self, vote_cycle_id: uuid.UUID) -> Sequence[VoteCandidate]:
        stmt: Select[tuple[VoteCandidate]] = (
            select(VoteCandidate)
            .where(VoteCandidate.vote_cycle_id == vote_cycle_id)
            .order_by(VoteCandidate.created_at)
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

    async def get_cycle_by_id(self, vote_cycle_id: uuid.UUID) -> VoteCycle | None:
        stmt: Select[tuple[VoteCycle]] = (
            select(VoteCycle)
            .options(selectinload(VoteCycle.candidates))
            .where(VoteCycle.vote_cycle_id == vote_cycle_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_open_cycle_for_chapter(self, chapter_id: str) -> VoteCycle | None:
        stmt: Select[tuple[VoteCycle]] = (
            select(VoteCycle)
            .where(VoteCycle.chapter_id == chapter_id)
            .where(VoteCycle.status == "open")
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # --- 写入方法 ---

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
        candidates_data: list[dict[str, Any]],
    ) -> VoteCycle:
        cycle_id = uuid.uuid4()
        candidates = [
            VoteCandidate(
                candidate_id=uuid.uuid4(),
                vote_cycle_id=cycle_id,
                title=c["title"],
                summary=c["summary"],
                description=c.get("description"),
                region_scope=c.get("region_scope", []),
                risk_tags=c.get("risk_tags", []),
                generated_params=c.get("generated_params"),
                status="active",
            )
            for c in candidates_data
        ]
        cycle = VoteCycle(
            vote_cycle_id=cycle_id,
            chapter_id=chapter_id,
            status="draft",
            starts_at=starts_at,
            ends_at=ends_at,
            created_by=created_by,
            created_reason=created_reason,
            candidates=candidates,
        )
        self.db.add(cycle)
        await self.db.flush()
        return cycle

    async def transition_cycle_status(
        self, vote_cycle_id: uuid.UUID, new_status: str
    ) -> VoteCycle | None:
        stmt: Select[tuple[VoteCycle]] = (
            select(VoteCycle)
            .options(selectinload(VoteCycle.candidates))
            .where(VoteCycle.vote_cycle_id == vote_cycle_id)
        )
        result = await self.db.execute(stmt)
        cycle = result.scalar_one_or_none()
        if cycle is None:
            return None
        cycle.status = new_status
        await self.db.flush()
        return cycle

    async def tally_votes(self, vote_cycle_id: uuid.UUID) -> dict[str, Any]:
        """计票：统计每个候选项的得票数和加权总分，更新 vote_count 并返回获胜者。"""
        # 统计每个候选项的得票数和加权总分
        stmt = (
            select(
                Vote.candidate_id,
                sa_func.count(Vote.vote_id).label("count"),
                sa_func.sum(Vote.weight).label("total_weight"),
            )
            .where(Vote.vote_cycle_id == vote_cycle_id)
            .group_by(Vote.candidate_id)
        )
        result = await self.db.execute(stmt)
        tally_rows = result.all()

        tally_map: dict[uuid.UUID, dict[str, Any]] = {}
        for row in tally_rows:
            tally_map[row.candidate_id] = {
                "count": row.count,
                "total_weight": float(row.total_weight) if row.total_weight else 0.0,
            }

        # 更新每个候选项的 vote_count
        all_candidates = await self.get_all_candidates_for_cycle(vote_cycle_id)
        winning_candidate_id: uuid.UUID | None = None
        max_weighted_score = -1.0

        for candidate in all_candidates:
            tally = tally_map.get(candidate.candidate_id, {"count": 0, "total_weight": 0.0})
            candidate.vote_count = tally["count"]
            if tally["total_weight"] > max_weighted_score and candidate.status == "active" and tally["count"] > 0:
                max_weighted_score = tally["total_weight"]
                winning_candidate_id = candidate.candidate_id

        # 标记获胜候选项为 selected（仅在有投票时）
        if winning_candidate_id is not None:
            winner = next(
                (c for c in all_candidates if c.candidate_id == winning_candidate_id), None
            )
            if winner:
                winner.status = "selected"

        await self.db.flush()

        return {
            "winning_candidate_id": winning_candidate_id,
            "tally": tally_map,
        }

    async def withdraw_candidate(self, candidate_id: uuid.UUID) -> VoteCandidate | None:
        stmt: Select[tuple[VoteCandidate]] = select(VoteCandidate).where(
            VoteCandidate.candidate_id == candidate_id
        )
        result = await self.db.execute(stmt)
        candidate = result.scalar_one_or_none()
        if candidate is None:
            return None
        candidate.status = "withdrawn"
        await self.db.flush()
        return candidate

    async def get_vote_history(
        self, player_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[tuple[Vote, VoteCandidate]], int]:
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

    @staticmethod
    def is_valid_transition(current_status: str, new_status: str) -> bool:
        allowed = VALID_TRANSITIONS.get(current_status, set())
        return new_status in allowed
