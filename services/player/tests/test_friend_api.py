"""好友系统 API 测试。"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_test_token
from app.core.errors import PlayerErrorCodes
from app.domain.models import Friendship, Player
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
async def player_a() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_A_ID),
        display_name="PlayerA",
        chapter_id="ch_prologue_01",
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
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def pending_request(player_a: Player, player_b: Player) -> Friendship:
    """创建一条 A→B 的 pending 好友请求。"""
    from tests.conftest import TestSessionLocal

    friendship = Friendship(
        friendship_id=uuid.uuid4(),
        player_id=player_a.player_id,
        friend_id=player_b.player_id,
        status="pending",
    )
    async with TestSessionLocal() as session:
        session.add(friendship)
        await session.commit()
    return friendship


@pytest_asyncio.fixture
async def accepted_friendship(player_a: Player, player_b: Player) -> Friendship:
    """创建一条 A↔B 的 accepted 好友关系。"""
    from tests.conftest import TestSessionLocal

    friendship = Friendship(
        friendship_id=uuid.uuid4(),
        player_id=player_a.player_id,
        friend_id=player_b.player_id,
        status="accepted",
    )
    async with TestSessionLocal() as session:
        session.add(friendship)
        await session.commit()
    return friendship


@pytest.mark.asyncio
async def test_send_friend_request_success(
    client: AsyncClient, player_a: Player, player_b: Player, player_a_token: str
) -> None:
    """测试成功发送好友请求。"""
    response = await client.post(
        "/api/v1/player/friends/request",
        json={"friend_id": PLAYER_B_ID},
        headers={
            "Authorization": f"Bearer {player_a_token}",
            "X-Trace-Id": "trace_test_send_req",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "request_id" in data
    assert data["data"]["status"] == "pending"
    assert data["data"]["player_id"] == PLAYER_A_ID
    assert data["data"]["friend_id"] == PLAYER_B_ID


@pytest.mark.asyncio
async def test_send_friend_request_cannot_friend_self(
    client: AsyncClient, player_a: Player, player_a_token: str
) -> None:
    """测试不能向自己发送好友请求（400）。"""
    response = await client.post(
        "/api/v1/player/friends/request",
        json={"friend_id": PLAYER_A_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["code"] == PlayerErrorCodes.CANNOT_FRIEND_SELF


@pytest.mark.asyncio
async def test_send_friend_request_target_not_found(
    client: AsyncClient, player_a: Player, player_a_token: str
) -> None:
    """测试目标玩家不存在（404）。"""
    fake_id = "00000000-0000-0000-0000-999999999999"
    response = await client.post(
        "/api/v1/player/friends/request",
        json={"friend_id": fake_id},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.PLAYER_NOT_FOUND


@pytest.mark.asyncio
async def test_send_friend_request_already_sent(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    pending_request: Friendship,
    player_a_token: str,
) -> None:
    """测试重复发送好友请求（409）。"""
    response = await client.post(
        "/api/v1/player/friends/request",
        json={"friend_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.FRIEND_REQUEST_ALREADY_SENT


@pytest.mark.asyncio
async def test_send_friend_request_already_friends(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    accepted_friendship: Friendship,
    player_a_token: str,
) -> None:
    """测试已是好友时发送请求（409）。"""
    response = await client.post(
        "/api/v1/player/friends/request",
        json={"friend_id": PLAYER_B_ID},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    data = response.json()
    assert data["code"] == PlayerErrorCodes.ALREADY_FRIENDS


@pytest.mark.asyncio
async def test_accept_friend_request_success(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    pending_request: Friendship,
    player_b_token: str,
) -> None:
    """测试成功接受好友请求。"""
    response = await client.post(
        "/api/v1/player/friends/accept",
        json={"player_id": PLAYER_A_ID},
        headers={
            "Authorization": f"Bearer {player_b_token}",
            "X-Trace-Id": "trace_test_accept",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "accepted"


@pytest.mark.asyncio
async def test_accept_friend_request_not_found(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    player_b_token: str,
) -> None:
    """测试接受不存在的好友请求（404）。"""
    response = await client.post(
        "/api/v1/player/friends/accept",
        json={"player_id": PLAYER_A_ID},
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.FRIEND_REQUEST_NOT_FOUND


@pytest.mark.asyncio
async def test_reject_friend_request_success(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    pending_request: Friendship,
    player_b_token: str,
) -> None:
    """测试成功拒绝好友请求。"""
    response = await client.post(
        "/api/v1/player/friends/reject",
        json={"player_id": PLAYER_A_ID},
        headers={
            "Authorization": f"Bearer {player_b_token}",
            "X-Trace-Id": "trace_test_reject",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "rejected"


@pytest.mark.asyncio
async def test_delete_friend_success(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    accepted_friendship: Friendship,
    player_a_token: str,
) -> None:
    """测试成功删除好友。"""
    response = await client.delete(
        f"/api/v1/player/friends/{PLAYER_B_ID}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["deleted"] is True


@pytest.mark.asyncio
async def test_delete_friend_not_found(
    client: AsyncClient,
    player_a: Player,
    player_a_token: str,
) -> None:
    """测试删除不存在的好友（404）。"""
    fake_id = "00000000-0000-0000-0000-999999999999"
    response = await client.delete(
        f"/api/v1/player/friends/{fake_id}",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == PlayerErrorCodes.FRIEND_NOT_FOUND


@pytest.mark.asyncio
async def test_get_friends_list(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    accepted_friendship: Friendship,
    player_a_token: str,
) -> None:
    """测试获取好友列表。"""
    response = await client.get(
        "/api/v1/player/friends",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert data["data"]["total"] == 1
    assert len(data["data"]["friends"]) == 1
    friend = data["data"]["friends"][0]
    assert friend["friend_id"] == PLAYER_B_ID
    assert friend["status"] == "accepted"


@pytest.mark.asyncio
async def test_get_pending_requests(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    pending_request: Friendship,
    player_b_token: str,
) -> None:
    """测试获取待处理的好友请求。"""
    response = await client.get(
        "/api/v1/player/friends/requests",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert len(data["data"]["requests"]) == 1
    req = data["data"]["requests"][0]
    assert req["player_id"] == PLAYER_A_ID
    assert req["status"] == "pending"


@pytest.mark.asyncio
async def test_get_friend_status(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    accepted_friendship: Friendship,
    player_a_token: str,
) -> None:
    """测试获取好友状态（已有好友关系和无好友关系）。"""
    # 已有好友关系
    response = await client.get(
        f"/api/v1/player/friends/{PLAYER_B_ID}/status",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "accepted"

    # 无好友关系
    fake_id = "00000000-0000-0000-0000-999999999999"
    response = await client.get(
        f"/api/v1/player/friends/{fake_id}/status",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "none"
    assert data["data"]["friendship_id"] is None


@pytest.mark.asyncio
async def test_friend_request_auto_accept(
    client: AsyncClient,
    player_a: Player,
    player_b: Player,
    player_a_token: str,
    player_b_token: str,
) -> None:
    """测试当 B 已向 A 发送 pending 请求时，A 向 B 发送请求会自动接受。"""
    # B 先向 A 发送好友请求
    response_b = await client.post(
        "/api/v1/player/friends/request",
        json={"friend_id": PLAYER_A_ID},
        headers={
            "Authorization": f"Bearer {player_b_token}",
            "X-Trace-Id": "trace_test_auto_accept_b",
        },
    )
    assert response_b.status_code == 201
    assert response_b.json()["data"]["status"] == "pending"

    # A 向 B 发送请求，应自动接受 B 的 pending 请求
    response_a = await client.post(
        "/api/v1/player/friends/request",
        json={"friend_id": PLAYER_B_ID},
        headers={
            "Authorization": f"Bearer {player_a_token}",
            "X-Trace-Id": "trace_test_auto_accept_a",
        },
    )
    assert response_a.status_code == 201
    data_a = response_a.json()
    assert data_a["data"]["status"] == "accepted"

    # 验证好友列表中包含对方
    list_response = await client.get(
        "/api/v1/player/friends",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["data"]["total"] == 1
