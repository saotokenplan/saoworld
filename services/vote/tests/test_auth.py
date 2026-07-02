"""JWT 鉴权与权限校验测试。"""

import uuid

import pytest
from httpx import AsyncClient

from app.core.auth import create_test_token, decode_jwt_token
from app.schemas.auth import Role, Scope


class TestJWTToken:
    """JWT Token 解析测试。"""

    def test_decode_valid_token(self):
        """测试解析有效的 JWT Token。"""
        token = create_test_token(
            user_id="ops_user_001",
            role=Role.OPS,
        )
        token_data = decode_jwt_token(token)

        assert token_data.sub == "ops_user_001"
        assert token_data.role == Role.OPS
        assert Scope.OPS_VOTE_CYCLES_WRITE.value in token_data.scopes

    def test_decode_token_with_custom_scopes(self):
        """测试解析自定义 Scope 的 Token。"""
        token = create_test_token(
            user_id="custom_user",
            role=Role.PLAYER,
            scopes=["votes:read", "votes:submit"],
        )
        token_data = decode_jwt_token(token)

        assert token_data.sub == "custom_user"
        assert token_data.role == Role.PLAYER
        assert "votes:read" in token_data.scopes
        assert "votes:submit" in token_data.scopes

    def test_decode_invalid_token(self):
        """测试解析无效 Token 抛出错误。"""
        from app.core.auth import InvalidTokenError

        with pytest.raises(InvalidTokenError):
            decode_jwt_token("invalid_token_string")

    def test_decode_expired_token(self):
        """测试解析过期 Token 抛出错误。"""
        from app.core.auth import ExpiredTokenError, create_test_token

        # 创建一个已经过期的 Token（过期时间设为负数）
        token = create_test_token(
            user_id="expired_user",
            role=Role.OPS,
            expire_minutes=-10,
        )

        with pytest.raises(ExpiredTokenError):
            decode_jwt_token(token)


