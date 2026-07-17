"""匹配系统仓储层。"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Sequence

from sqlalchemy import and_, or_, select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import (
    MatchSeason,
    PlayerRating,
    MatchQueue,
    MatchRoom,
    MatchResult,
)


TIER_ORDER = ["bronze", "silver", "gold", "platinum", "diamond", "master", "challenger"]
TIER_POINTS_BASE = [0, 100, 200, 300, 400, 500, 600]
DEFAULT_MATCH_TIMEOUT_SECONDS = 120
DEFAULT_TIER_RANGE = 1
DEFAULT_LEVEL_RANGE = 10


def tier_to_index(tier: str) -> int:
    try:
        return TIER_ORDER.index(tier)
    except ValueError:
        return 0


def index_to_tier(index: int) -> str:
    if index < 0:
        return TIER_ORDER[0]
    if index >= len(TIER_ORDER):
        return TIER_ORDER[-1]
    return TIER_ORDER[index]


def _tier_order_case() -> case:
    """构造 tier -> int 的 CASE 表达式，用于正确排序段位。"""
    whens = [(PlayerRating.tier == t, i) for i, t in enumerate(TIER_ORDER)]
    return case(*whens, else_=-1)


class MatchSeasonRepository:
    """匹配赛季仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_season(
        self,
        season_key: str,
        season_name: str,
        start_at: datetime,
        end_at: datetime,
        description: str | None = None,
        reward_config: dict | None = None,
    ) -> MatchSeason:
        season = MatchSeason(
            season_id=uuid.uuid4(),
            season_key=season_key,
            season_name=season_name,
            status="upcoming",
            start_at=start_at,
            end_at=end_at,
            description=description,
            reward_jsonb=reward_config,
        )
        self.db.add(season)
        await self.db.flush()
        return season

    async def get_season(self, season_id: uuid.UUID) -> MatchSeason | None:
        result = await self.db.execute(
            select(MatchSeason).where(MatchSeason.season_id == season_id)
        )
        return result.scalar_one_or_none()

    async def get_season_by_key(self, season_key: str) -> MatchSeason | None:
        result = await self.db.execute(
            select(MatchSeason).where(MatchSeason.season_key == season_key)
        )
        return result.scalar_one_or_none()

    async def get_current_season(self) -> MatchSeason | None:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(MatchSeason)
            .where(
                and_(
                    MatchSeason.status == "active",
                    MatchSeason.start_at <= now,
                    MatchSeason.end_at >= now,
                )
            )
            .order_by(MatchSeason.start_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_seasons(
        self,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[MatchSeason], int]:
        query = select(MatchSeason)
        count_query = select(func.count()).select_from(MatchSeason)

        if status:
            query = query.where(MatchSeason.status == status)
            count_query = count_query.where(MatchSeason.status == status)

        query = query.order_by(MatchSeason.start_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one() or 0

        return result.scalars().all(), total

    async def update_season_status(
        self, season_id: uuid.UUID, status: str
    ) -> MatchSeason | None:
        season = await self.get_season(season_id)
        if season is None:
            return None
        season.status = status
        season.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return season

    async def get_settlement_status(
        self, season_id: uuid.UUID
    ) -> str | None:
        season = await self.get_season(season_id)
        if season is None:
            return None
        return season.settlement_status

    async def update_settlement_status(
        self,
        season_id: uuid.UUID,
        settlement_status: str,
        settled_at: datetime | None = None,
    ) -> MatchSeason | None:
        season = await self.get_season(season_id)
        if season is None:
            return None
        season.settlement_status = settlement_status
        if settled_at is not None:
            season.settled_at = settled_at
        elif settlement_status == "settled":
            season.settled_at = datetime.now(timezone.utc)
        season.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return season


class PlayerRatingRepository:
    """玩家段位仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_player_rating(
        self, player_id: uuid.UUID, season_id: uuid.UUID
    ) -> PlayerRating | None:
        result = await self.db.execute(
            select(PlayerRating).where(
                and_(
                    PlayerRating.player_id == player_id,
                    PlayerRating.season_id == season_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_or_create_rating(
        self, player_id: uuid.UUID, season_id: uuid.UUID
    ) -> PlayerRating:
        rating = await self.get_player_rating(player_id, season_id)
        if rating is not None:
            return rating

        rating = PlayerRating(
            rating_id=uuid.uuid4(),
            player_id=player_id,
            season_id=season_id,
            tier="bronze",
            division=5,
            rating_points=0,
            wins=0,
            losses=0,
            draws=0,
            win_streak=0,
            best_tier="bronze",
            best_division=5,
        )
        self.db.add(rating)
        await self.db.flush()
        return rating

    async def update_rating_after_match(
        self,
        player_id: uuid.UUID,
        season_id: uuid.UUID,
        is_winner: bool,
        is_draw: bool = False,
        rating_change: int = 0,
    ) -> PlayerRating | None:
        rating = await self.get_or_create_rating(player_id, season_id)

        if is_draw:
            rating.draws += 1
            rating.win_streak = 0
        elif is_winner:
            rating.wins += 1
            rating.win_streak += 1
            new_points = rating.rating_points + abs(rating_change)
            while new_points >= 100 and rating.division > 1:
                new_points -= 100
                rating.division -= 1
            if new_points >= 100 and rating.division == 1:
                current_tier_idx = tier_to_index(rating.tier)
                if current_tier_idx < len(TIER_ORDER) - 1:
                    rating.tier = index_to_tier(current_tier_idx + 1)
                    rating.division = 5
                    new_points -= 100
            rating.rating_points = min(new_points, 99)
        else:
            rating.losses += 1
            rating.win_streak = 0
            new_points = rating.rating_points - abs(rating_change)
            while new_points < 0 and rating.division < 5:
                new_points += 100
                rating.division += 1
            if new_points < 0 and rating.division == 5:
                current_tier_idx = tier_to_index(rating.tier)
                if current_tier_idx > 0:
                    rating.tier = index_to_tier(current_tier_idx - 1)
                    rating.division = 1
                    new_points = 99 + new_points
                else:
                    new_points = 0
            rating.rating_points = max(new_points, 0)

        new_tier_idx = tier_to_index(rating.tier)
        new_total = new_tier_idx * 500 + (5 - rating.division) * 100 + rating.rating_points
        best_total = tier_to_index(rating.best_tier) * 500 + (5 - rating.best_division) * 100
        if new_total > best_total:
            rating.best_tier = rating.tier
            rating.best_division = rating.division

        rating.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return rating

    async def get_leaderboard(
        self,
        season_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[Sequence[PlayerRating], int]:
        count_query = select(func.count()).select_from(
            select(PlayerRating).where(PlayerRating.season_id == season_id).subquery()
        )

        tier_order = _tier_order_case()
        query = (
            select(PlayerRating)
            .where(PlayerRating.season_id == season_id)
            .order_by(
                desc(tier_order),
                PlayerRating.division,
                desc(PlayerRating.rating_points),
                desc(PlayerRating.wins),
            )
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one() or 0

        return result.scalars().all(), total

    async def get_player_rank(
        self, player_id: uuid.UUID, season_id: uuid.UUID
    ) -> int | None:
        """查询玩家在指定赛季的排名，无段位记录返回 None。"""
        rating = await self.get_player_rating(player_id, season_id)
        if rating is None:
            return None

        target_tier_idx = tier_to_index(rating.tier)
        tier_order = _tier_order_case()
        better_query = select(func.count()).where(
            and_(
                PlayerRating.season_id == season_id,
                or_(
                    tier_order > target_tier_idx,
                    and_(
                        tier_order == target_tier_idx,
                        or_(
                            PlayerRating.division < rating.division,
                            and_(
                                PlayerRating.division == rating.division,
                                or_(
                                    PlayerRating.rating_points > rating.rating_points,
                                    and_(
                                        PlayerRating.rating_points == rating.rating_points,
                                        PlayerRating.wins > rating.wins,
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            )
        )
        better_count = await self.db.scalar(better_query) or 0
        return better_count + 1

    async def get_tier_distribution(
        self, season_id: uuid.UUID
    ) -> dict[str, int]:
        """返回各段位的玩家数量分布，key 为 tier 名，value 为数量。"""
        tier_order = _tier_order_case()
        query = (
            select(PlayerRating.tier, func.count())
            .where(PlayerRating.season_id == season_id)
            .group_by(PlayerRating.tier, tier_order)
            .order_by(desc(tier_order))
        )
        result = await self.db.execute(query)
        distribution: dict[str, int] = {tier: 0 for tier in TIER_ORDER}
        for tier, count in result.all():
            if tier in distribution:
                distribution[tier] = int(count)
        return distribution

    async def get_neighbors(
        self,
        player_id: uuid.UUID,
        season_id: uuid.UUID,
        before: int = 2,
        after: int = 2,
    ) -> tuple[Sequence[PlayerRating], int | None]:
        """返回排名附近的玩家列表。

        Returns:
            (neighbors, my_rank) - neighbors 包含玩家自身及附近 N 名玩家；
            my_rank 为玩家自身排名，无段位记录时返回 (空列表, None)。
        """
        rating = await self.get_player_rating(player_id, season_id)
        if rating is None:
            return [], None

        my_rank = await self.get_player_rank(player_id, season_id)
        if my_rank is None:
            return [], None

        start = max(0, my_rank - 1 - before)
        window_size = before + 1 + after

        tier_order = _tier_order_case()
        query = (
            select(PlayerRating)
            .where(PlayerRating.season_id == season_id)
            .order_by(
                desc(tier_order),
                PlayerRating.division,
                desc(PlayerRating.rating_points),
                desc(PlayerRating.wins),
            )
            .limit(window_size)
            .offset(start)
        )
        result = await self.db.execute(query)
        return result.scalars().all(), my_rank

    async def count_active_players(self, season_id: uuid.UUID) -> int:
        """统计赛季活跃玩家数（有段位记录的玩家）。"""
        query = select(func.count()).select_from(
            select(PlayerRating).where(PlayerRating.season_id == season_id).subquery()
        )
        result = await self.db.scalar(query)
        return int(result or 0)

    async def list_all_ratings_for_settlement(
        self,
        season_id: uuid.UUID,
        limit: int = 200,
        offset: int = 0,
    ) -> Sequence[PlayerRating]:
        """列出赛季所有段位记录（用于结算），按排名顺序返回。"""
        tier_order = _tier_order_case()
        query = (
            select(PlayerRating)
            .where(PlayerRating.season_id == season_id)
            .order_by(
                desc(tier_order),
                PlayerRating.division,
                desc(PlayerRating.rating_points),
                desc(PlayerRating.wins),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return result.scalars().all()


class MatchQueueRepository:
    """匹配队列仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def join_queue(
        self,
        player_id: uuid.UUID,
        season_id: uuid.UUID,
        match_mode: str = "solo_1v1",
        tier: str = "bronze",
        division: int = 5,
        player_level: int = 1,
        timeout_seconds: int = DEFAULT_MATCH_TIMEOUT_SECONDS,
    ) -> MatchQueue:
        now = datetime.now(timezone.utc)
        queue_item = MatchQueue(
            queue_id=uuid.uuid4(),
            player_id=player_id,
            season_id=season_id,
            match_mode=match_mode,
            status="queuing",
            tier=tier,
            division=division,
            player_level=player_level,
            joined_at=now,
            timeout_at=now + timedelta(seconds=timeout_seconds),
        )
        self.db.add(queue_item)
        await self.db.flush()
        return queue_item

    async def leave_queue(self, player_id: uuid.UUID, season_id: uuid.UUID) -> MatchQueue | None:
        result = await self.db.execute(
            select(MatchQueue).where(
                and_(
                    MatchQueue.player_id == player_id,
                    MatchQueue.season_id == season_id,
                    MatchQueue.status == "queuing",
                )
            )
        )
        queue_item = result.scalar_one_or_none()
        if queue_item is None:
            return None
        queue_item.status = "cancelled"
        queue_item.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return queue_item

    async def get_player_queue_status(
        self, player_id: uuid.UUID, season_id: uuid.UUID
    ) -> MatchQueue | None:
        result = await self.db.execute(
            select(MatchQueue).where(
                and_(
                    MatchQueue.player_id == player_id,
                    MatchQueue.season_id == season_id,
                    MatchQueue.status == "queuing",
                )
            )
        )
        return result.scalar_one_or_none()

    async def is_player_in_queue(self, player_id: uuid.UUID, season_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(func.count())
            .select_from(MatchQueue)
            .where(
                and_(
                    MatchQueue.player_id == player_id,
                    MatchQueue.season_id == season_id,
                    MatchQueue.status == "queuing",
                )
            )
        )
        count = result.scalar_one() or 0
        return count > 0

    async def find_match(
        self,
        player_id: uuid.UUID,
        season_id: uuid.UUID,
        match_mode: str,
        tier: str,
        division: int,
        player_level: int,
        tier_range: int = DEFAULT_TIER_RANGE,
        level_range: int = DEFAULT_LEVEL_RANGE,
    ) -> MatchQueue | None:
        player_tier_idx = tier_to_index(tier)
        min_tier_idx = max(0, player_tier_idx - tier_range)
        max_tier_idx = min(len(TIER_ORDER) - 1, player_tier_idx + tier_range)

        min_level = max(1, player_level - level_range)
        max_level = player_level + level_range

        result = await self.db.execute(
            select(MatchQueue)
            .where(
                and_(
                    MatchQueue.season_id == season_id,
                    MatchQueue.match_mode == match_mode,
                    MatchQueue.status == "queuing",
                    MatchQueue.player_id != player_id,
                    MatchQueue.player_level >= min_level,
                    MatchQueue.player_level <= max_level,
                    MatchQueue.tier.in_([index_to_tier(i) for i in range(min_tier_idx, max_tier_idx + 1)]),
                )
            )
            .order_by(MatchQueue.joined_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_matched(
        self, queue_id: uuid.UUID, match_room_id: uuid.UUID
    ) -> MatchQueue | None:
        result = await self.db.execute(
            select(MatchQueue).where(MatchQueue.queue_id == queue_id)
        )
        queue_item = result.scalar_one_or_none()
        if queue_item is None:
            return None
        queue_item.status = "matched"
        queue_item.matched_at = datetime.now(timezone.utc)
        queue_item.match_room_id = match_room_id
        queue_item.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return queue_item

    async def list_queues(
        self,
        season_id: uuid.UUID | None = None,
        status: str | None = None,
        match_mode: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[MatchQueue], int]:
        query = select(MatchQueue)
        count_query = select(func.count()).select_from(MatchQueue)

        if season_id:
            query = query.where(MatchQueue.season_id == season_id)
            count_query = count_query.where(MatchQueue.season_id == season_id)
        if status:
            query = query.where(MatchQueue.status == status)
            count_query = count_query.where(MatchQueue.status == status)
        if match_mode:
            query = query.where(MatchQueue.match_mode == match_mode)
            count_query = count_query.where(MatchQueue.match_mode == match_mode)

        query = query.order_by(MatchQueue.joined_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one() or 0

        return result.scalars().all(), total


class MatchRoomRepository:
    """对战房间仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_room(
        self,
        season_id: uuid.UUID,
        player1_id: uuid.UUID,
        player2_id: uuid.UUID,
        match_mode: str = "solo_1v1",
    ) -> MatchRoom:
        room = MatchRoom(
            room_id=uuid.uuid4(),
            season_id=season_id,
            match_mode=match_mode,
            status="waiting",
            player1_id=player1_id,
            player2_id=player2_id,
            player1_ready=False,
            player2_ready=False,
        )
        self.db.add(room)
        await self.db.flush()
        return room

    async def get_room(self, room_id: uuid.UUID) -> MatchRoom | None:
        result = await self.db.execute(
            select(MatchRoom).where(MatchRoom.room_id == room_id)
        )
        return result.scalar_one_or_none()

    async def player_ready(
        self, room_id: uuid.UUID, player_id: uuid.UUID
    ) -> MatchRoom | None:
        room = await self.get_room(room_id)
        if room is None:
            return None

        if room.player1_id == player_id:
            room.player1_ready = True
        elif room.player2_id == player_id:
            room.player2_ready = True
        else:
            return None

        if room.player1_ready and room.player2_ready and room.status == "waiting":
            room.status = "ready"

        room.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return room

    async def start_match(self, room_id: uuid.UUID) -> MatchRoom | None:
        room = await self.get_room(room_id)
        if room is None:
            return None
        room.status = "in_progress"
        room.started_at = datetime.now(timezone.utc)
        room.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return room

    async def submit_result(
        self,
        room_id: uuid.UUID,
        winner_id: uuid.UUID,
        match_data: dict | None = None,
    ) -> MatchRoom | None:
        room = await self.get_room(room_id)
        if room is None:
            return None
        room.status = "completed"
        room.winner_id = winner_id
        room.ended_at = datetime.now(timezone.utc)
        if room.started_at:
            duration = (room.ended_at - room.started_at).total_seconds()
            room.duration_seconds = int(duration)
        room.match_data_jsonb = match_data
        room.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return room

    async def list_rooms(
        self,
        season_id: uuid.UUID | None = None,
        status: str | None = None,
        player_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[MatchRoom], int]:
        query = select(MatchRoom)
        count_query = select(func.count()).select_from(MatchRoom)

        if season_id:
            query = query.where(MatchRoom.season_id == season_id)
            count_query = count_query.where(MatchRoom.season_id == season_id)
        if status:
            query = query.where(MatchRoom.status == status)
            count_query = count_query.where(MatchRoom.status == status)
        if player_id:
            query = query.where(
                or_(
                    MatchRoom.player1_id == player_id,
                    MatchRoom.player2_id == player_id,
                )
            )
            count_query = count_query.where(
                or_(
                    MatchRoom.player1_id == player_id,
                    MatchRoom.player2_id == player_id,
                )
            )

        query = query.order_by(MatchRoom.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one() or 0

        return result.scalars().all(), total


class MatchResultRepository:
    """对战结果仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_result(
        self,
        room_id: uuid.UUID,
        season_id: uuid.UUID,
        match_mode: str,
        winner_id: uuid.UUID | None,
        loser_id: uuid.UUID | None,
        is_draw: bool,
        winner_rating_change: int,
        loser_rating_change: int,
        winner_tier_before: str,
        winner_division_before: int,
        winner_tier_after: str,
        winner_division_after: int,
        loser_tier_before: str,
        loser_division_before: int,
        loser_tier_after: str,
        loser_division_after: int,
        submitted_by: uuid.UUID,
        match_data: dict | None = None,
    ) -> MatchResult:
        result = MatchResult(
            result_id=uuid.uuid4(),
            room_id=room_id,
            season_id=season_id,
            match_mode=match_mode,
            winner_id=winner_id,
            loser_id=loser_id,
            is_draw=is_draw,
            winner_rating_change=winner_rating_change,
            loser_rating_change=loser_rating_change,
            winner_tier_before=winner_tier_before,
            winner_division_before=winner_division_before,
            winner_tier_after=winner_tier_after,
            winner_division_after=winner_division_after,
            loser_tier_before=loser_tier_before,
            loser_division_before=loser_division_before,
            loser_tier_after=loser_tier_after,
            loser_division_after=loser_division_after,
            match_data_jsonb=match_data,
            submitted_by=submitted_by,
        )
        self.db.add(result)
        await self.db.flush()
        return result

    async def get_result(self, result_id: uuid.UUID) -> MatchResult | None:
        result_obj = await self.db.execute(
            select(MatchResult).where(MatchResult.result_id == result_id)
        )
        return result_obj.scalar_one_or_none()

    async def get_result_by_room(self, room_id: uuid.UUID) -> MatchResult | None:
        result = await self.db.execute(
            select(MatchResult).where(MatchResult.room_id == room_id)
        )
        return result.scalar_one_or_none()

    async def list_results(
        self,
        season_id: uuid.UUID | None = None,
        player_id: uuid.UUID | None = None,
        match_mode: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[MatchResult], int]:
        query = select(MatchResult)
        count_query = select(func.count()).select_from(MatchResult)

        if season_id:
            query = query.where(MatchResult.season_id == season_id)
            count_query = count_query.where(MatchResult.season_id == season_id)
        if player_id:
            query = query.where(
                or_(
                    MatchResult.winner_id == player_id,
                    MatchResult.loser_id == player_id,
                )
            )
            count_query = count_query.where(
                or_(
                    MatchResult.winner_id == player_id,
                    MatchResult.loser_id == player_id,
                )
            )
        if match_mode:
            query = query.where(MatchResult.match_mode == match_mode)
            count_query = count_query.where(MatchResult.match_mode == match_mode)

        query = query.order_by(MatchResult.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one() or 0

        return result.scalars().all(), total

    async def get_player_match_history(
        self,
        player_id: uuid.UUID,
        season_id: uuid.UUID | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[MatchResult], int]:
        query = select(MatchResult).where(
            or_(
                MatchResult.winner_id == player_id,
                MatchResult.loser_id == player_id,
            )
        )
        count_query = select(func.count()).select_from(MatchResult).where(
            or_(
                MatchResult.winner_id == player_id,
                MatchResult.loser_id == player_id,
            )
        )

        if season_id:
            query = query.where(MatchResult.season_id == season_id)
            count_query = count_query.where(MatchResult.season_id == season_id)

        query = query.order_by(MatchResult.created_at.desc()).limit(limit).offset(offset)

        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one() or 0

        return result.scalars().all(), total


def calculate_rating_change(
    winner_tier: str,
    winner_division: int,
    loser_tier: str,
    loser_division: int,
    base_points: int = 20,
) -> tuple[int, int]:
    winner_total = tier_to_index(winner_tier) * 5 + (5 - winner_division)
    loser_total = tier_to_index(loser_tier) * 5 + (5 - loser_division)
    diff = loser_total - winner_total

    winner_gain = base_points + diff
    loser_loss = base_points - diff

    winner_gain = max(5, min(winner_gain, 50))
    loser_loss = max(5, min(loser_loss, 50))

    return winner_gain, loser_loss
