"""用户反馈仓储层。"""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import set_pending_feedback_count
from app.domain.models import PlayerFeedback


class FeedbackRepository:
    """用户反馈仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        player_id: str,
        feedback_type: str,
        title: str,
        content: str,
        priority: str = "medium",
        region_id: str | None = None,
        chapter_id: str | None = None,
        attachment_urls: list[str] | None = None,
        metadata_jsonb: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> PlayerFeedback:
        """创建用户反馈。"""
        feedback = PlayerFeedback(
            feedback_id=uuid.uuid4(),
            player_id=player_id,
            feedback_type=feedback_type,
            title=title,
            content=content,
            priority=priority,
            region_id=region_id,
            chapter_id=chapter_id,
            attachment_urls=attachment_urls,
            metadata_jsonb=metadata_jsonb,
            trace_id=trace_id,
        )
        self.db.add(feedback)
        await self.db.flush()
        await self.db.refresh(feedback)

        # 更新待处理反馈数
        pending_count = await self.count_by_status("pending")
        set_pending_feedback_count(pending_count)

        return feedback

    async def get_by_id(self, feedback_id: uuid.UUID) -> PlayerFeedback | None:
        """根据ID查询反馈。"""
        result = await self.db.execute(
            select(PlayerFeedback).where(PlayerFeedback.feedback_id == feedback_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        status: str | None = None,
        feedback_type: str | None = None,
        priority: str | None = None,
        player_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PlayerFeedback]:
        """列表查询反馈。"""
        query = select(PlayerFeedback)

        if status:
            query = query.where(PlayerFeedback.status == status)
        if feedback_type:
            query = query.where(PlayerFeedback.feedback_type == feedback_type)
        if priority:
            query = query.where(PlayerFeedback.priority == priority)
        if player_id:
            query = query.where(PlayerFeedback.player_id == player_id)

        query = query.order_by(PlayerFeedback.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        status: str | None = None,
        feedback_type: str | None = None,
        priority: str | None = None,
        player_id: str | None = None,
    ) -> int:
        """统计反馈数。"""
        query = select(func.count(PlayerFeedback.feedback_id))

        if status:
            query = query.where(PlayerFeedback.status == status)
        if feedback_type:
            query = query.where(PlayerFeedback.feedback_type == feedback_type)
        if priority:
            query = query.where(PlayerFeedback.priority == priority)
        if player_id:
            query = query.where(PlayerFeedback.player_id == player_id)

        result = await self.db.execute(query)
        return result.scalar_one()

    async def count_by_status(self, status: str) -> int:
        """按状态统计反馈数。"""
        result = await self.db.execute(
            select(func.count(PlayerFeedback.feedback_id)).where(PlayerFeedback.status == status)
        )
        return result.scalar_one()

    async def update_status(
        self,
        feedback_id: uuid.UUID,
        new_status: str,
        resolved_by: str | None = None,
        resolution_note: str | None = None,
    ) -> PlayerFeedback | None:
        """更新反馈状态。"""
        feedback = await self.get_by_id(feedback_id)
        if not feedback:
            return None

        old_status = feedback.status
        feedback.status = new_status

        if new_status in ("resolved", "closed"):
            feedback.resolved_by = resolved_by
            feedback.resolved_at = func.now()
            feedback.resolution_note = resolution_note

        await self.db.flush()
        await self.db.refresh(feedback)

        # 更新待处理反馈数
        if old_status == "pending":
            pending_count = await self.count_by_status("pending")
            set_pending_feedback_count(pending_count)

        return feedback

    async def update_priority(
        self,
        feedback_id: uuid.UUID,
        new_priority: str,
    ) -> PlayerFeedback | None:
        """更新反馈优先级。"""
        feedback = await self.get_by_id(feedback_id)
        if not feedback:
            return None

        feedback.priority = new_priority
        await self.db.flush()
        await self.db.refresh(feedback)
        return feedback