"""好友协作任务 API 测试。"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.core.errors import PlayerErrorCodes
from app.domain.models import Friendship, FriendCollabQuest, Player
from app.schemas.auth import Role

PLAYER_A_ID = "00000000-0000-0000-0000-000000000101"
PLAYER_B_ID = "00000000-0000-0000-0000-000000000102"
PLAYER_C_ID = "00000000-0000-0000-0000-000000000103"


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
async def player_a() -> Player:
    player = Player(
        player_id=uuid.UUID(PLAYER_A_ID),
        display_name="PlayerA_Collab",
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
        display_name="PlayerB_Collab",
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
        display_name="PlayerC_Collab",
        chapter_id="ch_prologue_01",
    )
    from tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        session.add(player)
        await session.commit()
    return player


@pytest_asyncio.fixture
async def friendship_a_b(player_a: Player, player_b: Player) -> Friendship:
    """创建 A 和 B 的好友关系（单向，从 A 到 B）。"""
    from tests.conftest import TestSessionLocal

    friend = Friendship(
        friendship_id=uuid.uuid4(),
        player_id=player_a.player_id,
        friend_id=player_b.player_id,
        status="accepted",
    )
    async with TestSessionLocal() as session:
        session.add(friend)
        await session.commit()
    return friend


@pytest_asyncio.fixture
async def existing_quest(player_a: Player, player_b: Player) -> FriendCollabQuest:
    """创建一个待接受的协作任务。"""
    from tests.conftest import TestSessionLocal

    quest = FriendCollabQuest(
        quest_id=uuid.uuid4(),
        initiator_id=player_a.player_id,
        friend_id=player_b.player_id,
        quest_type="hunt",
        status="pending_invite",
        title="狩猎任务",
        description="一起去狩猎",
        objectives_jsonb={"kill_count": 10},
        rewards_jsonb={"gold": 100},
        schema_version=1,
    )
    async with TestSessionLocal() as session:
        session.add(quest)
        await session.commit()
    return quest


@pytest_asyncio.fixture
async def active_quest(player_a: Player, player_b: Player) -> FriendCollabQuest:
    """创建一个进行中的协作任务。"""
    from tests.conftest import TestSessionLocal

    quest = FriendCollabQuest(
        quest_id=uuid.uuid4(),
        initiator_id=player_a.player_id,
        friend_id=player_b.player_id,
        quest_type="explore",
        status="active",
        title="探索任务",
        objectives_jsonb={"areas": 5},
        rewards_jsonb={"exp": 200},
        schema_version=1,
    )
    async with TestSessionLocal() as session:
        session.add(quest)
        await session.commit()
    return quest


@pytest.mark.asyncio
async def test_create_collab_quest_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    player_b: Player,
    friendship_a_b: Friendship,
) -> None:
    """测试创建协作任务成功。"""
    response = await client.post(
        "/api/v1/player/friend/collab-quests",
        json={
            "friend_id": PLAYER_B_ID,
            "quest_type": "hunt",
            "title": "一起狩猎",
            "objectives": {"kill_count": 10},
            "rewards": {"gold": 100},
        },
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["initiator_id"] == PLAYER_A_ID
    assert data["friend_id"] == PLAYER_B_ID
    assert data["status"] == "pending_invite"
    assert data["quest_type"] == "hunt"
    assert data["title"] == "一起狩猎"


@pytest.mark.asyncio
async def test_create_collab_quest_with_self(
    client: AsyncClient, player_a_token: str, player_a: Player
) -> None:
    """测试与自己创建协作任务。"""
    response = await client.post(
        "/api/v1/player/friend/collab-quests",
        json={
            "friend_id": PLAYER_A_ID,
            "quest_type": "hunt",
            "title": "自娱自乐",
        },
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == PlayerErrorCodes.CANNOT_COLLAB_WITH_SELF


@pytest.mark.asyncio
async def test_create_collab_quest_not_friends(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    player_c: Player,
) -> None:
    """测试与非好友创建协作任务。"""
    response = await client.post(
        "/api/v1/player/friend/collab-quests",
        json={
            "friend_id": PLAYER_C_ID,
            "quest_type": "hunt",
            "title": "非好友任务",
        },
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.NOT_FRIENDS_FOR_COLLAB


@pytest.mark.asyncio
async def test_accept_collab_quest_success(
    client: AsyncClient,
    player_b_token: str,
    player_b: Player,
    existing_quest: FriendCollabQuest,
) -> None:
    """测试接受协作任务邀请成功。"""
    response = await client.post(
        f"/api/v1/player/friend/collab-quests/{existing_quest.quest_id}/accept",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_reject_collab_quest_success(
    client: AsyncClient,
    player_b_token: str,
    player_b: Player,
    existing_quest: FriendCollabQuest,
) -> None:
    """测试拒绝协作任务邀请成功。"""
    response = await client.post(
        f"/api/v1/player/friend/collab-quests/{existing_quest.quest_id}/reject",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "failed"


@pytest.mark.asyncio
async def test_update_progress_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    active_quest: FriendCollabQuest,
) -> None:
    """测试更新协作任务进度成功。"""
    response = await client.post(
        f"/api/v1/player/friend/collab-quests/{active_quest.quest_id}/progress",
        json={"progress_data": {"areas_explored": 3}},
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "active"


@pytest.mark.asyncio
async def test_complete_quest_success(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    active_quest: FriendCollabQuest,
) -> None:
    """测试完成协作任务成功。"""
    response = await client.post(
        f"/api/v1/player/friend/collab-quests/{active_quest.quest_id}/complete",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_get_active_quests(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    active_quest: FriendCollabQuest,
) -> None:
    """测试获取进行中的协作任务。"""
    response = await client.get(
        "/api/v1/player/friend/collab-quests/active",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_pending_invites(
    client: AsyncClient,
    player_b_token: str,
    player_b: Player,
    existing_quest: FriendCollabQuest,
) -> None:
    """测试获取待处理邀请。"""
    response = await client.get(
        "/api/v1/player/friend/collab-quests/pending",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_quest_history(
    client: AsyncClient,
    player_a_token: str,
    player_a: Player,
    active_quest: FriendCollabQuest,
) -> None:
    """测试获取协作任务历史。"""
    # 先完成任务使其进入历史
    await client.post(
        f"/api/v1/player/friend/collab-quests/{active_quest.quest_id}/complete",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    response = await client.get(
        "/api/v1/player/friend/collab-quests/history",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_quest_not_found(
    client: AsyncClient, player_a_token: str, player_a: Player
) -> None:
    """测试协作任务不存在。"""
    fake_quest_id = uuid.uuid4()
    response = await client.post(
        f"/api/v1/player/friend/collab-quests/{fake_quest_id}/accept",
        headers={"Authorization": f"Bearer {player_a_token}"},
    )
    assert response.status_code == 404
    assert response.json()["code"] == PlayerErrorCodes.COLLAB_QUEST_NOT_FOUND


@pytest.mark.asyncio
async def test_quest_expired(
    client: AsyncClient,
    player_b_token: str,
    player_b: Player,
    existing_quest: FriendCollabQuest,
) -> None:
    """测试已过期的协作任务不能接受。"""
    # 手动将任务设置为已过期
    from tests.conftest import TestSessionLocal
    from sqlalchemy import select

    async with TestSessionLocal() as session:
        stmt = select(FriendCollabQuest).where(
            FriendCollabQuest.quest_id == existing_quest.quest_id
        )
        result = await session.execute(stmt)
        quest = result.scalar_one_or_none()
        if quest is not None:
            quest.status = "expired"
            await session.commit()

    response = await client.post(
        f"/api/v1/player/friend/collab-quests/{existing_quest.quest_id}/accept",
        headers={"Authorization": f"Bearer {player_b_token}"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == PlayerErrorCodes.COLLAB_QUEST_NOT_PENDING
