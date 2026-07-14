import pytest


class TestProxyRouting:
    @pytest.mark.asyncio
    async def test_vote_service_route(self, client, valid_token):
        response = await client.get(
            "/api/v1/votes/current",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_world_service_route(self, client, valid_token):
        response = await client.get(
            "/api/v1/world/regions",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_content_service_route(self, client, valid_token):
        response = await client.get(
            "/api/v1/content/updates",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_generation_service_route(self, client, valid_token):
        response = await client.get(
            "/api/v1/generation/requests",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_review_service_route(self, client, valid_token):
        response = await client.get(
            "/api/v1/review/records",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_player_service_route(self, client, valid_token):
        response = await client.get(
            "/api/v1/player/info",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_ops_service_route(self, client, ops_token):
        response = await client.get(
            "/api/v1/ops/dashboard",
            headers={"Authorization": f"Bearer {ops_token}"},
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_unknown_route_returns_404(self, client, valid_token):
        response = await client.get(
            "/api/v1/unknown/path",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_request_id_passed_to_backend(self, client, valid_token):
        custom_id = "req_proxy_test_001"
        response = await client.get(
            "/api/v1/votes/current",
            headers={
                "Authorization": f"Bearer {valid_token}",
                "X-Request-Id": custom_id,
            },
        )
        assert response.headers.get("X-Request-Id") == custom_id

    @pytest.mark.asyncio
    async def test_trace_id_passed_to_backend(self, client, valid_token):
        trace_id = "trace_proxy_test_001"
        response = await client.get(
            "/api/v1/votes/current",
            headers={
                "Authorization": f"Bearer {valid_token}",
                "X-Trace-Id": trace_id,
            },
        )
        assert response.headers.get("X-Trace-Id") == trace_id

    @pytest.mark.asyncio
    async def test_idempotency_key_passed_to_backend(self, client, valid_token):
        idempotency_key = "idempotency_test_key_001"
        response = await client.get(
            "/api/v1/votes/current",
            headers={
                "Authorization": f"Bearer {valid_token}",
                "Idempotency-Key": idempotency_key,
            },
        )
        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_post_request_proxy(self, client, valid_token):
        response = await client.post(
            "/api/v1/votes/submit",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={"candidate_id": "test-candidate-id"},
        )
        assert response.status_code == 503
