"""跨服匹配系统 API 测试。"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.core.errors import PlayerErrorCodes
from app.domain.models import Player, MatchSeason, PlayerRating, MatchRoom, MatchResult
from app.schemas.auth import Role

PLAYER_A_ID = "00000000-0000-0000-0000-000000000001"
PLAYER_B_ID = "00000000-0000-0000-0000-000000000002"
PLAYER_C_ID = "00000000-0000-0000-0000-000000000003"


@pytest_asyncio.fixture
def player_a_token() -> str:
    return create_test_token(user_id=PLAYER_A_ID, role=Role.PLAYER)


@pytest_asyncio.fixture
def player_b_token() -> str:
    return create_test_token(user_id=PLAYER_B_ID, role=Role.PLAYER)


@pytest_asyncio.fixture
def player_c_token() -> str:
    return create_test_token(user_id=PLAYER_C_ID, role=Role.PLAYER)


@pytest_asyncio.fixture
def ops_token() -> str:
    return create_test_token(user_id="ops-001", role=Role.OPS)


@pytest_asyncio.fixture
async def player_a() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_A_ID),
        display_name="PlayerA",
        chapter_id="ch_prologue_01",
        level=10,
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def player_b() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_B_ID),
        display_name="PlayerB",
        chapter_id="ch_prologue_01",
        level=12,
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def player_c() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_C_ID),
        display_name="PlayerC",
        chapter_id="ch_prologue_01",
        level=8,
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def active_season() -> MatchSeason:
    """创建一个活跃的赛季。"""
    from tests.conftest import TestSessionLocal

    now = datetime.now(timezone.utc)
    season = MatchSeason(
        season_id=uuid.uuid4(),
        season_key="s2026_01",
        season_name="2026 年第一赛季",
        status="active",
        start_at=now - timedelta(days=1),
        end_at=now + timedelta(days=30),
    )
    async with TestSessionLocal() as session:
        session.add(season)
        await session.commit()
        await session.refresh(season)
    return season


@pytest.mark.asyncio
async def test_get_my_rating_success(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """获取我的段位信息成功。"""
    response = await client.get(
        "/api/v1/player/match/rating",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["tier"] == "bronze"
    assert data["data"]["division"] == 5
    assert data["data"]["rating_points"] == 0
    assert data["data"]["season_id"] == str(active_season.season_id)


@pytest.mark.asyncio
async def test_get_my_rating_no_active_season(
    client: AsyncClient,
    player_a: Player,
    player_a_token: str,
) -> None:
    """无活跃赛季时获取段位返回 404。"""
    response = await client.get(
        "/api/v1/player/match/rating",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.NO_ACTIVE_SEASON


@pytest.mark.asyncio
async def test_get_my_rating_unauthorized(client: AsyncClient) -> None:
    """未授权访问返回 401。"""
    response = await client.get("/api/v1/player/match/rating")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_join_match_queue_success(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """加入匹配队列成功。"""
    response = await client.post(
        "/api/v1/player/match/queue/join",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={"match_mode": "solo_1v1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "queuing"
    assert data["data"]["match_mode"] == "solo_1v1"
    assert data["data"]["player_id"] == PLAYER_A_ID


@pytest.mark.asyncio
async def test_join_match_queue_already_in_queue(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """重复加入匹配队列返回 409。"""
    await client.post(
        "/api/v1/player/match/queue/join",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={"match_mode": "solo_1v1"},
    )
    response = await client.post(
        "/api/v1/player/match/queue/join",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={"match_mode": "solo_1v1"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_ALREADY_IN_QUEUE


@pytest.mark.asyncio
async def test_leave_match_queue_success(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """离开匹配队列成功。"""
    await client.post(
        "/api/v1/player/match/queue/join",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={"match_mode": "solo_1v1"},
    )
    response = await client.post(
        "/api/v1/player/match/queue/leave",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={"match_mode": "solo_1v1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "cancelled"


@pytest.mark.asyncio
async def test_leave_match_queue_not_in_queue(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """未在队列中离开返回 404。"""
    response = await client.post(
        "/api/v1/player/match/queue/leave",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={"match_mode": "solo_1v1"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_IN_QUEUE


@pytest.mark.asyncio
async def test_get_match_queue_status(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """获取匹配队列状态。"""
    await client.post(
        "/api/v1/player/match/queue/join",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={"match_mode": "solo_1v1"},
    )
    response = await client.get(
        "/api/v1/player/match/queue/status",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"] is not None
    assert data["data"]["status"] == "queuing"


@pytest.mark.asyncio
async def test_submit_match_result_and_rating_change(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """提交对战结果并验证段位变化。"""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        room = MatchRoom(
            room_id=uuid.uuid4(),
            season_id=active_season.season_id,
            match_mode="solo_1v1",
            player1_id=uuid.UUID(PLAYER_A_ID),
            player2_id=uuid.UUID(PLAYER_B_ID),
            status="in_progress",
        )
        session.add(room)
        await session.commit()
        room_id = room.room_id

    response = await client.post(
        f"/api/v1/player/match/rooms/{room_id}/result",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={
            "winner_id": PLAYER_A_ID,
            "match_data": {"duration": 300},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["winner_id"] == PLAYER_A_ID
    assert data["data"]["winner_rating_change"] > 0
    assert data["data"]["loser_rating_change"] < 0

    rating_resp = await client.get(
        "/api/v1/player/match/rating",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert rating_resp.status_code == 200
    rating_data = rating_resp.json()
    assert rating_data["data"]["wins"] == 1


@pytest.mark.asyncio
async def test_submit_match_result_already_completed(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """重复提交对战结果返回 409。"""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        room = MatchRoom(
            room_id=uuid.uuid4(),
            season_id=active_season.season_id,
            match_mode="solo_1v1",
            player1_id=uuid.UUID(PLAYER_A_ID),
            player2_id=uuid.UUID(PLAYER_B_ID),
            status="completed",
            winner_id=uuid.UUID(PLAYER_A_ID),
        )
        session.add(room)
        await session.commit()
        room_id = room.room_id

    response = await client.post(
        f"/api/v1/player/match/rooms/{room_id}/result",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={
            "winner_id": PLAYER_A_ID,
            "match_data": {"duration": 300},
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.MATCH_ALREADY_COMPLETED


@pytest.mark.asyncio
async def test_get_match_room_not_found(
    client: AsyncClient,
    player_a: Player,
    player_a_token: str,
) -> None:
    """获取不存在的房间返回 404。"""
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/player/match/rooms/{fake_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.MATCH_ROOM_NOT_FOUND


@pytest.mark.asyncio
async def test_get_match_history(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """获取对战历史记录。"""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        result = MatchResult(
            result_id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            season_id=active_season.season_id,
            match_mode="solo_1v1",
            winner_id=uuid.UUID(PLAYER_A_ID),
            loser_id=uuid.UUID(PLAYER_B_ID),
            is_draw=False,
            winner_rating_change=15,
            loser_rating_change=-15,
            winner_tier_before="bronze",
            winner_division_before=3,
            winner_tier_after="bronze",
            winner_division_after=3,
            loser_tier_before="bronze",
            loser_division_before=3,
            loser_tier_after="bronze",
            loser_division_after=3,
            submitted_by=uuid.UUID(PLAYER_A_ID),
        )
        session.add(result)
        await session.commit()

    response = await client.get(
        "/api/v1/player/match/history",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] >= 1
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_get_match_leaderboard(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    active_season: MatchSeason,
    player_a_token: str,
    player_b_token: str,
) -> None:
    """获取排行榜。"""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        rating_a = PlayerRating(
            rating_id=uuid.uuid4(),
            player_id=uuid.UUID(PLAYER_A_ID),
            season_id=active_season.season_id,
            tier="silver",
            division=1,
            rating_points=1200,
            wins=10,
            losses=5,
        )
        rating_b = PlayerRating(
            rating_id=uuid.uuid4(),
            player_id=uuid.UUID(PLAYER_B_ID),
            season_id=active_season.season_id,
            tier="bronze",
            division=2,
            rating_points=800,
            wins=5,
            losses=10,
        )
        session.add_all([rating_a, rating_b])
        await session.commit()

    response = await client.get(
        "/api/v1/player/match/leaderboard",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] >= 2
    assert data["data"]["items"][0]["rank"] == 1
    assert data["data"]["items"][0]["tier"] == "silver"


@pytest.mark.asyncio
async def test_ops_create_season_success(
    client: AsyncClient,
    ops_token: str,
) -> None:
    """运营创建赛季成功。"""
    now = datetime.now(timezone.utc)
    response = await client.post(
        "/api/v1/ops/match/seasons",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-season-001",
        },
        json={
            "season_key": "s2026_02",
            "season_name": "2026 年第二赛季",
            "start_at": (now + timedelta(days=30)).isoformat(),
            "end_at": (now + timedelta(days=60)).isoformat(),
            "description": "测试赛季",
            "reward_config": {"top_100": "称号"},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["season_key"] == "s2026_02"
    assert data["data"]["status"] == "upcoming"


@pytest.mark.asyncio
async def test_ops_create_season_duplicate(
    client: AsyncClient,
    active_season: MatchSeason,
    ops_token: str,
) -> None:
    """创建重复赛季返回 409。"""
    now = datetime.now(timezone.utc)
    response = await client.post(
        "/api/v1/ops/match/seasons",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-create-season-dup",
        },
        json={
            "season_key": active_season.season_key,
            "season_name": "重复赛季",
            "start_at": now.isoformat(),
            "end_at": (now + timedelta(days=30)).isoformat(),
        },
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.MATCH_SEASON_ALREADY_EXISTS


@pytest.mark.asyncio
async def test_ops_list_seasons(
    client: AsyncClient,
    active_season: MatchSeason,
    ops_token: str,
) -> None:
    """运营获取赛季列表。"""
    response = await client.get(
        "/api/v1/ops/match/seasons",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_ops_update_season_status(
    client: AsyncClient,
    active_season: MatchSeason,
    ops_token: str,
) -> None:
    """运营更新赛季状态。"""
    response = await client.patch(
        f"/api/v1/ops/match/seasons/{active_season.season_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-season-status",
        },
        json={"status": "ended"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "ended"


@pytest.mark.asyncio
async def test_ops_list_queues(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
    ops_token: str,
) -> None:
    """运营获取匹配队列列表。"""
    await client.post(
        "/api/v1/player/match/queue/join",
        headers={"Authorization": f"Bearer {player_a_token}"},
        json={"match_mode": "solo_1v1"},
    )
    response = await client.get(
        "/api/v1/ops/match/queues",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_ops_list_rooms(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    active_season: MatchSeason,
    ops_token: str,
) -> None:
    """运营获取对战房间列表。"""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        room = MatchRoom(
            room_id=uuid.uuid4(),
            season_id=active_season.season_id,
            match_mode="solo_1v1",
            player1_id=uuid.UUID(PLAYER_A_ID),
            player2_id=uuid.UUID(PLAYER_B_ID),
            status="in_progress",
        )
        session.add(room)
        await session.commit()

    response = await client.get(
        "/api/v1/ops/match/rooms",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_ops_list_results(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    active_season: MatchSeason,
    ops_token: str,
) -> None:
    """运营获取对战结果列表。"""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        result = MatchResult(
            result_id=uuid.uuid4(),
            room_id=uuid.uuid4(),
            season_id=active_season.season_id,
            match_mode="solo_1v1",
            winner_id=uuid.UUID(PLAYER_A_ID),
            loser_id=uuid.UUID(PLAYER_B_ID),
            is_draw=False,
            winner_rating_change=15,
            loser_rating_change=-15,
            winner_tier_before="bronze",
            winner_division_before=3,
            winner_tier_after="bronze",
            winner_division_after=3,
            loser_tier_before="bronze",
            loser_division_before=3,
            loser_tier_after="bronze",
            loser_division_after=3,
            submitted_by=uuid.UUID(PLAYER_A_ID),
        )
        session.add(result)
        await session.commit()

    response = await client.get(
        "/api/v1/ops/match/results",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_match_season_not_found(
    client: AsyncClient,
    ops_token: str,
) -> None:
    """更新不存在的赛季状态返回 404。"""
    fake_id = uuid.uuid4()
    response = await client.patch(
        f"/api/v1/ops/match/seasons/{fake_id}/status",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-update-nonexistent",
        },
        json={"status": "ended"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.MATCH_SEASON_NOT_FOUND


@pytest.mark.asyncio
async def test_player_not_in_room(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    player_c: Player,
    active_season: MatchSeason,
    player_c_token: str,
) -> None:
    """非房间内玩家提交结果返回 403。"""
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        room = MatchRoom(
            room_id=uuid.uuid4(),
            season_id=active_season.season_id,
            match_mode="solo_1v1",
            player1_id=uuid.UUID(PLAYER_A_ID),
            player2_id=uuid.UUID(PLAYER_B_ID),
            status="in_progress",
        )
        session.add(room)
        await session.commit()
        room_id = room.room_id

    response = await client.post(
        f"/api/v1/player/match/rooms/{room_id}/result",
        headers={"Authorization": f"Bearer {player_c_token}"},
        json={
            "winner_id": PLAYER_A_ID,
            "match_data": {"duration": 300},
        },
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_IN_ROOM


# === 赛季排行系统测试 ===


@pytest_asyncio.fixture
async def ended_season() -> MatchSeason:
    """创建一个已结束的赛季（用于结算测试）。"""
    from tests.conftest import TestSessionLocal

    now = datetime.now(timezone.utc)
    season = MatchSeason(
        season_id=uuid.uuid4(),
        season_key="s2025_ended_01",
        season_name="2025 年已结束赛季",
        status="ended",
        start_at=now - timedelta(days=60),
        end_at=now - timedelta(days=30),
        settlement_status="unsettled",
    )
    async with TestSessionLocal() as session:
        session.add(season)
        await session.commit()
        await session.refresh(season)
    return season


async def _create_rating(
    player_id: str,
    season_id: uuid.UUID,
    tier: str,
    division: int,
    rating_points: int,
    wins: int = 0,
    losses: int = 0,
) -> PlayerRating:
    """辅助函数：直接创建段位记录。"""
    from tests.conftest import TestSessionLocal

    rating = PlayerRating(
        rating_id=uuid.uuid4(),
        player_id=uuid.UUID(player_id),
        season_id=season_id,
        tier=tier,
        division=division,
        rating_points=rating_points,
        wins=wins,
        losses=losses,
    )
    async with TestSessionLocal() as session:
        session.add(rating)
        await session.commit()
    return rating


@pytest.mark.asyncio
async def test_get_match_leaderboard_tier_sort_order(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    player_c: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """排行榜段位排序正确性：challenger > master > diamond > ... > bronze。"""
    await _create_rating(PLAYER_A_ID, active_season.season_id, "challenger", 1, 999, wins=20)
    await _create_rating(PLAYER_B_ID, active_season.season_id, "master", 1, 800, wins=15)
    await _create_rating(PLAYER_C_ID, active_season.season_id, "bronze", 5, 0, wins=1)

    response = await client.get(
        "/api/v1/player/match/leaderboard",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    items = data["data"]["items"]
    assert len(items) == 3
    # challenger 应排第 1，master 第 2，bronze 第 3
    assert items[0]["tier"] == "challenger"
    assert items[0]["rank"] == 1
    assert items[1]["tier"] == "master"
    assert items[1]["rank"] == 2
    assert items[2]["tier"] == "bronze"
    assert items[2]["rank"] == 3


@pytest.mark.asyncio
async def test_get_match_leaderboard_with_season_id(
    client: AsyncClient,
    player_a: Player,
    ended_season: MatchSeason,
    player_a_token: str,
) -> None:
    """通过 season_id 查询历史赛季排行榜。"""
    await _create_rating(PLAYER_A_ID, ended_season.season_id, "gold", 2, 500, wins=8)

    response = await client.get(
        f"/api/v1/player/match/leaderboard?season_id={ended_season.season_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] >= 1
    assert data["data"]["items"][0]["tier"] == "gold"


@pytest.mark.asyncio
async def test_get_match_leaderboard_invalid_season_id(
    client: AsyncClient,
    player_a_token: str,
) -> None:
    """查询不存在的赛季返回 404。"""
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/player/match/leaderboard?season_id={fake_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.MATCH_SEASON_NOT_FOUND


@pytest.mark.asyncio
async def test_get_my_rank_success(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    player_c: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """查询玩家自身排名成功。"""
    await _create_rating(PLAYER_A_ID, active_season.season_id, "gold", 2, 500, wins=8, losses=2)
    await _create_rating(PLAYER_B_ID, active_season.season_id, "diamond", 1, 600, wins=12)
    await _create_rating(PLAYER_C_ID, active_season.season_id, "bronze", 5, 0, wins=0, losses=5)

    response = await client.get(
        "/api/v1/player/match/leaderboard/me",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["player_id"] == PLAYER_A_ID
    assert data["tier"] == "gold"
    assert data["rank"] == 2  # diamond 第一，gold 第二
    assert data["total_players"] == 3
    assert data["total_matches"] == 10
    assert data["win_rate"] == 0.8


@pytest.mark.asyncio
async def test_get_my_rank_no_rating(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """玩家无段位记录返回 404。"""
    response = await client.get(
        "/api/v1/player/match/leaderboard/me",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_RATING_NOT_FOUND


@pytest.mark.asyncio
async def test_get_tier_distribution(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    player_c: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """段位分布查询。"""
    await _create_rating(PLAYER_A_ID, active_season.season_id, "gold", 2, 500)
    await _create_rating(PLAYER_B_ID, active_season.season_id, "gold", 3, 400)
    await _create_rating(PLAYER_C_ID, active_season.season_id, "bronze", 5, 0)

    response = await client.get(
        "/api/v1/player/match/leaderboard/tier-distribution",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_players"] == 3
    # distribution 按段位从高到低排序
    distribution = {item["tier"]: item["count"] for item in data["distribution"]}
    assert distribution["gold"] == 2
    assert distribution["bronze"] == 1
    assert distribution["challenger"] == 0
    # 检查百分比总和接近 100
    total_pct = sum(item["percentage"] for item in data["distribution"])
    assert abs(total_pct - 100.0) < 0.1


@pytest.mark.asyncio
async def test_get_leaderboard_neighbors(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    player_c: Player,
    active_season: MatchSeason,
    player_b_token: str,
) -> None:
    """附近玩家查询：player_b 排第 2，应能看到前后各 1 名。"""
    await _create_rating(PLAYER_A_ID, active_season.season_id, "diamond", 1, 600, wins=12)
    await _create_rating(PLAYER_B_ID, active_season.season_id, "gold", 2, 500, wins=8)
    await _create_rating(PLAYER_C_ID, active_season.season_id, "bronze", 5, 0, wins=0)

    response = await client.get(
        "/api/v1/player/match/leaderboard/neighbors?before=1&after=1",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["my_rank"] == 2
    assert len(data["items"]) == 3  # 前1 + 自己 + 后1
    # 验证排名顺序
    ranks = [item["rank"] for item in data["items"]]
    assert ranks == [1, 2, 3]


@pytest.mark.asyncio
async def test_get_leaderboard_neighbors_no_rating(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """附近玩家查询：玩家无段位记录返回 404。"""
    response = await client.get(
        "/api/v1/player/match/leaderboard/neighbors",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == PlayerErrorCodes.PLAYER_RATING_NOT_FOUND


@pytest.mark.asyncio
async def test_get_my_season_rewards_empty(
    client: AsyncClient,
    player_a: Player,
    player_a_token: str,
) -> None:
    """玩家无奖励记录时返回空列表。"""
    response = await client.get(
        "/api/v1/player/match/rewards",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_settle_match_season_success(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    player_c: Player,
    ended_season: MatchSeason,
    ops_token: str,
) -> None:
    """赛季结算成功。"""
    await _create_rating(PLAYER_A_ID, ended_season.season_id, "challenger", 1, 999, wins=20)
    await _create_rating(PLAYER_B_ID, ended_season.season_id, "gold", 2, 500, wins=8)
    await _create_rating(PLAYER_C_ID, ended_season.season_id, "bronze", 5, 0, wins=1)

    response = await client.post(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/settle",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-settle-001",
        },
        json={"batch_size": 100},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["season_id"] == str(ended_season.season_id)
    assert data["settlement_status"] == "settled"
    assert data["total_grants"] == 3
    assert data["total_players"] == 3
    assert data["tier_distribution"]["challenger"] == 1
    assert data["tier_distribution"]["gold"] == 1
    assert data["tier_distribution"]["bronze"] == 1
    assert data["settled_at"] is not None


@pytest.mark.asyncio
async def test_settle_match_season_not_ended(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    ops_token: str,
) -> None:
    """结算未结束赛季返回 409。"""
    response = await client.post(
        f"/api/v1/ops/match/seasons/{active_season.season_id}/settle",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-settle-not-ended",
        },
        json={},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.MATCH_SEASON_NOT_ENDED


@pytest.mark.asyncio
async def test_settle_match_season_already_settled(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    ended_season: MatchSeason,
    ops_token: str,
) -> None:
    """结算已结算赛季返回幂等结果。"""
    await _create_rating(PLAYER_A_ID, ended_season.season_id, "gold", 1, 700, wins=15)
    await _create_rating(PLAYER_B_ID, ended_season.season_id, "silver", 2, 300, wins=5)

    # 第一次结算
    response1 = await client.post(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/settle",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-settle-idemp-1",
        },
        json={},
    )
    assert response1.status_code == 200
    assert response1.json()["data"]["total_grants"] == 2

    # 第二次结算（不同幂等键）：应返回幂等结果，不重复发放
    response2 = await client.post(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/settle",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-settle-idemp-2",
        },
        json={},
    )
    assert response2.status_code == 200
    data2 = response2.json()["data"]
    assert data2["settlement_status"] == "settled"
    assert data2["total_grants"] == 2  # 仍是 2，未重复发放


@pytest.mark.asyncio
async def test_settle_match_season_not_found(
    client: AsyncClient,
    ops_token: str,
) -> None:
    """结算不存在的赛季返回 404。"""
    fake_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/ops/match/seasons/{fake_id}/settle",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-settle-not-found",
        },
        json={},
    )
    assert response.status_code == 404
    assert response.json()["code"] == PlayerErrorCodes.MATCH_SEASON_NOT_FOUND


@pytest.mark.asyncio
async def test_list_season_rewards(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    ended_season: MatchSeason,
    ops_token: str,
) -> None:
    """运营查询赛季奖励列表。"""
    await _create_rating(PLAYER_A_ID, ended_season.season_id, "gold", 1, 700, wins=15)
    await _create_rating(PLAYER_B_ID, ended_season.season_id, "silver", 2, 300, wins=5)

    # 先结算
    await client.post(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/settle",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-settle-for-list",
        },
        json={},
    )

    # 查询奖励列表
    response = await client.get(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/rewards",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 2
    # 按排名升序
    assert data["items"][0]["final_rank"] == 1
    assert data["items"][0]["final_tier"] == "gold"
    assert data["items"][1]["final_rank"] == 2
    assert data["items"][1]["final_tier"] == "silver"
    # 验证奖励负载
    assert data["items"][0]["reward_payload"] is not None
    assert "title" in data["items"][0]["reward_payload"]


@pytest.mark.asyncio
async def test_list_season_rewards_with_status_filter(
    client: AsyncClient,
    player_a: Player,
    ended_season: MatchSeason,
    ops_token: str,
) -> None:
    """运营按状态过滤赛季奖励列表。"""
    await _create_rating(PLAYER_A_ID, ended_season.season_id, "gold", 1, 700, wins=15)

    # 先结算
    await client.post(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/settle",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-settle-for-filter",
        },
        json={},
    )

    # 仅查 granted 状态
    response = await client.get(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/rewards?status_filter=granted",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["status"] == "granted"


@pytest.mark.asyncio
async def test_get_my_season_rewards_after_settle(
    client: AsyncClient,
    player_a: Player,
    ended_season: MatchSeason,
    player_a_token: str,
    ops_token: str,
) -> None:
    """玩家在赛季结算后能查到自己的奖励。"""
    await _create_rating(PLAYER_A_ID, ended_season.season_id, "diamond", 1, 800, wins=20)

    # 运营结算
    await client.post(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/settle",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-settle-for-player-query",
        },
        json={},
    )

    # 玩家查询自己的奖励
    response = await client.get(
        "/api/v1/player/match/rewards",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert data["items"][0]["final_tier"] == "diamond"
    assert data["items"][0]["final_rank"] == 1
    assert data["items"][0]["status"] == "granted"


@pytest.mark.asyncio
async def test_get_match_leaderboard_unauthorized(client: AsyncClient) -> None:
    """未授权访问排行榜返回 401。"""
    response = await client.get("/api/v1/player/match/leaderboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_my_rank_unauthorized(client: AsyncClient) -> None:
    """未授权访问自身排名返回 401。"""
    response = await client.get("/api/v1/player/match/leaderboard/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_settle_match_season_forbidden(
    client: AsyncClient,
    ended_season: MatchSeason,
    player_a_token: str,
) -> None:
    """普通玩家不能结算赛季，返回 403。"""
    response = await client.post(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/settle",
        headers={
            "Authorization": f"Bearer {player_a_token}",
            "Idempotency-Key": "test-settle-forbidden",
        },
        json={},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_tier_distribution_empty_season(
    client: AsyncClient,
    player_a: Player,
    active_season: MatchSeason,
    player_a_token: str,
) -> None:
    """空赛季段位分布返回全 0。"""
    response = await client.get(
        "/api/v1/player/match/leaderboard/tier-distribution",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_players"] == 0
    # 所有段位 count 应为 0
    for item in data["distribution"]:
        assert item["count"] == 0
        assert item["percentage"] == 0.0


@pytest.mark.asyncio
async def test_settle_match_season_with_reward_config(
    client: AsyncClient,
    player_a: Player,
    ended_season: MatchSeason,
    ops_token: str,
    player_a_token: str,
) -> None:
    """结算时使用自定义奖励配置。"""
    await _create_rating(PLAYER_A_ID, ended_season.season_id, "master", 1, 800, wins=18)

    custom_config = {
        "master": {"title": "自定义宗师", "currency": 9999, "item": "rare_weapon"},
    }
    response = await client.post(
        f"/api/v1/ops/match/seasons/{ended_season.season_id}/settle",
        headers={
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "test-settle-custom-cfg",
        },
        json={"reward_config": custom_config},
    )
    assert response.status_code == 200

    # 玩家查询奖励，验证自定义配置生效
    reward_resp = await client.get(
        "/api/v1/player/match/rewards",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert reward_resp.status_code == 200
    items = reward_resp.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["reward_payload"]["title"] == "自定义宗师"
    assert items[0]["reward_payload"]["currency"] == 9999
    # 排名前 10 应有 rank_bonus
    assert "rank_bonus" in items[0]["reward_payload"]
