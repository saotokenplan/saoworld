import uuid
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ReviewRecord

REVIEW_VALID_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"approved", "rejected", "manual_review"},
    "approved": set(),
    "rejected": set(),
    "manual_review": {"approved", "rejected"},
}


class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review(
        self,
        object_id: uuid.UUID,
        object_type: str,
        review_type: str,
        trace_id: str,
        quality_score: float | None = None,
        detail: dict[str, Any] | None = None,
        result: str = "pending",
        risk_level: str = "low",
    ) -> ReviewRecord:
        review = ReviewRecord(
            object_id=object_id,
            object_type=object_type,
            review_type=review_type,
            trace_id=trace_id,
            quality_score=quality_score,
            detail_jsonb=detail,
            result=result,
            risk_level=risk_level,
        )
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def get_review_by_id(self, review_id: uuid.UUID) -> ReviewRecord | None:
        result = await self.db.execute(
            select(ReviewRecord).where(ReviewRecord.review_id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_reviews_by_object_id(self, object_id: uuid.UUID) -> list[ReviewRecord]:
        result = await self.db.execute(
            select(ReviewRecord)
            .where(ReviewRecord.object_id == object_id)
            .order_by(ReviewRecord.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_reviews(
        self,
        object_type: str | None = None,
        result: str | None = None,
        risk_level: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ReviewRecord], int]:
        query = select(ReviewRecord)
        count_query = select(func.count(ReviewRecord.review_id))

        conditions: list[Any] = []
        if object_type:
            conditions.append(ReviewRecord.object_type == object_type)
        if result:
            conditions.append(ReviewRecord.result == result)
        if risk_level:
            conditions.append(ReviewRecord.risk_level == risk_level)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        query = query.order_by(ReviewRecord.created_at.desc())
        query = query.offset(offset).limit(limit)

        result_obj = await self.db.execute(query)
        reviews = list(result_obj.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        return reviews, total

    def can_transition(self, from_status: str, to_status: str) -> bool:
        return to_status in REVIEW_VALID_TRANSITIONS.get(from_status, set())

    async def update_review_result(
        self,
        review_id: uuid.UUID,
        result: str,
        risk_level: str | None = None,
        reason: str | None = None,
        operator_id: str | None = None,
        operator_role: str | None = None,
    ) -> ReviewRecord:
        review = await self.get_review_by_id(review_id)
        if not review:
            raise ValueError("REVIEW_NOT_FOUND")

        if not self.can_transition(review.result, result):
            raise ValueError("INVALID_REVIEW_STATUS")

        review.result = result
        if risk_level is not None:
            review.risk_level = risk_level
        if reason is not None:
            review.reason = reason
        if operator_id is not None:
            review.operator_id = operator_id
        if operator_role is not None:
            review.operator_role = operator_role

        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def approve_by_object_id(
        self,
        object_id: uuid.UUID,
        operator_id: str,
        operator_role: str,
        reason: str | None = None,
    ) -> list[ReviewRecord]:
        reviews = await self.get_reviews_by_object_id(object_id)
        if not reviews:
            raise ValueError("NO_REVIEWS_FOUND")

        updated_reviews = []
        for review in reviews:
            if self.can_transition(review.result, "approved"):
                updated = await self.update_review_result(
                    review_id=review.review_id,
                    result="approved",
                    risk_level="low",
                    reason=reason,
                    operator_id=operator_id,
                    operator_role=operator_role,
                )
                updated_reviews.append(updated)

        return updated_reviews

    async def reject_by_object_id(
        self,
        object_id: uuid.UUID,
        operator_id: str,
        operator_role: str,
        reason: str | None = None,
        risk_level: str = "medium",
    ) -> list[ReviewRecord]:
        reviews = await self.get_reviews_by_object_id(object_id)
        if not reviews:
            raise ValueError("NO_REVIEWS_FOUND")

        updated_reviews = []
        for review in reviews:
            if self.can_transition(review.result, "rejected"):
                updated = await self.update_review_result(
                    review_id=review.review_id,
                    result="rejected",
                    risk_level=risk_level,
                    reason=reason,
                    operator_id=operator_id,
                    operator_role=operator_role,
                )
                updated_reviews.append(updated)

        return updated_reviews