"""review-service HTTP 客户端。

为 ops-service 提供调用 review-service 审核工作流 API 的能力。
"""

import structlog
import httpx

from app.core.config import settings

logger = structlog.get_logger(__name__)


class ReviewServiceClient:
    """review-service 审核 API 客户端。"""

    def __init__(self) -> None:
        self.base_url = settings.review_service_url

    async def list_review_objects(
        self,
        *,
        status: str | None = None,
        risk_level: str | None = None,
        object_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """查询待审核对象列表。"""
        params: dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        if risk_level:
            params["risk_level"] = risk_level
        if object_type:
            params["object_type"] = object_type

        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/review/objects",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def approve_review_object(
        self,
        object_id: str,
        *,
        notes: str | None = None,
        token: str | None = None,
        trace_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """批准审核对象。"""
        payload: dict = {}
        if notes:
            payload["notes"] = notes

        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/ops/review/{object_id}/approve",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def reject_review_object(
        self,
        object_id: str,
        *,
        reason: str,
        token: str | None = None,
        trace_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> dict:
        """拒绝审核对象。"""
        payload: dict = {"reason": reason}

        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/ops/review/{object_id}/reject",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_review_stats(
        self,
        *,
        token: str | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """查询审核统计。"""
        headers: dict = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if trace_id:
            headers["X-Trace-Id"] = trace_id

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/review/stats",
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()
