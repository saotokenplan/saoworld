"""Content service edge-case tests.

Covers:
1. Gray scope boundary tests (player_id filtering, player_percent boundaries, region_ids edge cases)
2. Invalid status transition tests (rolled_back terminal state, archived terminal state)
3. Duplicate content package creation
4. Vote cycle query boundary tests (empty list, non-existent IDs)
5. Content update visibility tests (archived/rolled_back not visible to players)
6. Pagination edge cases (offset beyond total, limit=0, limit>100)
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.db import Base, get_db
from app.core.errors import ContentErrorCodes
from app.domain.models import ContentPackage
from app.repositories.content_repo import ContentRepository, is_player_in_gray_scope


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_test_db_with_packages(
    packages: list[ContentPackage],
):
    """Create an isolated in-memory SQLite DB, insert packages, and return
    (engine, TestSession) so the caller can set up dependency overrides."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///file:testdb_edge?mode=memory&cache=shared&uri=true",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    TestSession = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSession() as session:
        for pkg in packages:
            session.add(pkg)
        await session.commit()

    return engine, TestSession


# ===========================================================================
# 1. Gray scope boundary tests
# ===========================================================================


class TestGrayScopeBoundary:
    """Tests for is_player_in_gray_scope covering player_id, player_percent,
    and region_ids boundary conditions."""

    def test_player_id_exact_match(self):
        """Player ID present in player_ids list returns True."""
        pid = "00000000-0000-0000-0000-000000000001"
        scope = {"player_ids": [pid]}
        assert is_player_in_gray_scope(scope, pid) is True

    def test_player_id_no_match(self):
        """Player ID not in player_ids list returns False."""
        scope = {"player_ids": ["aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"]}
        assert is_player_in_gray_scope(scope, "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb") is False

    def test_player_id_empty_list(self):
        """Empty player_ids list falls through to other criteria."""
        pid = "00000000-0000-0000-0000-000000000001"
        scope = {"player_ids": []}
        # Falls through to player_percent / region_ids — none present => False
        assert is_player_in_gray_scope(scope, pid) is False

    def test_player_percent_zero_excludes_all(self):
        """player_percent=0 excludes every player (0 < percent is False)."""
        scope = {"player_percent": 0}
        assert is_player_in_gray_scope(scope, "any-player-id") is False

    def test_player_percent_100_includes_all(self):
        """player_percent=100 includes every player (bucket always <= 100)."""
        scope = {"player_percent": 100}
        assert is_player_in_gray_scope(scope, "any-player-id") is True

    def test_player_percent_negative_excludes(self):
        """Negative player_percent is not in (0, 100] range so returns False."""
        scope = {"player_percent": -5}
        assert is_player_in_gray_scope(scope, "any-player-id") is False

    def test_player_percent_over_100_excludes(self):
        """player_percent > 100 fails the (0 < percent <= 100) check,
        so it falls through to region_ids and returns False."""
        scope = {"player_percent": 150}
        assert is_player_in_gray_scope(scope, "any-player-id") is False

    def test_player_percent_non_numeric_excludes(self):
        """Non-numeric player_percent falls through to region_ids."""
        scope = {"player_percent": "all"}
        assert is_player_in_gray_scope(scope, "any-player-id") is False

    def test_region_ids_match(self):
        """Player region in region_ids list returns True."""
        scope = {"region_ids": ["region_wasteland_01", "region_forest_01"]}
        assert is_player_in_gray_scope(scope, "player-001", "region_wasteland_01") is True

    def test_region_ids_no_match(self):
        """Player region not in region_ids list returns False."""
        scope = {"region_ids": ["region_wasteland_01"]}
        assert is_player_in_gray_scope(scope, "player-001", "region_desert_01") is False

    def test_region_ids_empty_list(self):
        """Empty region_ids list falls through — no region match."""
        scope = {"region_ids": []}
        assert is_player_in_gray_scope(scope, "player-001", "region_wasteland_01") is False

    def test_region_ids_player_has_no_region(self):
        """When region_ids are set but player_region_id is None, returns False."""
        scope = {"region_ids": ["region_wasteland_01"]}
        assert is_player_in_gray_scope(scope, "player-001", None) is False

    def test_player_ids_takes_priority_over_percent_and_region(self):
        """When player_ids is non-empty, it takes priority; percent & region are ignored."""
        pid_in = "player-in-list"
        scope = {
            "player_ids": [pid_in],
            "player_percent": 0,
            "region_ids": ["region_99"],
        }
        # player-001 is NOT in player_ids -> False (even if region matched)
        assert is_player_in_gray_scope(scope, "player-001", "region_99") is False
        # pid_in IS in player_ids -> True (even though percent=0)
        assert is_player_in_gray_scope(scope, pid_in, "region_99") is True

    def test_none_gray_scope_returns_false(self):
        """None gray_scope always returns False."""
        assert is_player_in_gray_scope(None, "any-player") is False

    def test_empty_gray_scope_returns_false(self):
        """Empty dict gray_scope returns False."""
        assert is_player_in_gray_scope({}, "any-player") is False