class TestAuthMiddleware:
    """鉴权中间件测试。"""

    @pytest.mark.asyncio
    async def test_ops_endpoint_without_token_returns_401(self, client: AsyncClient):
        """测试运营接口无 Token 返回 401。"""
        response = await client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_01",
                "starts_at": "2026-07-01T10:00:00Z",
                "ends_at": "2026-07-02T10:00:00Z",
                "reason": "测试投票周期",
                "candidates": [
                    {
                        "title": "选项 A",
                        "summary": "选项 A 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                    {
                        "title": "选项 B",
                        "summary": "选项 B 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                ],
            },
            headers={
                "Idempotency-Key": f"idem_{uuid.uuid4().hex[:12]}",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "MISSING_TOKEN"

    @pytest.mark.asyncio
    async def test_ops_endpoint_with_invalid_token_returns_401(self, client: AsyncClient):
        """测试运营接口无效 Token 返回 401。"""
        response = await client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_01",
                "starts_at": "2026-07-01T10:00:00Z",
                "ends_at": "2026-07-02T10:00:00Z",
                "reason": "测试投票周期",
                "candidates": [
                    {
                        "title": "选项 A",
                        "summary": "选项 A 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                    {
                        "title": "选项 B",
                        "summary": "选项 B 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                ],
            },
            headers={
                "Authorization": "Bearer invalid_token",
                "Idempotency-Key": f"idem_{uuid.uuid4().hex[:12]}",
            },
        )

        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "INVALID_TOKEN"

    @pytest.mark.asyncio
    async def test_ops_endpoint_with_player_token_returns_403(self, client: AsyncClient):
        """测试运营接口使用玩家 Token 返回 403。"""
        player_token = create_test_token(
            user_id="player_001",
            role=Role.PLAYER,
        )

        response = await client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_01",
                "starts_at": "2026-07-01T10:00:00Z",
                "ends_at": "2026-07-02T10:00:00Z",
                "reason": "测试投票周期",
                "candidates": [
                    {
                        "title": "选项 A",
                        "summary": "选项 A 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                    {
                        "title": "选项 B",
                        "summary": "选项 B 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                ],
            },
            headers={
                "Authorization": f"Bearer {player_token}",
                "Idempotency-Key": f"idem_{uuid.uuid4().hex[:12]}",
            },
        )

        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_ops_endpoint_with_ops_token_returns_success(self, client: AsyncClient):
        """测试运营接口使用 ops Token 正常工作。"""
        ops_token = create_test_token(
            user_id="ops_user_001",
            role=Role.OPS,
        )

        response = await client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_test_auth",
                "starts_at": "2026-07-01T10:00:00Z",
                "ends_at": "2026-07-02T10:00:00Z",
                "reason": "鉴权测试投票周期",
                "candidates": [
                    {
                        "title": "选项 A",
                        "summary": "选项 A 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                    {
                        "title": "选项 B",
                        "summary": "选项 B 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                ],
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"idem_auth_{uuid.uuid4().hex[:12]}",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["vote_cycle_id"] is not None
        assert data["chapter_id"] == "chapter_test_auth"

    @pytest.mark.asyncio
    async def test_ops_schedule_without_token_returns_401(self, client: AsyncClient):
        """测试 schedule 接口无 Token 返回 401。"""
        response = await client.post(
            "/api/v1/ops/vote-cycles/00000000-0000-0000-0000-000000000001/schedule",
            json={"reason": "测试"},
            headers={
                "Idempotency-Key": f"idem_{uuid.uuid4().hex[:12]}",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_ops_open_without_token_returns_401(self, client: AsyncClient):
        """测试 open 接口无 Token 返回 401。"""
        response = await client.post(
            "/api/v1/ops/vote-cycles/00000000-0000-0000-0000-000000000001/open",
            json={"reason": "测试"},
            headers={
                "Idempotency-Key": f"idem_{uuid.uuid4().hex[:12]}",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_ops_close_without_token_returns_401(self, client: AsyncClient):
        """测试 close 接口无 Token 返回 401。"""
        response = await client.post(
            "/api/v1/ops/vote-cycles/00000000-0000-0000-0000-000000000001/close",
            json={"reason": "测试"},
            headers={
                "Idempotency-Key": f"idem_{uuid.uuid4().hex[:12]}",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_ops_finalize_without_token_returns_401(self, client: AsyncClient):
        """测试 finalize 接口无 Token 返回 401。"""
        response = await client.post(
            "/api/v1/ops/vote-cycles/00000000-0000-0000-0000-000000000001/finalize",
            json={"reason": "测试"},
            headers={
                "Idempotency-Key": f"idem_{uuid.uuid4().hex[:12]}",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_full_lifecycle_with_auth(self, client: AsyncClient):
        """测试带鉴权的完整投票周期生命周期。"""
        ops_token = create_test_token(
            user_id="ops_lifecycle_user",
            role=Role.OPS,
        )

        # 1. 创建投票周期
        create_response = await client.post(
            "/api/v1/ops/vote-cycles",
            json={
                "chapter_id": "chapter_auth_lifecycle",
                "starts_at": "2026-07-01T10:00:00Z",
                "ends_at": "2026-07-02T10:00:00Z",
                "reason": "鉴权生命周期测试",
                "candidates": [
                    {
                        "title": "选项 A",
                        "summary": "选项 A 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                    {
                        "title": "选项 B",
                        "summary": "选项 B 概要",
                        "region_scope": [],
                        "risk_tags": [],
                    },
                ],
            },
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"idem_lifecycle_{uuid.uuid4().hex[:12]}",
            },
        )
        assert create_response.status_code == 201
        cycle_id = create_response.json()["vote_cycle_id"]

        # 2. schedule
        schedule_response = await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/schedule",
            json={"reason": "计划发布"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"idem_schedule_{uuid.uuid4().hex[:12]}",
            },
        )
        assert schedule_response.status_code == 200
        assert schedule_response.json()["status"] == "scheduled"

        # 3. open
        open_response = await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/open",
            json={"reason": "开放投票"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"idem_open_{uuid.uuid4().hex[:12]}",
            },
        )
        assert open_response.status_code == 200
        assert open_response.json()["status"] == "open"

        # 4. close
        close_response = await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/close",
            json={"reason": "关闭投票"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"idem_close_{uuid.uuid4().hex[:12]}",
            },
        )
        assert close_response.status_code == 200
        assert close_response.json()["status"] == "closed"

        # 5. finalize
        finalize_response = await client.post(
            f"/api/v1/ops/vote-cycles/{cycle_id}/finalize",
            json={"reason": "确认结果"},
            headers={
                "Authorization": f"Bearer {ops_token}",
                "Idempotency-Key": f"idem_finalize_{uuid.uuid4().hex[:12]}",
            },
        )
        assert finalize_response.status_code == 200
        assert finalize_response.json()["status"] == "finalized"


class TestUserPayload:
    """UserPayload 测试。"""

    def test_has_scope_returns_true_when_scope_present(self):
        """测试 has_scope 方法正确检测存在的 Scope。"""
        from app.schemas.auth import UserPayload

        user = UserPayload(
            user_id="test_user",
            role=Role.OPS,
            scopes=["ops:vote-cycles:write", "content:read"],
        )

        assert user.has_scope("ops:vote-cycles:write") is True
        assert user.has_scope(Scope.OPS_VOTE_CYCLES_WRITE) is True
        assert user.has_scope("votes:submit") is False

    def test_has_role_returns_true_when_role_matches(self):
        """测试 has_role 方法正确检测角色。"""
        from app.schemas.auth import UserPayload

        user = UserPayload(
            user_id="test_user",
            role=Role.OPS,
            scopes=["ops:vote-cycles:write"],
        )

        assert user.has_role(Role.OPS) is True
        assert user.has_role(Role.PLAYER) is False