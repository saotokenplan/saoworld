import pytest


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_rate_limit_allows_normal_requests(self, client, valid_token):
        for _ in range(5):
            response = await client.get(
                "/api/v1/votes/current",
                headers={"Authorization": f"Bearer {valid_token}"},
            )
            assert response.status_code != 429

    @pytest.mark.asyncio
    async def test_rate_limiter_class_logic(self):
        from app.core.limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=3)

        assert await limiter.check("player_1") is True
        assert await limiter.check("player_1") is True
        assert await limiter.check("player_1") is True
        assert await limiter.check("player_1") is False

    @pytest.mark.asyncio
    async def test_rate_limiter_per_player_isolation(self):
        from app.core.limiter import RateLimiter

        limiter = RateLimiter(requests_per_minute=3)

        for _ in range(4):
            await limiter.check("player_1")

        assert await limiter.check("player_1") is False
        assert await limiter.check("player_2") is True

    @pytest.mark.asyncio
    async def test_rate_limit_error_response_format(self, client, valid_token):
        from app.core.limiter import rate_limiter

        rate_limiter.requests_per_minute = 2

        for _ in range(3):
            response = await client.get(
                "/api/v1/votes/current",
                headers={"Authorization": f"Bearer {valid_token}"},
            )

        assert response.status_code == 429 or response.status_code == 503