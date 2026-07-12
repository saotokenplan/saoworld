import uuid
from datetime import datetime, timedelta, timezone

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.auth import create_test_token
from app.domain.models import VoteCandidate, VoteCycle, VoteDiscussion
from app.schemas.auth import Role
from tests.conftest import TestSessionLocal


PLAYER1_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
PLAYER2_ID = "b2c3d4e5-f6a7-8901-bcde-f12345678901"


@pytest_asyncio.fixture
def player1_token() -> str:
    return create_test_token(
        user_id=PLAYER1_ID,
        role=Role.PLAYER,
    )


@pytest_asyncio.fixture
def player2_token() -> str:
    return create_test_token(
        user_id=PLAYER2_ID,
        role=Role.PLAYER,
    )


@pytest_asyncio.fixture
async def open_vote_cycle_with_discussions() -> VoteCycle:
    now = datetime.now(timezone.utc)
    cycle_id = uuid.uuid4()
    candidates = [
        VoteCandidate(
            candidate_id=uuid.uuid4(),
            vote_cycle_id=cycle_id,
            title="候选A",
            summary="候选A摘要",
            status="active",
        ),
        VoteCandidate(
            candidate_id=uuid.uuid4(),
            vote_cycle_id=cycle_id,
            title="候选B",
            summary="候选B摘要",
            status="active",
        ),
    ]
    cycle = VoteCycle(
        vote_cycle_id=cycle_id,
        chapter_id="ch_test_01",
        status="open",
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(hours=23),
        created_by="system",
        created_reason="test cycle",
        candidates=candidates,
    )

    discussions = [
        VoteDiscussion(
            discussion_id=uuid.uuid4(),
            vote_cycle_id=cycle_id,
            player_id=uuid.UUID(PLAYER1_ID),
            content="这是第一条讨论",
            like_count=5,
            reply_count=2,
            status="active",
        ),
        VoteDiscussion(
            discussion_id=uuid.uuid4(),
            vote_cycle_id=cycle_id,
            player_id=uuid.UUID(PLAYER2_ID),
            content="这是第二条讨论，热度更高",
            like_count=15,
            reply_count=5,
            status="active",
        ),
    ]

    async with TestSessionLocal() as session:
        session.add(cycle)
        session.add_all(discussions)
        await session.commit()

        stmt = (
            select(VoteCycle)
            .options(selectinload(VoteCycle.candidates))
            .where(VoteCycle.vote_cycle_id == cycle_id)
        )
        result = await session.execute(stmt)
        loaded_cycle = result.scalar_one()
        _ = [c.candidate_id for c in loaded_cycle.candidates]
        return loaded_cycle