# ===========================================================================
# 2. Invalid status transition tests (terminal states)
# ===========================================================================


class TestInvalidStatusTransitions:
    """Tests verifying that terminal states (rolled_back, archived) reject
    release and rollback operations."""

    @pytest.mark.asyncio
    async def test_rolled_back_cannot_release_gray(
        self, client: AsyncClient, ops_token: str, content_packages
    ):
        """A rolled_back package cannot be released as gray (terminal state)."""
        rolled_back_pkg = next(p for p in content_packages if p.status == "rolled_back")
        response = await client.post(
            f"/api/v1/ops/content-packages/{rolled_back_pkg.content_package_id}/release",
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": "edge-release-rolled-back-gray",
            },
            json={"release_mode": "gray", "reason": "should fail"},
        )
        assert response.status_code == 409
        assert response.json()["code"] == ContentErrorCodes.INVALID_PACKAGE_STATE

    @pytest.mark.asyncio
    async def test_rolled_back_cannot_release_full(
        self, client: AsyncClient, ops_token: str, content_packages
    ):
        """A rolled_back package cannot be fully released (terminal state)."""
        rolled_back_pkg = next(p for p in content_packages if p.status == "rolled_back")
        response = await client.post(
            f"/api/v1/ops/content-packages/{rolled_back_pkg.content_package_id}/release",
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": "edge-release-rolled-back-full",
            },
            json={"release_mode": "full", "reason": "should fail"},
        )
        assert response.status_code == 409
        assert response.json()["code"] == ContentErrorCodes.INVALID_PACKAGE_STATE

    @pytest.mark.asyncio
    async def test_rolled_back_cannot_rollback_again(
        self, client: AsyncClient, ops_token: str, content_packages
    ):
        """A rolled_back package cannot be rolled back again (terminal state)."""
        rolled_back_pkg = next(p for p in content_packages if p.status == "rolled_back")
        response = await client.post(
            f"/api/v1/ops/content-packages/{rolled_back_pkg.content_package_id}/rollback",
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": "edge-rollback-rolled-back-again",
            },
            json={"target_version": "v0.9.0", "reason": "should fail"},
        )
        assert response.status_code == 409
        assert response.json()["code"] == ContentErrorCodes.INVALID_PACKAGE_STATE

    @pytest.mark.asyncio
    async def test_archived_cannot_release(
        self, client: AsyncClient, ops_token: str
    ):
        """An archived package cannot be released (archived is a terminal state)."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///file:testdb_archived?mode=memory&cache=shared&uri=true",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        TestSession = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        pkg_id = uuid.uuid4()
        async with TestSession() as session:
            pkg = ContentPackage(
                content_package_id=pkg_id,
                chapter_id="chapter_01",
                package_version="pkg_archived_01",
                title="已归档内容包",
                status="archived",
                payload_jsonb={"test": "archived"},
            )
            session.add(pkg)
            await session.commit()

        from app.main import app

        async def override_db():
            async with TestSession() as s:
                yield s

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post(
                f"/api/v1/ops/content-packages/{pkg_id}/release",
                headers={
                    "Authorization": f"Bearer {ops_token}",
                    "Idempotency-Key": "edge-release-archived",
                },
                json={"release_mode": "gray", "reason": "should fail"},
            )
            assert response.status_code == 409
            assert response.json()["code"] == ContentErrorCodes.INVALID_PACKAGE_STATE
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_archived_cannot_rollback(
        self, client: AsyncClient, ops_token: str
    ):
        """An archived package cannot be rolled back (archived -> rolled_back not allowed)."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///file:testdb_archived_rb?mode=memory&cache=shared&uri=true",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        TestSession = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        pkg_id = uuid.uuid4()
        async with TestSession() as session:
            pkg = ContentPackage(
                content_package_id=pkg_id,
                chapter_id="chapter_01",
                package_version="pkg_archived_rb_01",
                title="已归档不可回滚包",
                status="archived",
                payload_jsonb={"test": "archived-rollback"},
            )
            session.add(pkg)
            await session.commit()

        from app.main import app

        async def override_db():
            async with TestSession() as s:
                yield s

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.post(
                f"/api/v1/ops/content-packages/{pkg_id}/rollback",
                headers={
                    "Authorization": f"Bearer {ops_token}",
                    "Idempotency-Key": "edge-rollback-archived",
                },
                json={"target_version": "v0.9.0", "reason": "should fail"},
            )
            assert response.status_code == 409
            assert response.json()["code"] == ContentErrorCodes.INVALID_PACKAGE_STATE
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_packaged_cannot_rollback(
        self, client: AsyncClient, ops_token: str, content_packages
    ):
        """A packaged (never released) package cannot be rolled back."""
        packaged_pkg = next(p for p in content_packages if p.status == "packaged")
        response = await client.post(
            f"/api/v1/ops/content-packages/{packaged_pkg.content_package_id}/rollback",
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": "edge-rollback-packaged",
            },
            json={"target_version": "v0.9.0", "reason": "should fail"},
        )
        assert response.status_code == 409
        assert response.json()["code"] == ContentErrorCodes.INVALID_PACKAGE_STATE

    def test_valid_transitions_table(self):
        """Verify VALID_TRANSITIONS mapping matches the state machine spec."""
        from app.repositories.content_repo import VALID_TRANSITIONS

        assert VALID_TRANSITIONS == {
            "packaged": {"gray"},
            "gray": {"live", "rolled_back"},
            "live": {"archived", "rolled_back"},
            "archived": set(),
            "rolled_back": set(),
        }


