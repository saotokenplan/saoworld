import uuid

import pytest
from httpx import AsyncClient

from app.core.errors import ContentErrorCodes


@pytest.mark.asyncio
async def test_list_content_updates_returns_visible_packages(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 3
    assert len(data["data"]["packages"]) == 3
    for pkg in data["data"]["packages"]:
        assert pkg["status"] in ("gray", "live")


@pytest.mark.asyncio
async def test_list_content_updates_envelope_format(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "meta" in data
    assert "packages" in data["data"]
    assert "total" in data["data"]


@pytest.mark.asyncio
async def test_list_content_updates_pagination(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates?limit=1&offset=0",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["packages"]) == 1
    assert data["meta"]["total"] == 3
    assert data["meta"]["limit"] == 1
    assert data["meta"]["offset"] == 0


@pytest.mark.asyncio
async def test_list_content_updates_pagination_offset(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates?limit=1&offset=2",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["packages"]) == 1
    assert data["meta"]["total"] == 3
    assert data["meta"]["offset"] == 2


@pytest.mark.asyncio
async def test_list_content_updates_filter_by_chapter(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates?chapter_id=chapter_01",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 2
    for pkg in data["data"]["packages"]:
        assert pkg["chapter_id"] == "chapter_01"


@pytest.mark.asyncio
async def test_list_content_updates_chapter_no_match(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates?chapter_id=chapter_nonexistent",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 0
    assert len(data["data"]["packages"]) == 0


@pytest.mark.asyncio
async def test_get_package_detail_found(
    client: AsyncClient, player_token: str, content_packages
):
    live_package = next(p for p in content_packages if p.status == "live")
    response = await client.get(
        f"/api/v1/content/packages/{live_package.content_package_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert str(data["data"]["content_package_id"]) == str(live_package.content_package_id)
    assert data["data"]["title"] == live_package.title
    assert data["data"]["status"] == live_package.status
    assert data["data"]["payload"] == live_package.payload_jsonb


@pytest.mark.asyncio
async def test_get_package_detail_not_found(
    client: AsyncClient, player_token: str
):
    fake_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/content/packages/{fake_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == ContentErrorCodes.PACKAGE_NOT_FOUND


@pytest.mark.asyncio
async def test_get_package_detail_packaged_hidden_from_player(
    client: AsyncClient, player_token: str, content_packages
):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.get(
        f"/api/v1/content/packages/{packaged_package.content_package_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_package_detail_rolled_back_hidden_from_player(
    client: AsyncClient, player_token: str, content_packages
):
    rolled_back_package = next(p for p in content_packages if p.status == "rolled_back")
    response = await client.get(
        f"/api/v1/content/packages/{rolled_back_package.content_package_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_package_detail_visible_to_ops(
    client: AsyncClient, ops_token: str, content_packages
):
    packaged_package = next(p for p in content_packages if p.status == "packaged")
    response = await client.get(
        f"/api/v1/content/packages/{packaged_package.content_package_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert str(data["data"]["content_package_id"]) == str(packaged_package.content_package_id)


@pytest.mark.asyncio
async def test_list_content_updates_with_trace_id(
    client: AsyncClient, player_token: str, content_packages
):
    trace_id = "trace_test_123"
    response = await client.get(
        "/api/v1/content/updates",
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Trace-Id": trace_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id


@pytest.mark.asyncio
async def test_list_content_updates_request_id_header(
    client: AsyncClient, player_token: str, content_packages
):
    response = await client.get(
        "/api/v1/content/updates",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert "X-Request-Id" in response.headers
    assert response.headers["X-Request-Id"].startswith("req_")


@pytest.mark.asyncio
async def test_get_package_detail_with_trace_id(
    client: AsyncClient, player_token: str, content_packages
):
    live_package = next(p for p in content_packages if p.status == "live")
    trace_id = "trace_detail_456"
    response = await client.get(
        f"/api/v1/content/packages/{live_package.content_package_id}",
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Trace-Id": trace_id,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["trace_id"] == trace_id


@pytest.mark.asyncio
async def test_gray_package_visible_to_player_in_scope(
    client: AsyncClient, content_packages
):
    from app.core.auth import create_test_token
    from app.schemas.auth import Role

    player_id_in_scope = "00000000-0000-0000-0000-000000000001"
    token = create_test_token(user_id=player_id_in_scope, role=Role.PLAYER)

    response = await client.get(
        "/api/v1/content/updates",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Player-Id": player_id_in_scope,
        },
    )
    assert response.status_code == 200
    data = response.json()
    statuses = [pkg["status"] for pkg in data["data"]["packages"]]
    assert "live" in statuses


@pytest.mark.asyncio
async def test_gray_package_hidden_from_player_not_in_scope(
    client: AsyncClient, content_packages
):
    from app.core.auth import create_test_token
    from app.schemas.auth import Role

    player_id_outside = "11111111-1111-1111-1111-111111111111"
    token = create_test_token(user_id=player_id_outside, role=Role.PLAYER)

    response = await client.get(
        "/api/v1/content/updates",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Player-Id": player_id_outside,
        },
    )
    assert response.status_code == 200
    data = response.json()
    statuses = [pkg["status"] for pkg in data["data"]["packages"]]
    assert "gray" not in statuses
    for pkg in data["data"]["packages"]:
        assert pkg["status"] == "live"


@pytest.mark.asyncio
async def test_gray_package_with_player_ids_whitelist(
    client: AsyncClient, content_packages
):
    from app.core.auth import create_test_token
    from app.core.db import get_db
    from app.domain.models import ContentPackage
    from app.schemas.auth import Role
    from datetime import datetime, timezone
    import uuid
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    allowed_player_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    other_player_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    test_engine = create_async_engine(
        "sqlite+aiosqlite:///file:testdb_gray?mode=memory&cache=shared&uri=true",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    TestSession = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )

    from app.core.db import Base
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        pkg = ContentPackage(
            content_package_id=uuid.uuid4(),
            chapter_id="chapter_03",
            package_version="pkg_test_gray_01",
            title="灰度白名单测试包",
            summary="测试玩家白名单灰度",
            status="gray",
            gray_scope_jsonb={"player_ids": [allowed_player_id]},
            payload_jsonb={"test": "gray_whitelist"},
            released_at=datetime.now(timezone.utc),
        )
        session.add(pkg)
        await session.commit()

    async def override_db():
        async with TestSession() as s:
            yield s

    from app.main import app
    app.dependency_overrides[get_db] = override_db

    try:
        allowed_token = create_test_token(user_id=allowed_player_id, role=Role.PLAYER)
        response = await client.get(
            "/api/v1/content/updates",
            headers={
                "Authorization": f"Bearer {allowed_token}",
                "X-Player-Id": allowed_player_id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        statuses = [pkg["status"] for pkg in data["data"]["packages"]]
        assert "gray" in statuses

        other_token = create_test_token(user_id=other_player_id, role=Role.PLAYER)
        response2 = await client.get(
            "/api/v1/content/updates",
            headers={
                "Authorization": f"Bearer {other_token}",
                "X-Player-Id": other_player_id,
            },
        )
        assert response2.status_code == 200
        data2 = response2.json()
        statuses2 = [pkg["status"] for pkg in data2["data"]["packages"]]
        assert "gray" not in statuses2
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()


def test_is_player_in_gray_scope_player_ids():
    from app.repositories.content_repo import is_player_in_gray_scope

    scope = {"player_ids": ["player-001", "player-002"]}
    assert is_player_in_gray_scope(scope, "player-001") is True
    assert is_player_in_gray_scope(scope, "player-003") is False


def test_is_player_in_gray_scope_empty():
    from app.repositories.content_repo import is_player_in_gray_scope

    assert is_player_in_gray_scope(None, "player-001") is False
    assert is_player_in_gray_scope({}, "player-001") is False


def test_is_player_in_gray_scope_region_ids():
    from app.repositories.content_repo import is_player_in_gray_scope

    scope = {"region_ids": ["region_01", "region_02"]}
    assert is_player_in_gray_scope(scope, "player-001", "region_01") is True
    assert is_player_in_gray_scope(scope, "player-001", "region_03") is False
    assert is_player_in_gray_scope(scope, "player-001", None) is False


def test_is_player_in_gray_scope_priority():
    from app.repositories.content_repo import is_player_in_gray_scope

    scope = {
        "player_ids": ["player-001"],
        "player_percent": 0,
        "region_ids": ["region_01"],
    }
    assert is_player_in_gray_scope(scope, "player-001", "region_99") is True
    assert is_player_in_gray_scope(scope, "player-002", "region_01") is False


@pytest.mark.asyncio
async def test_get_package_by_vote_cycle_found(
    client: AsyncClient, player_token: str, content_packages
):
    from app.core.db import get_db
    from app.domain.models import ContentPackage
    from datetime import datetime, timezone
    import uuid
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    test_vote_cycle_id = uuid.uuid4()

    test_engine = create_async_engine(
        "sqlite+aiosqlite:///file:testdb_vote_cycle?mode=memory&cache=shared&uri=true",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    TestSession = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )

    from app.core.db import Base
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        pkg = ContentPackage(
            content_package_id=uuid.uuid4(),
            chapter_id="chapter_01",
            package_version="pkg_test_vote_01",
            source_vote_cycle_id=test_vote_cycle_id,
            title="投票结果测试包",
            summary="测试投票结果落地",
            status="live",
            payload_jsonb={"regions": [{"name": "测试区域"}]},
            released_at=datetime.now(timezone.utc),
        )
        session.add(pkg)
        await session.commit()

    async def override_db():
        async with TestSession() as s:
            yield s

    from app.main import app
    app.dependency_overrides[get_db] = override_db

    try:
        response = await client.get(
            f"/api/v1/content/packages/by-vote-cycle/{test_vote_cycle_id}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "data" in data
        assert data["data"]["title"] == "投票结果测试包"
        assert data["data"]["source_vote_cycle_id"] == str(test_vote_cycle_id)
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_get_package_by_vote_cycle_not_found(
    client: AsyncClient, player_token: str
):
    non_existent_vote_cycle_id = uuid.uuid4()
    response = await client.get(
        f"/api/v1/content/packages/by-vote-cycle/{non_existent_vote_cycle_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "PACKAGE_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_package_by_vote_cycle_packaged_hidden_from_player(
    client: AsyncClient, player_token: str
):
    from app.core.db import get_db
    from app.domain.models import ContentPackage
    from datetime import datetime, timezone
    import uuid
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    test_vote_cycle_id = uuid.uuid4()

    test_engine = create_async_engine(
        "sqlite+aiosqlite:///file:testdb_vote_packaged?mode=memory&cache=shared&uri=true",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    TestSession = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
    )

    from app.core.db import Base
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        pkg = ContentPackage(
            content_package_id=uuid.uuid4(),
            chapter_id="chapter_01",
            package_version="pkg_test_packaged_01",
            source_vote_cycle_id=test_vote_cycle_id,
            title="打包状态测试包",
            summary="测试打包状态不可见",
            status="packaged",
            payload_jsonb={},
        )
        session.add(pkg)
        await session.commit()

    async def override_db():
        async with TestSession() as s:
            yield s

    from app.main import app
    app.dependency_overrides[get_db] = override_db

    try:
        response = await client.get(
            f"/api/v1/content/packages/by-vote-cycle/{test_vote_cycle_id}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "PACKAGE_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()
        await test_engine.dispose()



