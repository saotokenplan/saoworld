import pytest


class TestRequestTracing:
    @pytest.mark.asyncio
    async def test_auto_generated_request_id(self, client):
        response = await client.get("/api/v1/health")
        request_id = response.headers.get("X-Request-Id")
        assert request_id is not None
        assert request_id.startswith("req_")

    @pytest.mark.asyncio
    async def test_custom_request_id_preserved(self, client):
        custom_id = "req_custom_123"
        response = await client.get("/api/v1/health", headers={"X-Request-Id": custom_id})
        assert response.headers["X-Request-Id"] == custom_id

    @pytest.mark.asyncio
    async def test_trace_id_preserved(self, client):
        trace_id = "trace_abc_123"
        response = await client.get("/api/v1/health", headers={"X-Trace-Id": trace_id})
        assert response.headers["X-Trace-Id"] == trace_id

    @pytest.mark.asyncio
    async def test_request_id_in_response_body(self, client):
        response = await client.get("/api/v1/health")
        data = response.json()
        assert "request_id" not in data

    @pytest.mark.asyncio
    async def test_request_id_in_error_response(self, client):
        response = await client.get("/api/v1/votes/current")
        assert response.status_code == 401
        data = response.json()
        assert "request_id" in data

    @pytest.mark.asyncio
    async def test_trace_id_in_error_response(self, client):
        trace_id = "trace_error_test"
        response = await client.get(
            "/api/v1/votes/current",
            headers={"X-Trace-Id": trace_id},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["trace_id"] == trace_id

    @pytest.mark.asyncio
    async def test_different_requests_have_different_ids(self, client):
        response1 = await client.get("/api/v1/health")
        response2 = await client.get("/api/v1/health")
        assert response1.headers["X-Request-Id"] != response2.headers["X-Request-Id"]
