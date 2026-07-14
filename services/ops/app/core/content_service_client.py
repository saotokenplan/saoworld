"""content-service HTTP 客户端。

为 ops-service 提供调用 content-service 运营 API 的能力。
"""

from typing import cast

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ContentServiceClient:
    """content-service 运营 API 客户端。"""

    def __init__(self) -> None:
        self.base_url = settings.content_service_url

    async def release_content_package(
        self,
        content_package_id: str,
        *,
        release_mode: str = "gray",
        gray_scope: dict | None = None,
        token: str | None = None,
        trace_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """发布内容包（灰度或全量）。"""
        payload: dict = {"release_mode": release_mode}
        if gray_scope:
            payload["gray_scope"] = gray_scope

        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/ops/content-packages/{content_package_id}/release",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())

    async def rollback_content_package(
        self,
        content_package_id: str,
        *,
        reason: str | None = None,
        token: str | None = None,
        trace_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """回滚内容包。"""
        payload: dict = {}
        if reason:
            payload["reason"] = reason

        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/ops/content-packages/{content_package_id}/rollback",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())

    async def list_content_packages(
        self,
        *,
        status: str | None = None,
        region_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """查询内容包列表。"""
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if region_id:
            params["region_id"] = region_id

        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/content/updates",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())

    async def get_content_package_detail(
        self,
        content_package_id: str,
        *,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """查询内容包详情。"""
        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/content/packages/{content_package_id}",
                headers=headers,
            )
            resp.raise_for_status()
            return cast(dict, resp.json())