# ===========================================================================
# 3. Duplicate content package creation
# ===========================================================================


class TestDuplicatePackageCreation:
    """Tests for creating content packages with the same version/chapter_id.
    The service currently does NOT enforce uniqueness on package_version,
    so both creations should succeed independently."""

    @pytest.mark.asyncio
    async def test_create_package_same_version_succeeds(
        self, client: AsyncClient, ops_token: str
    ):
        """Creating two packages with the same package_version should both succeed
        (no unique constraint on package_version alone)."""
        payload = {
            "chapter_id": "chapter_01",
            "package_version": "pkg_ch01_20260701_dup",
            "title": "重复版本测试包1",
            "payload": {"test": "dup1"},
        }
        headers = {
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "edge-dup-create-1",
            "X-Trace-Id": "trace_dup_1",
        }
        resp1 = await client.post(
            "/api/v1/ops/content-packages", headers=headers, json=payload
        )
        assert resp1.status_code == 201
        pkg1_id = resp1.json()["data"]["content_package_id"]

        headers2 = {
            "Authorization": f"Bearer {ops_token}",
            "Idempotency-Key": "edge-dup-create-2",
            "X-Trace-Id": "trace_dup_2",
        }
        resp2 = await client.post(
            "/api/v1/ops/content-packages", headers=headers2, json=payload
        )
        assert resp2.status_code == 201
        pkg2_id = resp2.json()["data"]["content_package_id"]

        # They should be different packages with different IDs
        assert pkg1_id != pkg2_id

    @pytest.mark.asyncio
    async def test_create_package_same_chapter_and_version(
        self, client: AsyncClient, ops_token: str
    ):
        """Creating two packages with same chapter_id AND package_version succeeds
        (no composite unique constraint)."""
        for i in range(2):
            response = await client.post(
                "/api/v1/ops/content-packages",
                headers={
                    "Authorization": f"Bearer {ops_token}",
                    "Idempotency-Key": f"edge-dup-chapver-{i}",
                },
                json={
                    "chapter_id": "chapter_99",
                    "package_version": "pkg_ch99_20260701_01",
                    "title": f"重复章节版本测试{i}",
                    "payload": {"dup": True},
                },
            )
            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_idempotency_key_prevents_true_duplicate(
        self, client: AsyncClient, ops_token: str
    ):
        """While same business data is allowed, the Idempotency-Key header
        is required but doesn't prevent separate calls with different keys."""
        # The service requires Idempotency-Key but does not store/deduplicate by it
        # in the current implementation, so different keys with same payload create
        # separate packages. This test documents that behavior.
        base_payload = {
            "chapter_id": "chapter_50",
            "package_version": "pkg_idem_test",
            "title": "幂等测试",
            "payload": {"idem": True},
        }
        resp1 = await client.post(
            "/api/v1/ops/content-packages",
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": "edge-idem-key-A",
            },
            json=base_payload,
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            "/api/v1/ops/content-packages",
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": "edge-idem-key-B",
            },
            json=base_payload,
        )
        assert resp2.status_code == 201

        # Different content_package_ids confirm they are distinct records
        assert resp1.json()["data"]["content_package_id"] != resp2.json()["data"]["content_package_id"]


