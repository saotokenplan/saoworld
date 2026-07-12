"""内容包服务客户端，用于查询内容包落地信息。"""

import uuid
from datetime import datetime
from typing import Any

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class ContentPackageInfo:
    """内容包落地信息。"""

    def __init__(
        self,
        content_package_id: uuid.UUID,
        vote_cycle_id: uuid.UUID,
        version: str,
        status: str,
        affected_regions: list[str],
        landed_at: datetime | None = None,
    ) -> None:
        self.content_package_id = content_package_id
        self.vote_cycle_id = vote_cycle_id
        self.version = version
        self.status = status
        self.affected_regions = affected_regions
        self.landed_at = landed_at

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContentPackageInfo":
        """从字典解析内容包信息。"""
        return cls(
            content_package_id=uuid.UUID(data["content_package_id"]),
            vote_cycle_id=uuid.UUID(data["vote_cycle_id"]),
            version=data["version"],
            status=data["status"],
            affected_regions=data.get("affected_regions", []),
            landed_at=datetime.fromisoformat(data["landed_at"]) if data.get("landed_at") else None,
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典。"""
        return {
            "content_package_id": str(self.content_package_id),
            "vote_cycle_id": str(self.vote_cycle_id),
            "version": self.version,
            "status": self.status,
            "affected_regions": self.affected_regions,
            "landed_at": self.landed_at.isoformat() if self.landed_at else None,
        }


class ContentPackageClient:
    """内容包服务客户端。"""

    def __init__(self) -> None:
        self.base_url = settings.content_service_url
        self.timeout = httpx.Timeout(settings.content_service_timeout_seconds)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端。"""
        if self._client is None:
            self._client = httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """关闭客户端连接。"""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_content_package_by_vote_cycle(
        self,
        vote_cycle_id: uuid.UUID,
        authorization: str | None = None,
    ) -> ContentPackageInfo | None:
        """
        根据投票周期 ID 查询内容包信息。

        Args:
            vote_cycle_id: 投票周期 ID
            authorization: 认证令牌（可选）

        Returns:
            内容包信息，如果不存在则返回 None
        """
        client = await self._get_client()

        headers = {}
        if authorization:
            headers["Authorization"] = authorization

        try:
            response = await client.get(
                f"/api/v1/content/packages/by-vote-cycle/{vote_cycle_id}",
                headers=headers,
            )

            if response.status_code == 404:
                logger.info(
                    "content_package_not_found",
                    vote_cycle_id=str(vote_cycle_id),
                )
                return None

            if response.status_code != 200:
                logger.warning(
                    "content_service_error",
                    vote_cycle_id=str(vote_cycle_id),
                    status_code=response.status_code,
                )
                return None

            data = response.json()
            envelope = data.get("data", data)

            return ContentPackageInfo.from_dict(envelope)

        except httpx.TimeoutException:
            logger.error(
                "content_service_timeout",
                vote_cycle_id=str(vote_cycle_id),
                timeout_seconds=settings.content_service_timeout_seconds,
            )
            return None
        except httpx.RequestError as e:
            logger.error(
                "content_service_request_error",
                vote_cycle_id=str(vote_cycle_id),
                error=str(e),
            )
            return None
        except Exception as e:
            logger.error(
                "content_service_unexpected_error",
                vote_cycle_id=str(vote_cycle_id),
                error=str(e),
            )
            return None

    async def get_content_packages_batch(
        self,
        vote_cycle_ids: list[uuid.UUID],
        authorization: str | None = None,
    ) -> dict[uuid.UUID, ContentPackageInfo]:
        """
        批量查询多个投票周期的内容包信息。

        Args:
            vote_cycle_ids: 投票周期 ID 列表
            authorization: 认证令牌（可选）

        Returns:
            投票周期 ID 到内容包信息的映射
        """
        if not vote_cycle_ids:
            return {}

        result: dict[uuid.UUID, ContentPackageInfo] = {}

        # 并发查询所有内容包信息
        client = await self._get_client()
        headers = {}
        if authorization:
            headers["Authorization"] = authorization

        async def fetch_one(vote_cycle_id: uuid.UUID) -> tuple[uuid.UUID, ContentPackageInfo | None]:
            try:
                response = await client.get(
                    f"/api/v1/content/packages/by-vote-cycle/{vote_cycle_id}",
                    headers=headers,
                )

                if response.status_code == 200:
                    data = response.json()
                    envelope = data.get("data", data)
                    return vote_cycle_id, ContentPackageInfo.from_dict(envelope)

                return vote_cycle_id, None

            except Exception as e:
                logger.error(
                    "content_package_batch_fetch_error",
                    vote_cycle_id=str(vote_cycle_id),
                    error=str(e),
                )
                return vote_cycle_id, None

        # 使用 asyncio.gather 并发查询
        import asyncio

        tasks = [fetch_one(vcid) for vcid in vote_cycle_ids]
        results = await asyncio.gather(*tasks)

        for vote_cycle_id, info in results:
            if info is not None:
                result[vote_cycle_id] = info

        return result