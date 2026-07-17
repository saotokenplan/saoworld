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
