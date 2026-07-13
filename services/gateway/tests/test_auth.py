import pytest

from app.core.errors import GatewayErrorCodes


class TestAuthentication:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client):
        response = await client.get("/api/v1/votes/current")
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, client, invalid_token):
        response = await client.get(
            "/api/v1/votes/current",
            headers={"Authorization": f"Bearer {invalid_token}"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == GatewayErrorCodes.INVALID_TOKEN

    @pytest.mark.asyncio
    async def test_expired_token_returns_401(self, client, expired_token):
        response = await client.get(
            "/api/v1/votes/current",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_valid_token_allowed(self, client, valid_token):
        response = await client.get(
            "/api/v1/votes/current",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 404 or response.status_code == 503

    @pytest.mark.asyncio
    async def test_invalid_auth_scheme_returns_401(self, client):
        response = await client.get(
            "/api/v1/votes/current",
            headers={"Authorization": "Basic somebase64string"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["code"] == "INVALID_AUTH_SCHEME"

    @pytest.mark.asyncio
    async def test_request_id_in_auth_error(self, client):
        response = await client.get("/api/v1/votes/current")
        assert response.status_code == 401
        data = response.json()
        assert "request_id" in data
        assert response.headers.get("X-Request-Id") is not None
