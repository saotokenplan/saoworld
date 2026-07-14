"""vote-service HTTP 客户端。

为 ops-service 提供调用 vote-service 运营 API 的能力。
"""

from typing import cast

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class VoteServiceClient:
    """vote-service 运营 API 客户端。"""

    def __init__(self) -> None:
        self.base_url = settings.vote_service_url

    async def create_vote_cycle(
        self,
        *,
        chapter_id: str,
        title: str,
        description: str | None = None,
        started_at: str | None = None,
        ended_at: str | None = None,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """创建投票周期。"""
        payload: dict = {
            "chapter_id": chapter_id,
            "title": title,
        }
        if description:
            payload["description"] = description
        if started_at:
            payload["started_at"] = started_at
        if ended_at:
            payload["ended_at"] = ended_at

        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/ops/vote-cycles",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())

    async def schedule_vote_cycle(
        self,
        vote_cycle_id: str,
        *,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """计划投票周期。"""
        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/ops/vote-cycles/{vote_cycle_id}/schedule",
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())

    async def open_vote_cycle(
        self,
        vote_cycle_id: str,
        *,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """开启投票。"""
        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/ops/vote-cycles/{vote_cycle_id}/open",
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())

    async def close_vote_cycle(
        self,
        vote_cycle_id: str,
        *,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """关闭投票。"""
        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/ops/vote-cycles/{vote_cycle_id}/close",
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())

    async def finalize_vote_cycle(
        self,
        vote_cycle_id: str,
        *,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """确认投票结果。"""
        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/ops/vote-cycles/{vote_cycle_id}/finalize",
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())

    async def list_vote_cycles(
        self,
        *,
        status: str | None = None,
        chapter_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """查询投票周期列表。"""
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if chapter_id:
            params["chapter_id"] = chapter_id

        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/votes/history",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())

    async def get_vote_cycle_detail(
        self,
        vote_cycle_id: str,
        *,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """查询投票周期详情。"""
        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/votes/history/{vote_cycle_id}/review",
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())
