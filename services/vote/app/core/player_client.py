"""player-service HTTP 客户端。

用于 vote-service 在投票提交前查询玩家在 player-service 中的贡献度。
"""

import structlog
from httpx import AsyncClient, HTTPStatusError, RequestError, TimeoutException

from app.core.config import settings
from app.core.errors import VoteErrorCodes, raise_vote_error

logger = structlog.get_logger()


class PlayerContributionClient:
    """查询玩家贡献度的 HTTP 客户端。"""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.player_service_url).rstrip("/")
        self.timeout = timeout or settings.player_service_timeout_seconds
        self._client: AsyncClient | None = None

    async def _get_client(self) -> AsyncClient:
        if self._client is None:
            self._client = AsyncClient(timeout=self.timeout)
        return self._client

    async def get_contribution(self, player_id: str, authorization: str | None) -> int:
        """查询玩家当前贡献度总分。

        Args:
            player_id: 玩家 ID（UUID 字符串）
            authorization: 玩家 JWT Token（Authorization 头值）

        Returns:
            int: 玩家贡献度总分

        Raises:
            HTTPException: player-service 不可用或返回非 200 响应
        """
        if not authorization:
            raise_vote_error(
                VoteErrorCodes.DEPENDENCY_UNAVAILABLE,
                "缺少调用 player-service 的认证信息",
                request_id="req_player_contribution_no_auth",
                status_code=503,
            )

        url = f"{self.base_url}/api/v1/player/contribution"
        headers = {
            "Authorization": authorization,
            "Accept": "application/json",
        }

        client = await self._get_client()
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
        except (RequestError, TimeoutException) as exc:
            logger.error(
                "player_service_dependency_unavailable",
                player_id=player_id,
                error=str(exc),
            )
            raise_vote_error(
                VoteErrorCodes.DEPENDENCY_UNAVAILABLE,
                "player-service 暂时不可用，请稍后重试",
                request_id="req_player_contribution_dependency",
                status_code=503,
            )
        except HTTPStatusError as exc:
            logger.error(
                "player_service_http_error",
                player_id=player_id,
                status_code=exc.response.status_code,
                error=str(exc),
            )
            raise_vote_error(
                VoteErrorCodes.DEPENDENCY_UNAVAILABLE,
                f"player-service 返回错误: {exc.response.status_code}",
                request_id="req_player_contribution_http_error",
                status_code=503,
            )

        data = response.json().get("data", {})
        contribution_points = data.get("contribution_points", 0)
        return int(contribution_points)

    async def close(self) -> None:
        """关闭底层 HTTP 客户端。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