# ===========================================================================
# 4. Vote cycle query boundary tests
# ===========================================================================


class TestVoteCycleQueryBoundary:
    """Tests for vote-cycle-based package queries with edge-case inputs."""

    @pytest.mark.asyncio
    async def test_get_packages_by_vote_cycle_ids_empty_list(self):
        """Passing an empty vote_cycle_ids list returns an empty list."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///file:testdb_vc_empty?mode=memory&cache=shared&uri=true",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        TestSession = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with TestSession() as session:
            repo = ContentRepository(session)
            results = await repo.get_packages_by_vote_cycle_ids([])
            assert results == []

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_get_packages_by_vote_cycle_ids_nonexistent(self):
        """Querying non-existent vote_cycle_ids returns an empty list."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///file:testdb_vc_nonexist?mode=memory&cache=shared&uri=true",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        TestSession = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with TestSession() as session:
            repo = ContentRepository(session)
            results = await repo.get_packages_by_vote_cycle_ids([uuid.uuid4(), uuid.uuid4()])
            assert results == []

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_get_package_by_vote_cycle_api_invalid_uuid(
        self, client: AsyncClient, player_token: str
    ):
        """Passing an invalid UUID format for vote_cycle_id returns 422."""
        response = await client.get(
            "/api/v1/content/packages/by-vote-cycle/not-a-uuid",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_package_by_vote_cycle_api_nonexistent(
        self, client: AsyncClient, player_token: str
    ):
        """Querying a valid but non-existent vote_cycle_id returns 404."""
        fake_vote_cycle_id = uuid.uuid4()
        response = await client.get(
            f"/api/v1/content/packages/by-vote-cycle/{fake_vote_cycle_id}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 404
        assert response.json()["code"] == ContentErrorCodes.PACKAGE_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_packages_by_vote_cycle_ids_partial_match(self):
        """When some vote_cycle_ids match and some don't, only matching ones return."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///file:testdb_vc_partial?mode=memory&cache=shared&uri=true",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        TestSession = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        vc_id_match = uuid.uuid4()
        vc_id_no_match = uuid.uuid4()

        async with TestSession() as session:
            pkg = ContentPackage(
                content_package_id=uuid.uuid4(),
                chapter_id="chapter_01",
                package_version="pkg_partial_01",
                source_vote_cycle_id=vc_id_match,
                title="部分匹配测试包",
                status="live",
                payload_jsonb={"test": "partial"},
                released_at=datetime.now(timezone.utc),
            )
            session.add(pkg)
            await session.commit()

        async with TestSession() as session:
            repo = ContentRepository(session)
            results = await repo.get_packages_by_vote_cycle_ids([vc_id_match, vc_id_no_match])
            assert len(results) == 1
            assert results[0].source_vote_cycle_id == vc_id_match

        await engine.dispose()


# ===========================================================================
# 5. Content update visibility tests
# ===========================================================================


class TestContentUpdateVisibility:
    """Tests ensuring that archived and rolled_back packages are not visible
    to players through the content updates listing API."""

    @pytest.mark.asyncio
    async def test_rolled_back_not_in_updates(
        self, client: AsyncClient, player_token: str, content_packages
    ):
        """Rolled_back packages should not appear in the player-visible updates list."""
        response = await client.get(
            "/api/v1/content/updates",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        for pkg in data["data"]["packages"]:
            assert pkg["status"] != "rolled_back"

    @pytest.mark.asyncio
    async def test_archived_not_in_updates(
        self, client: AsyncClient, player_token: str
    ):
        """Archived packages should not appear in the player-visible updates list."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///file:testdb_vis_archived?mode=memory&cache=shared&uri=true",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        TestSession = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with TestSession() as session:
            pkg = ContentPackage(
                content_package_id=uuid.uuid4(),
                chapter_id="chapter_01",
                package_version="pkg_vis_archived_01",
                title="归档不可见测试包",
                status="archived",
                payload_jsonb={"test": "archived_vis"},
            )
            session.add(pkg)
            await session.commit()

        from app.main import app

        async def override_db():
            async with TestSession() as s:
                yield s

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.get(
                "/api/v1/content/updates",
                headers={"Authorization": f"Bearer {player_token}"},
            )
            assert response.status_code == 200
            data = response.json()
            for pkg in data["data"]["packages"]:
                assert pkg["status"] != "archived"
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_packaged_not_in_updates(
        self, client: AsyncClient, player_token: str, content_packages
    ):
        """Packaged (not yet released) packages should not appear in the updates list."""
        response = await client.get(
            "/api/v1/content/updates",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        for pkg in data["data"]["packages"]:
            assert pkg["status"] != "packaged"

    @pytest.mark.asyncio
    async def test_rolled_back_detail_hidden_from_player(
        self, client: AsyncClient, player_token: str, content_packages
    ):
        """A player requesting detail of a rolled_back package gets 404."""
        rolled_back_pkg = next(p for p in content_packages if p.status == "rolled_back")
        response = await client.get(
            f"/api/v1/content/packages/{rolled_back_pkg.content_package_id}",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 404
        assert response.json()["code"] == ContentErrorCodes.PACKAGE_NOT_FOUND

    @pytest.mark.asyncio
    async def test_rolled_back_detail_visible_to_ops(
        self, client: AsyncClient, ops_token: str, content_packages
    ):
        """An ops user can view detail of a rolled_back package."""
        rolled_back_pkg = next(p for p in content_packages if p.status == "rolled_back")
        response = await client.get(
            f"/api/v1/content/packages/{rolled_back_pkg.content_package_id}",
            headers={"Authorization": f"Bearer {ops_token}"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "rolled_back"

    @pytest.mark.asyncio
    async def test_archived_detail_hidden_from_player(
        self, client: AsyncClient, player_token: str
    ):
        """A player requesting detail of an archived package gets 404."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///file:testdb_vis_archived_det?mode=memory&cache=shared&uri=true",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        TestSession = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        pkg_id = uuid.uuid4()
        async with TestSession() as session:
            pkg = ContentPackage(
                content_package_id=pkg_id,
                chapter_id="chapter_01",
                package_version="pkg_archived_det_01",
                title="归档详情不可见包",
                status="archived",
                payload_jsonb={"test": "archived_detail"},
            )
            session.add(pkg)
            await session.commit()

        from app.main import app

        async def override_db():
            async with TestSession() as s:
                yield s

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.get(
                f"/api/v1/content/packages/{pkg_id}",
                headers={"Authorization": f"Bearer {player_token}"},
            )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()

    @pytest.mark.asyncio
    async def test_archived_detail_visible_to_ops(
        self, client: AsyncClient, ops_token: str
    ):
        """An ops user can view detail of an archived package."""
        engine = create_async_engine(
            "sqlite+aiosqlite:///file:testdb_vis_archived_ops?mode=memory&cache=shared&uri=true",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        TestSession = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        pkg_id = uuid.uuid4()
        async with TestSession() as session:
            pkg = ContentPackage(
                content_package_id=pkg_id,
                chapter_id="chapter_01",
                package_version="pkg_archived_ops_01",
                title="归档ops可见包",
                status="archived",
                payload_jsonb={"test": "archived_ops"},
            )
            session.add(pkg)
            await session.commit()

        from app.main import app

        async def override_db():
            async with TestSession() as s:
                yield s

        app.dependency_overrides[get_db] = override_db
        try:
            response = await client.get(
                f"/api/v1/content/packages/{pkg_id}",
                headers={"Authorization": f"Bearer {ops_token}"},
            )
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "archived"
        finally:
            app.dependency_overrides.clear()
            await engine.dispose()


# ===========================================================================
# 6. Pagination edge cases
# ===========================================================================


class TestPaginationEdgeCases:
    """Tests for pagination boundary conditions on the content updates endpoint."""

    @pytest.mark.asyncio
    async def test_offset_beyond_total_returns_empty(
        self, client: AsyncClient, player_token: str, content_packages
    ):
        """When offset >= total, the result list should be empty but total still accurate."""
        response = await client.get(
            "/api/v1/content/updates?offset=9999&limit=20",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["packages"] == []
        assert data["meta"]["total"] >= 0

    @pytest.mark.asyncio
    async def test_limit_zero_rejected(self, client: AsyncClient, player_token: str):
        """limit=0 should be rejected by the API (ge=1 constraint)."""
        response = await client.get(
            "/api/v1/content/updates?limit=0",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_exceeds_100_rejected(self, client: AsyncClient, player_token: str):
        """limit > 100 should be rejected by the API (le=100 constraint)."""
        response = await client.get(
            "/api/v1/content/updates?limit=101",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_offset_negative_rejected(self, client: AsyncClient, player_token: str):
        """Negative offset should be rejected by the API (ge=0 constraint)."""
        response = await client.get(
            "/api/v1/content/updates?offset=-1",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_limit_exactly_100_accepted(
        self, client: AsyncClient, player_token: str, content_packages
    ):
        """limit=100 is the maximum allowed value and should be accepted."""
        response = await client.get(
            "/api/v1/content/updates?limit=100",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        assert response.json()["meta"]["limit"] == 100

    @pytest.mark.asyncio
    async def test_limit_exactly_1_accepted(
        self, client: AsyncClient, player_token: str, content_packages
    ):
        """limit=1 is the minimum allowed value and should be accepted."""
        response = await client.get(
            "/api/v1/content/updates?limit=1",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        assert response.json()["meta"]["limit"] == 1
        assert len(response.json()["data"]["packages"]) <= 1

    @pytest.mark.asyncio
    async def test_offset_zero_default(
        self, client: AsyncClient, player_token: str, content_packages
    ):
        """When offset is not specified, it defaults to 0."""
        response = await client.get(
            "/api/v1/content/updates",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        assert response.json()["meta"]["offset"] == 0

    @pytest.mark.asyncio
    async def test_offset_at_total_returns_empty(
        self, client: AsyncClient, player_token: str, content_packages
    ):
        """When offset equals the total number of visible packages, result is empty."""
        # First, get total
        response = await client.get(
            "/api/v1/content/updates?limit=100",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        total = response.json()["meta"]["total"]

        # Then query with offset = total
        response2 = await client.get(
            f"/api/v1/content/updates?offset={total}&limit=20",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response2.status_code == 200
        assert response2.json()["data"]["packages"] == []
        assert response2.json()["meta"]["total"] == total

    @pytest.mark.asyncio
    async def test_pagination_consistent_results(
        self, client: AsyncClient, player_token: str, content_packages
    ):
        """Paginating through all results yields the same set as a single query."""
        all_resp = await client.get(
            "/api/v1/content/updates?limit=100",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        all_ids = [p["content_package_id"] for p in all_resp.json()["data"]["packages"]]

        page1 = await client.get(
            "/api/v1/content/updates?limit=2&offset=0",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        page1_ids = [p["content_package_id"] for p in page1.json()["data"]["packages"]]

        page2 = await client.get(
            "/api/v1/content/updates?limit=2&offset=2",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        page2_ids = [p["content_package_id"] for p in page2.json()["data"]["packages"]]

        combined = page1_ids + page2_ids
        # All paginated IDs should appear in the full result
        for cid in combined:
            assert cid in all_ids