class TestListDiscussions:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, setup_db):
        yield

    async def test_list_discussions_success(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        response = await client.get(
            f"/api/v1/votes/discussions/{open_vote_cycle_with_discussions.vote_cycle_id}",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["discussions"] is not None
        assert len(data["data"]["discussions"]) == 2
        assert data["meta"]["total"] == 2

    async def test_list_discussions_sorted_by_time(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        response = await client.get(
            f"/api/v1/votes/discussions/{open_vote_cycle_with_discussions.vote_cycle_id}",
            params={"sort_by": "time"},
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        discussions = data["data"]["discussions"]
        assert len(discussions) == 2
        assert discussions[0]["created_at"] >= discussions[1]["created_at"]

    async def test_list_discussions_sorted_by_hot(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        response = await client.get(
            f"/api/v1/votes/discussions/{open_vote_cycle_with_discussions.vote_cycle_id}",
            params={"sort_by": "hot"},
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        discussions = data["data"]["discussions"]
        assert len(discussions) == 2
        assert discussions[0]["like_count"] >= discussions[1]["like_count"]

    async def test_list_discussions_pagination(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        response = await client.get(
            f"/api/v1/votes/discussions/{open_vote_cycle_with_discussions.vote_cycle_id}",
            params={"limit": 1, "offset": 0},
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["discussions"]) == 1
        assert data["meta"]["total"] == 2
        assert data["meta"]["limit"] == 1
        assert data["meta"]["offset"] == 0

    async def test_list_discussions_cycle_not_found(
        self,
        client: AsyncClient,
        player1_token: str,
    ):
        fake_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/votes/discussions/{fake_id}",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "VOTE_CYCLE_NOT_FOUND"

    async def test_list_discussions_without_token(
        self,
        client: AsyncClient,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        response = await client.get(
            f"/api/v1/votes/discussions/{open_vote_cycle_with_discussions.vote_cycle_id}",
        )
        assert response.status_code == 401


class TestCreateDiscussion:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, setup_db):
        yield

    async def test_create_discussion_success(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle: VoteCycle,
    ):
        response = await client.post(
            f"/api/v1/votes/discussions/{open_vote_cycle.vote_cycle_id}",
            json={"content": "这是一条新讨论"},
            headers={
                "Authorization": f"Bearer {player1_token}",
                "X-Trace-Id": "trace_test_001",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["content"] == "这是一条新讨论"
        assert data["data"]["status"] == "active"
        assert data["data"]["like_count"] == 0
        assert data["data"]["reply_count"] == 0
        assert data["data"]["has_liked"] is False

    async def test_create_discussion_content_too_long(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle: VoteCycle,
    ):
        long_content = "a" * 501
        response = await client.post(
            f"/api/v1/votes/discussions/{open_vote_cycle.vote_cycle_id}",
            json={"content": long_content},
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 422

    async def test_create_discussion_cycle_not_found(
        self,
        client: AsyncClient,
        player1_token: str,
    ):
        fake_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/votes/discussions/{fake_id}",
            json={"content": "测试讨论"},
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 404

    async def test_create_discussion_without_token(
        self,
        client: AsyncClient,
        open_vote_cycle: VoteCycle,
    ):
        response = await client.post(
            f"/api/v1/votes/discussions/{open_vote_cycle.vote_cycle_id}",
            json={"content": "测试讨论"},
        )
        assert response.status_code == 401


class TestLikeDiscussion:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, setup_db):
        yield

    async def test_like_discussion_success(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=1)
            discussion_id = discussions[0].discussion_id
            initial_likes = discussions[0].like_count

        response = await client.post(
            f"/api/v1/votes/discussions/{discussion_id}/like",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["liked"] is True
        assert data["data"]["like_count"] == initial_likes + 1

    async def test_like_discussion_duplicate(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=1)
            discussion_id = discussions[0].discussion_id

        await client.post(
            f"/api/v1/votes/discussions/{discussion_id}/like",
            headers={"Authorization": f"Bearer {player1_token}"},
        )

        response = await client.post(
            f"/api/v1/votes/discussions/{discussion_id}/like",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["liked"] is False

    async def test_like_discussion_not_found(
        self,
        client: AsyncClient,
        player1_token: str,
    ):
        fake_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/votes/discussions/{fake_id}/like",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 404


class TestUnlikeDiscussion:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, setup_db):
        yield

    async def test_unlike_discussion_success(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=1)
            discussion_id = discussions[0].discussion_id

        await client.post(
            f"/api/v1/votes/discussions/{discussion_id}/like",
            headers={"Authorization": f"Bearer {player1_token}"},
        )

        response = await client.post(
            f"/api/v1/votes/discussions/{discussion_id}/unlike",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["liked"] is False

    async def test_unlike_discussion_not_liked(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=1)
            discussion_id = discussions[0].discussion_id

        response = await client.post(
            f"/api/v1/votes/discussions/{discussion_id}/unlike",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["liked"] is True


class TestDeleteDiscussion:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, setup_db):
        yield

    async def test_delete_own_discussion_success(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=10)
            player1_discussion = None
            for d in discussions:
                if d.player_id == uuid.UUID(PLAYER1_ID):
                    player1_discussion = d
                    break
            assert player1_discussion is not None
            discussion_id = player1_discussion.discussion_id

        response = await client.delete(
            f"/api/v1/votes/discussions/{discussion_id}",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "deleted"

    async def test_delete_other_discussion_forbidden(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=10)
            player2_discussion = None
            for d in discussions:
                if d.player_id == uuid.UUID(PLAYER2_ID):
                    player2_discussion = d
                    break
            assert player2_discussion is not None
            discussion_id = player2_discussion.discussion_id

        response = await client.delete(
            f"/api/v1/votes/discussions/{discussion_id}",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 403

    async def test_delete_discussion_not_found(
        self,
        client: AsyncClient,
        player1_token: str,
    ):
        fake_id = uuid.uuid4()
        response = await client.delete(
            f"/api/v1/votes/discussions/{fake_id}",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 404


class TestReplies:
    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, setup_db):
        yield

    async def test_create_reply_success(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=1)
            discussion_id = discussions[0].discussion_id
            initial_reply_count = discussions[0].reply_count

        response = await client.post(
            f"/api/v1/votes/discussions/{discussion_id}/replies",
            json={"content": "这是一条回复"},
            headers={
                "Authorization": f"Bearer {player1_token}",
                "X-Trace-Id": "trace_reply_001",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["data"]["content"] == "这是一条回复"
        assert data["data"]["status"] == "active"
        assert data["data"]["discussion_id"] == str(discussion_id)

        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            updated = await repo.get_discussion(discussion_id)
            assert updated is not None
            assert updated.reply_count == initial_reply_count + 1

    async def test_list_replies_success(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=1)
            discussion_id = discussions[0].discussion_id

            await repo.create_reply(
                discussion_id=discussion_id,
                player_id=uuid.UUID(PLAYER1_ID),
                content="回复1",
            )
            await repo.create_reply(
                discussion_id=discussion_id,
                player_id=uuid.UUID(PLAYER2_ID),
                content="回复2",
            )
            await session.commit()

        response = await client.get(
            f"/api/v1/votes/discussions/{discussion_id}/replies",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["replies"]) == 2
        assert data["meta"]["total"] == 2

    async def test_create_reply_discussion_not_found(
        self,
        client: AsyncClient,
        player1_token: str,
    ):
        fake_id = uuid.uuid4()
        response = await client.post(
            f"/api/v1/votes/discussions/{fake_id}/replies",
            json={"content": "测试回复"},
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 404

    async def test_like_reply_success(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=1)
            discussion_id = discussions[0].discussion_id
            reply = await repo.create_reply(
                discussion_id=discussion_id,
                player_id=uuid.UUID(PLAYER2_ID),
                content="测试回复",
            )
            await session.commit()
            reply_id = reply.reply_id

        response = await client.post(
            f"/api/v1/votes/replies/{reply_id}/like",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["liked"] is True
        assert data["data"]["like_count"] == 1

    async def test_delete_own_reply_success(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=1)
            discussion_id = discussions[0].discussion_id
            reply = await repo.create_reply(
                discussion_id=discussion_id,
                player_id=uuid.UUID(PLAYER1_ID),
                content="我的回复",
            )
            await session.commit()
            reply_id = reply.reply_id

        response = await client.delete(
            f"/api/v1/votes/replies/{reply_id}",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["status"] == "deleted"

    async def test_delete_other_reply_forbidden(
        self,
        client: AsyncClient,
        player1_token: str,
        open_vote_cycle_with_discussions: VoteCycle,
    ):
        cycle_id = open_vote_cycle_with_discussions.vote_cycle_id
        async with TestSessionLocal() as session:
            from app.repositories.discussion_repo import DiscussionRepository
            repo = DiscussionRepository(session)
            discussions, _ = await repo.list_discussions(cycle_id, limit=1)
            discussion_id = discussions[0].discussion_id
            reply = await repo.create_reply(
                discussion_id=discussion_id,
                player_id=uuid.UUID(PLAYER2_ID),
                content="别人的回复",
            )
            await session.commit()
            reply_id = reply.reply_id

        response = await client.delete(
            f"/api/v1/votes/replies/{reply_id}",
            headers={"Authorization": f"Bearer {player1_token}"},
        )
        assert response.status_code == 403
