import uuid
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import GeneratedObject, GenerationRequest

REQUEST_VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"processing", "failed_permanent"},
    "processing": {"succeeded", "failed_retryable", "failed_permanent"},
    "succeeded": set(),
    "failed_retryable": {"pending", "processing", "failed_permanent"},
    "failed_permanent": set(),
}

OBJECT_VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending_review": {"approved", "rejected", "needs_revision"},
    "approved": set(),
    "rejected": set(),
    "needs_revision": {"pending_review", "approved", "rejected"},
}


class GenerationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(
        self,
        template_id: str,
        input_payload: dict[str, Any],
        trace_id: str,
        vote_cycle_id: uuid.UUID | None = None,
        source_candidate_id: uuid.UUID | None = None,
    ) -> GenerationRequest:
        req = GenerationRequest(
            vote_cycle_id=vote_cycle_id,
            source_candidate_id=source_candidate_id,
            template_id=template_id,
            input_payload_jsonb=input_payload,
            status="pending",
            trace_id=trace_id,
        )
        self.db.add(req)
        await self.db.flush()
        await self.db.refresh(req)
        return req

    async def get_request_by_id(self, request_id: uuid.UUID) -> GenerationRequest | None:
        result = await self.db.execute(
            select(GenerationRequest).where(GenerationRequest.request_id == request_id)
        )
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[GenerationRequest], int]:
        query = select(GenerationRequest)
        count_query = select(func.count(GenerationRequest.request_id))

        conditions: list[Any] = []
        if status:
            conditions.append(GenerationRequest.status == status)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        query = query.order_by(GenerationRequest.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        requests = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        return requests, total

    def can_transition_request(self, from_status: str, to_status: str) -> bool:
        return to_status in REQUEST_VALID_TRANSITIONS.get(from_status, set())

    async def update_request_status(
        self,
        request_id: uuid.UUID,
        new_status: str,
        error_message: str | None = None,
    ) -> GenerationRequest:
        req = await self.get_request_by_id(request_id)
        if not req:
            raise ValueError("REQUEST_NOT_FOUND")

        if not self.can_transition_request(req.status, new_status):
            raise ValueError("INVALID_REQUEST_STATUS")

        if new_status == "pending" and req.status == "failed_retryable":
            if req.retry_count >= req.max_retries:
                raise ValueError("MAX_RETRIES_EXCEEDED")
            req.retry_count += 1

        req.status = new_status
        if error_message is not None:
            req.error_message = error_message

        await self.db.flush()
        await self.db.refresh(req)
        return req

    async def increment_retry(self, request_id: uuid.UUID) -> GenerationRequest:
        req = await self.get_request_by_id(request_id)
        if not req:
            raise ValueError("REQUEST_NOT_FOUND")

        if req.retry_count >= req.max_retries:
            raise ValueError("MAX_RETRIES_EXCEEDED")

        req.retry_count += 1
        await self.db.flush()
        await self.db.refresh(req)
        return req

    async def create_generated_object(
        self,
        request_id: uuid.UUID,
        object_type: str,
        object_payload: dict[str, Any],
        schema_version: int = 1,
        quality_score: float | None = None,
    ) -> GeneratedObject:
        obj = GeneratedObject(
            request_id=request_id,
            object_type=object_type,
            schema_version=schema_version,
            object_payload_jsonb=object_payload,
            quality_score=quality_score,
            status="pending_review",
        )
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def get_object_by_id(self, object_id: uuid.UUID) -> GeneratedObject | None:
        result = await self.db.execute(
            select(GeneratedObject).where(GeneratedObject.object_id == object_id)
        )
        return result.scalar_one_or_none()

    async def list_objects_by_request_id(
        self, request_id: uuid.UUID
    ) -> list[GeneratedObject]:
        result = await self.db.execute(
            select(GeneratedObject)
            .where(GeneratedObject.request_id == request_id)
            .order_by(GeneratedObject.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_objects(
        self,
        status: str | None = None,
        object_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[GeneratedObject], int]:
        query = select(GeneratedObject)
        count_query = select(func.count(GeneratedObject.object_id))

        conditions: list[Any] = []
        if status:
            conditions.append(GeneratedObject.status == status)
        if object_type:
            conditions.append(GeneratedObject.object_type == object_type)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        query = query.order_by(GeneratedObject.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        objects = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        return objects, total

    def can_transition_object(self, from_status: str, to_status: str) -> bool:
        return to_status in OBJECT_VALID_TRANSITIONS.get(from_status, set())

    async def update_object_status(
        self,
        object_id: uuid.UUID,
        new_status: str,
    ) -> GeneratedObject:
        obj = await self.get_object_by_id(object_id)
        if not obj:
            raise ValueError("OBJECT_NOT_FOUND")

        if not self.can_transition_object(obj.status, new_status):
            raise ValueError("INVALID_OBJECT_STATUS")

        obj.status = new_status
        await self.db.flush()
        await self.db.refresh(obj)
        return obj
