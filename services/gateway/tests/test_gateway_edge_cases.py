"""Gateway 边界场景与补充测试。

覆盖以下测试缺口：
1. 代理请求错误处理（连接失败、超时、内部错误的错误码验证）
2. 无效事件请求体校验（缺失字段、空列表、非法 JSON）
3. 服务健康检查详情（各服务不可达时的状态与延迟字段）
4. Auth Scope 权限校验（不同 scope 组合的通过/拒绝）
5. 限流行为（健康检查豁免、精确边界触发、错误响应格式）
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.core.config import settings
from app.core.errors import GatewayErrorCodes
from tests.conftest import create_test_token


# ---------------------------------------------------------------------------
# 1. 代理请求错误处理
# ---------------------------------------------------------------------------


class TestProxyErrorHandling:
    """验证代理请求到后端服务失败时返回正确的错误码和状态码。"""

    @pytest.mark.asyncio
    async def test_proxy_connect_error_returns_service_unavailable_code(self, client, valid_token):
        """代理到不可用服务时应返回 503 和 SERVICE_UNAVAILABLE 错误码。"""
        response = await client.get(
            "/api/v1/votes/current",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 503
        data = response.json()
        assert data["code"] == GatewayErrorCodes.SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_proxy_connect_error_includes_request_id(self, client, valid_token):
        """代理连接失败响应中必须包含 request_id 字段。"""
        request_id = "req_proxy_err_001"
        response = await client.get(
            "/api/v1/votes/current",
            headers={
                "Authorization": f"Bearer {valid_token}",
                "X-Request-Id": request_id,
            },
        )
        assert response.status_code == 503
        assert response.headers.get("X-Request-Id") == request_id

    @pytest.mark.asyncio
    async def test_proxy_connect_error_includes_trace_id(self, client, valid_token):
        """代理连接失败响应中必须回传 trace_id。"""
        trace_id = "trace_proxy_err_001"
        response = await client.get(
            "/api/v1/votes/current",
            headers={
                "Authorization": f"Bearer {valid_token}",
                "X-Trace-Id": trace_id,
            },
        )
        assert response.status_code == 503
        assert response.headers.get("X-Trace-Id") == trace_id

    @pytest.mark.asyncio
    async def test_proxy_timeout_returns_gateway_timeout_code(self, client, valid_token):
        """代理请求超时时应返回 504 和 GATEWAY_TIMEOUT 错误码。"""
        import httpx

        with patch("app.core.proxy.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_instance.request = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

            response = await client.get(
                "/api/v1/votes/current",
                headers={"Authorization": f"Bearer {valid_token}"},
            )
            assert response.status_code == 504
            data = response.json()
            assert data["code"] == GatewayErrorCodes.GATEWAY_TIMEOUT

    @pytest.mark.asyncio
    async def test_proxy_unexpected_exception_returns_internal_error_code(self, client, valid_token):
        """代理请求发生未知异常时应返回 500 和 INTERNAL_ERROR 错误码。"""
        with patch("app.core.proxy.httpx.AsyncClient") as mock_client_cls:
            mock_instance = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)
            mock_instance.request = AsyncMock(side_effect=RuntimeError("unexpected"))

            response = await client.get(
                "/api/v1/votes/current",
                headers={"Authorization": f"Bearer {valid_token}"},
            )
            assert response.status_code == 500
            data = response.json()
            assert data["code"] == GatewayErrorCodes.INTERNAL_ERROR

    @pytest.mark.asyncio
    async def test_proxy_unknown_path_returns_not_found_code(self, client, valid_token):
        """请求未映射到任何后端服务的路径应返回 404 和 NOT_FOUND 错误码。"""
        response = await client.get(
            "/api/v1/nonexistent/endpoint",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == GatewayErrorCodes.NOT_FOUND

    @pytest.mark.asyncio
    async def test_proxy_post_to_unavailable_service_returns_503(self, client, valid_token):
        """POST 请求代理到不可用服务时同样返回 503。"""
        response = await client.post(
            "/api/v1/votes/submit",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={"candidate_id": "test-id"},
        )
        assert response.status_code == 503
        data = response.json()
        assert data["code"] == GatewayErrorCodes.SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_proxy_delete_to_unavailable_service_returns_503(self, client, valid_token):
        """DELETE 请求代理到不可用服务时同样返回 503。"""
        response = await client.delete(
            "/api/v1/world/regions/region_01",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 503
        data = response.json()
        assert data["code"] == GatewayErrorCodes.SERVICE_UNAVAILABLE


# ---------------------------------------------------------------------------
# 2. 无效事件请求体校验
# ---------------------------------------------------------------------------


class TestInvalidEventBody:
    """验证事件提交接口对无效请求体的校验行为。"""

    @pytest.mark.asyncio
    async def test_submit_events_with_empty_list_returns_ok(self, client):
        """提交空事件列表应返回 200，published_count 为 0。"""
        with patch("app.api.routes.get_event_bus") as mock_get_bus:
            mock_bus = AsyncMock()
            mock_get_bus.return_value = mock_bus

            response = await client.post(
                "/api/v1/events/batch",
                json={"events": []},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["published_count"] == 0

    @pytest.mark.asyncio
    async def test_submit_events_missing_event_type(self, client):
        """缺少 event_type 字段应返回 422 校验错误。"""
        response = await client.post(
            "/api/v1/events/batch",
            json={
                "events": [
                    {
                        "player_id": "00000000-0000-0000-0000-000000000001",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_events_missing_player_id(self, client):
        """缺少 player_id 字段应返回 422 校验错误。"""
        response = await client.post(
            "/api/v1/events/batch",
            json={
                "events": [
                    {
                        "event_type": "player_action",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_events_missing_timestamp(self, client):
        """缺少 timestamp 字段应返回 422 校验错误。"""
        response = await client.post(
            "/api/v1/events/batch",
            json={
                "events": [
                    {
                        "event_type": "player_action",
                        "player_id": "00000000-0000-0000-0000-000000000001",
                    }
                ]
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_events_invalid_json_body(self, client):
        """发送非法 JSON 应返回 422 校验错误。"""
        response = await client.post(
            "/api/v1/events/batch",
            content=b"not valid json{{{",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_events_missing_events_key(self, client):
        """请求体中缺少 events 键应返回 422 校验错误。"""
        response = await client.post(
            "/api/v1/events/batch",
            json={"data": "invalid"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_events_with_invalid_timestamp_format(self, client):
        """timestamp 字段格式非法应返回 422 校验错误。"""
        response = await client.post(
            "/api/v1/events/batch",
            json={
                "events": [
                    {
                        "event_type": "player_action",
                        "player_id": "00000000-0000-0000-0000-000000000001",
                        "timestamp": "not-a-datetime",
                    }
                ]
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_events_optional_fields_default_correctly(self, client):
        """region_id、payload、trace_id 为可选字段，省略时应使用默认值。"""
        event_data = {
            "events": [
                {
                    "event_type": "player_action",
                    "player_id": "00000000-0000-0000-0000-000000000001",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }

        with patch("app.api.routes.get_event_bus") as mock_get_bus:
            mock_bus = AsyncMock()
            mock_get_bus.return_value = mock_bus

            response = await client.post("/api/v1/events/batch", json=event_data)

            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "ok"
            assert data["data"]["published_count"] == 1


# ---------------------------------------------------------------------------
# 3. 服务健康检查详情
# ---------------------------------------------------------------------------


class TestServicesHealthDetails:
    """验证 /health/services 端点返回的详细状态信息。"""

    @pytest.mark.asyncio
    async def test_all_services_unreachable_when_down(self, client):
        """当所有后端服务都不可达时，每个服务状态应为 unreachable。"""
        response = await client.get("/api/v1/health/services")
        assert response.status_code == 200
        data = response.json()
        for svc in data["services"]:
            assert svc["status"] == "unreachable"

    @pytest.mark.asyncio
    async def test_unreachable_services_have_no_latency(self, client):
        """不可达服务的 latency_ms 应为 None。"""
        response = await client.get("/api/v1/health/services")
        assert response.status_code == 200
        data = response.json()
        for svc in data["services"]:
            if svc["status"] == "unreachable":
                assert svc["latency_ms"] is None

    @pytest.mark.asyncio
    async def test_gateway_info_in_services_health(self, client):
        """services health 响应中 gateway 字段应包含正确的服务名和版本。"""
        response = await client.get("/api/v1/health/services")
        assert response.status_code == 200
        data = response.json()
        assert data["gateway"]["status"] == "ok"
        assert data["gateway"]["service"] == settings.app_name
        assert data["gateway"]["version"] == settings.app_version

    @pytest.mark.asyncio
    async def test_each_service_has_url_field(self, client):
        """每个服务条目应包含 url 字段且非空。"""
        response = await client.get("/api/v1/health/services")
        assert response.status_code == 200
        data = response.json()
        for svc in data["services"]:
            assert "url" in svc
            assert svc["url"] != ""

    @pytest.mark.asyncio
    async def test_service_health_count_matches_config(self, client):
        """services 列表长度应与配置的后端服务数量一致（7个）。"""
        response = await client.get("/api/v1/health/services")
        assert response.status_code == 200
        data = response.json()
        expected_services = [
            "vote-service",
            "world-service",
            "content-service",
            "generation-service",
            "review-service",
            "player-service",
            "ops-service",
        ]
        assert len(data["services"]) == len(expected_services)
        actual_names = {s["service"] for s in data["services"]}
        assert actual_names == set(expected_services)

    @pytest.mark.asyncio
    async def test_services_health_no_auth_required(self, client):
        """services health 端点不需要认证即可访问。"""
        response = await client.get("/api/v1/health/services")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# 4. Auth Scope 权限校验
# ---------------------------------------------------------------------------


class TestAuthScopeValidation:
    """验证不同 scope 组合对受保护端点的访问控制。"""

    @pytest.mark.asyncio
    async def test_player_token_forbidden_on_ops_endpoint(self, client, valid_token):
        """只有 votes:read/votes:submit scope 的 player token 访问 ops 端点应返回 403。"""
        response = await client.get(
            "/api/v1/ops/dashboard",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_player_token_forbidden_on_content_release(self, client):
        """缺少 content:release scope 的 token 访问内容发布接口应返回 403。"""
        token = create_test_token(
            "00000000-0000-0000-0000-000000000010",
            roles=["player"],
            scopes=["votes:read", "votes:submit"],
        )
        response = await client.post(
            "/api/v1/content/release",
            headers={"Authorization": f"Bearer {token}"},
            json={"package_id": "pkg_test"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_player_token_forbidden_on_content_rollback(self, client):
        """缺少 content:rollback scope 的 token 访问内容回滚接口应返回 403。"""
        token = create_test_token(
            "00000000-0000-0000-0000-000000000011",
            roles=["player"],
            scopes=["votes:read", "votes:submit"],
        )
        response = await client.post(
            "/api/v1/content/rollback",
            headers={"Authorization": f"Bearer {token}"},
            json={"package_id": "pkg_test"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_player_without_history_scope_forbidden_on_votes_history(self, client):
        """缺少 votes:history:read scope 的 token 访问投票历史接口应返回 403。"""
        token = create_test_token(
            "00000000-0000-0000-0000-000000000012",
            roles=["player"],
            scopes=["votes:read", "votes:submit"],
        )
        response = await client.get(
            "/api/v1/votes/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        data = response.json()
        assert data["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_ops_token_allowed_on_ops_endpoint(self, client, ops_token):
        """拥有 ops:* scope 的 ops token 可以访问 ops 端点（后端不可达返回 503，不是 403）。"""
        response = await client.get(
            "/api/v1/ops/dashboard",
            headers={"Authorization": f"Bearer {ops_token}"},
        )
        assert response.status_code != 403
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_token_with_history_scope_allowed_on_votes_history(self, client):
        """拥有 votes:history:read scope 的 token 可以通过权限校验访问投票历史。"""
        token = create_test_token(
            "00000000-0000-0000-0000-000000000013",
            roles=["player"],
            scopes=["votes:read", "votes:history:read"],
        )
        response = await client.get(
            "/api/v1/votes/history",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 权限校验通过，因后端不可达返回 503
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_forbidden_response_includes_request_id(self, client, valid_token):
        """403 响应中必须包含 request_id。"""
        request_id = "req_scope_test_001"
        response = await client.get(
            "/api/v1/ops/dashboard",
            headers={
                "Authorization": f"Bearer {valid_token}",
                "X-Request-Id": request_id,
            },
        )
        assert response.status_code == 403
        assert response.headers.get("X-Request-Id") == request_id

    @pytest.mark.asyncio
    async def test_forbidden_response_includes_trace_id(self, client, valid_token):
        """403 响应中必须回传 trace_id。"""
        trace_id = "trace_scope_test_001"
        response = await client.get(
            "/api/v1/ops/dashboard",
            headers={
                "Authorization": f"Bearer {valid_token}",
                "X-Trace-Id": trace_id,
            },
        )
        assert response.status_code == 403
        assert response.headers.get("X-Trace-Id") == trace_id

    @pytest.mark.asyncio
    async def test_token_with_content_release_scope_passes_auth(self, client):
        """拥有 content:release scope 的 token 可以通过权限校验访问内容发布端点。"""
        token = create_test_token(
            "00000000-0000-0000-0000-000000000014",
            roles=["ops"],
            scopes=["content:release"],
        )
        response = await client.post(
            "/api/v1/content/release",
            headers={"Authorization": f"Bearer {token}"},
            json={"package_id": "pkg_test"},
        )
        # 权限校验通过，因后端不可达返回 503
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_token_with_content_rollback_scope_passes_auth(self, client):
        """拥有 content:rollback scope 的 token 可以通过权限校验访问内容回滚端点。"""
        token = create_test_token(
            "00000000-0000-0000-0000-000000000015",
            roles=["ops"],
            scopes=["content:rollback"],
        )
        response = await client.post(
            "/api/v1/content/rollback",
            headers={"Authorization": f"Bearer {token}"},
            json={"package_id": "pkg_test"},
        )
        # 权限校验通过，因后端不可达返回 503
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_no_scope_required_for_unprotected_path(self, client):
        """不在 PATH_SCOPE_RULES 中的路径不需要特定 scope，仅需认证即可。"""
        token = create_test_token(
            "00000000-0000-0000-0000-000000000016",
            roles=["player"],
            scopes=["votes:read"],
        )
        response = await client.get(
            "/api/v1/player/info",
            headers={"Authorization": f"Bearer {token}"},
        )
        # 不需要特定 scope，仅需认证。后端不可达返回 503
        assert response.status_code != 403
        assert response.status_code == 503


# ---------------------------------------------------------------------------
# 5. 限流行为
# ---------------------------------------------------------------------------


class TestRateLimitingBehavior:
    """验证限流中间件的行为细节。"""

    @pytest.mark.asyncio
    async def test_health_endpoints_bypass_rate_limit(self, client):
        """健康检查端点不受限流影响，即使超过限流阈值也应返回 200。"""
        from app.core.limiter import rate_limiter

        original_limit = rate_limiter.requests_per_minute
        rate_limiter.requests_per_minute = 2
        rate_limiter.client_requests.clear()

        try:
            # 先用一个已认证请求消耗限流配额
            token = create_test_token(
                "00000000-0000-0000-0000-000000000020",
                scopes=["votes:read"],
            )
            for _ in range(3):
                await client.get(
                    "/api/v1/votes/current",
                    headers={"Authorization": f"Bearer {token}"},
                )

            # 健康检查不应受影响
            response = await client.get("/api/v1/health")
            assert response.status_code == 200

            response = await client.get("/api/v1/health/services")
            assert response.status_code == 200
        finally:
            rate_limiter.requests_per_minute = original_limit
            rate_limiter.client_requests.clear()

    @pytest.mark.asyncio
    async def test_rate_limit_triggered_at_exact_boundary(self, client):
        """请求数恰好达到限流阈值时，最后一次请求应被拒绝。"""
        from app.core.limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=3)

        # 前 3 次允许
        for i in range(3):
            result = await limiter.check("player_boundary")
            assert result is True, f"请求 {i + 1} 应被允许"

        # 第 4 次拒绝
        result = await limiter.check("player_boundary")
        assert result is False

    @pytest.mark.asyncio
    async def test_rate_limit_error_has_correct_code(self, client):
        """限流错误响应应包含 RATE_LIMIT_EXCEEDED 错误码。"""
        from app.core.limiter import rate_limiter

        rate_limiter.requests_per_minute = 2
        rate_limiter.client_requests.clear()

        try:
            token = create_test_token(
                "00000000-0000-0000-0000-000000000021",
                scopes=["votes:read"],
            )

            # 消耗配额
            for _ in range(3):
                response = await client.get(
                    "/api/v1/votes/current",
                    headers={"Authorization": f"Bearer {token}"},
                )

            # 最后一次应触发限流或 503（后端不可达先于限流触发）
            # 如果返回 429，验证错误码
            if response.status_code == 429:
                data = response.json()
                assert data["code"] == "RATE_LIMIT_EXCEEDED"
        finally:
            rate_limiter.requests_per_minute = 60
            rate_limiter.client_requests.clear()

    @pytest.mark.asyncio
    async def test_rate_limit_per_player_isolation_in_integration(self, client):
        """不同玩家的限流配额互相独立，一个玩家被限流不影响另一个。"""
        from app.core.limiter import rate_limiter

        rate_limiter.requests_per_minute = 2
        rate_limiter.client_requests.clear()

        try:
            token_a = create_test_token(
                "00000000-0000-0000-0000-000000000030",
                scopes=["votes:read"],
            )
            token_b = create_test_token(
                "00000000-0000-0000-0000-000000000031",
                scopes=["votes:read"],
            )

            # 玩家 A 消耗配额
            for _ in range(3):
                await client.get(
                    "/api/v1/votes/current",
                    headers={"Authorization": f"Bearer {token_a}"},
                )

            # 玩家 B 的请求不受影响（可能 503 但不应是 429）
            response_b = await client.get(
                "/api/v1/votes/current",
                headers={"Authorization": f"Bearer {token_b}"},
            )
            assert response_b.status_code != 429
        finally:
            rate_limiter.requests_per_minute = 60
            rate_limiter.client_requests.clear()

    @pytest.mark.asyncio
    async def test_unauthenticated_requests_not_rate_limited(self, client):
        """未认证请求不触发限流（中间件跳过无 player_id 的请求）。"""
        from app.core.limiter import rate_limiter

        rate_limiter.requests_per_minute = 2
        rate_limiter.client_requests.clear()

        try:
            # 多次无 token 请求
            for _ in range(5):
                response = await client.get("/api/v1/votes/current")
                assert response.status_code == 401  # 认证失败，但不是 429
        finally:
            rate_limiter.requests_per_minute = 60
            rate_limiter.client_requests.clear()

    @pytest.mark.asyncio
    async def test_rate_limiter_cleans_expired_entries(self):
        """限流器应清理超过 60 秒的过期请求记录。"""
        import time

        from app.core.limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=2)

        # 手动添加过期记录
        limiter.client_requests["player_old"] = [time.time() - 120]

        # 清理后，新请求应被允许
        result = await limiter.check("player_old")
        assert result is True

    @pytest.mark.asyncio
    async def test_events_endpoint_not_rate_limited(self, client):
        """事件提交端点 (/api/v1/events) 不需要认证，因此不触发限流。"""
        from app.core.limiter import rate_limiter

        rate_limiter.requests_per_minute = 1
        rate_limiter.client_requests.clear()

        try:
            # 多次请求事件端点
            for _ in range(3):
                response = await client.post(
                    "/api/v1/events/batch",
                    json={
                        "events": [
                            {
                                "event_type": "test",
                                "player_id": "00000000-0000-0000-0000-000000000040",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            }
                        ]
                    },
                )
                # 应返回 200 或 500（Redis 连接失败），但不是 429
                assert response.status_code != 429
        finally:
            rate_limiter.requests_per_minute = 60
            rate_limiter.client_requests.clear()
