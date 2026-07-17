"""好友协作任务仓储层。"""

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import FriendCollabQuest


class FriendCollabQuestRepository:
    """好友协作任务仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_quest(
        self,
        initiator_id: uuid.UUID,
        friend_id: uuid.UUID,
        quest_type: str,
        title: str,
        objectives: dict | None = None,
        rewards: dict | None = None,
        expires_at: datetime | None = None,
        description: str | None = None,
    ) -> FriendCollabQuest:
        """创建协作任务。

        Args:
            initiator_id: 发起者玩家ID
            friend_id: 好友玩家ID
            quest_type: 任务类型
            title: 任务标题
            objectives: 任务目标
            rewards: 任务奖励
            expires_at: 过期时间
            description: 任务描述

        Returns:
            FriendCollabQuest: 协作任务记录
        """
        quest = FriendCollabQuest(
            quest_id=uuid.uuid4(),
            initiator_id=initiator_id,
            friend_id=friend_id,
            quest_type=quest_type,
            status="pending_invite",
            title=title,
            description=description,
            objectives_jsonb=objectives,
            rewards_jsonb=rewards,
            expires_at=expires_at,
            schema_version=1,
        )
        self.db.add(quest)
        await self.db.flush()
        return quest

    async def accept_quest(self, quest_id: uuid.UUID) -> FriendCollabQuest | None:
        """接受协作任务邀请。

        Args:
            quest_id: 任务ID

        Returns:
            FriendCollabQuest | None: 更新后的任务，不存在返回 None
        """
        quest = await self.get_quest(quest_id)
        if quest is None:
            return None

        quest.status = "active"
        quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return quest

    async def reject_quest(self, quest_id: uuid.UUID) -> FriendCollabQuest | None:
        """拒绝协作任务邀请。

        Args:
            quest_id: 任务ID

        Returns:
            FriendCollabQuest | None: 更新后的任务，不存在返回 None
        """
        quest = await self.get_quest(quest_id)
        if quest is None:
            return None

        quest.status = "failed"
        quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return quest

    async def update_progress(
        self, quest_id: uuid.UUID, player_id: uuid.UUID, progress_data: dict
    ) -> FriendCollabQuest | None:
        """更新协作任务进度。

        Args:
            quest_id: 任务ID
            player_id: 更新进度的玩家ID
            progress_data: 进度数据

        Returns:
            FriendCollabQuest | None: 更新后的任务，不存在返回 None
        """
        quest = await self.get_quest(quest_id)
        if quest is None:
            return None

        existing_progress = quest.progress_jsonb or {}
        existing_progress[str(player_id)] = progress_data
        quest.progress_jsonb = existing_progress
        quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return quest

    async def complete_quest(self, quest_id: uuid.UUID) -> FriendCollabQuest | None:
        """完成协作任务。

        Args:
            quest_id: 任务ID

        Returns:
            FriendCollabQuest | None: 更新后的任务，不存在返回 None
        """
        quest = await self.get_quest(quest_id)
        if quest is None:
            return None

        quest.status = "completed"
        quest.completed_at = datetime.now(timezone.utc)
        quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return quest

    async def fail_quest(self, quest_id: uuid.UUID) -> FriendCollabQuest | None:
        """协作任务失败。

        Args:
            quest_id: 任务ID

        Returns:
            FriendCollabQuest | None: 更新后的任务，不存在返回 None
        """
        quest = await self.get_quest(quest_id)
        if quest is None:
            return None

        quest.status = "failed"
        quest.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return quest

    async def get_quest(self, quest_id: uuid.UUID) -> FriendCollabQuest | None:
        """获取协作任务详情。

        Args:
            quest_id: 任务ID

        Returns:
            FriendCollabQuest | None: 任务记录，不存在返回 None
        """
        stmt = select(FriendCollabQuest).where(FriendCollabQuest.quest_id == quest_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_quests(
        self, player_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[FriendCollabQuest], int]:
        """获取玩家进行中的协作任务。

        Args:
            player_id: 玩家ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            tuple[list[FriendCollabQuest], int]: 任务列表和总数
        """
        base_filter = and_(
            or_(
                FriendCollabQuest.initiator_id == player_id,
                FriendCollabQuest.friend_id == player_id,
            ),
            FriendCollabQuest.status == "active",
        )

        count_stmt = select(func.count(FriendCollabQuest.quest_id)).where(base_filter)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            select(FriendCollabQuest)
            .where(base_filter)
            .order_by(FriendCollabQuest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        quests = result.scalars().all()

        return quests, total

    async def get_pending_invites(
        self, player_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[FriendCollabQuest], int]:
        """获取待处理的协作任务邀请。

        Args:
            player_id: 玩家ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            tuple[list[FriendCollabQuest], int]: 任务列表和总数
        """
        base_filter = and_(
            FriendCollabQuest.friend_id == player_id,
            FriendCollabQuest.status == "pending_invite",
        )

        count_stmt = select(func.count(FriendCollabQuest.quest_id)).where(base_filter)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            select(FriendCollabQuest)
            .where(base_filter)
            .order_by(FriendCollabQuest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        quests = result.scalars().all()

        return quests, total

    async def get_quest_history(
        self, player_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[FriendCollabQuest], int]:
        """获取玩家协作任务历史。

        Args:
            player_id: 玩家ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            tuple[list[FriendCollabQuest], int]: 任务列表和总数
        """
        base_filter = and_(
            or_(
                FriendCollabQuest.initiator_id == player_id,
                FriendCollabQuest.friend_id == player_id,
            ),
            FriendCollabQuest.status.in_(["completed", "failed", "expired"]),
        )

        count_stmt = select(func.count(FriendCollabQuest.quest_id)).where(base_filter)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            select(FriendCollabQuest)
            .where(base_filter)
            .order_by(FriendCollabQuest.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        quests = result.scalars().all()

        return quests, total

    async def expire_overdue_quests(self) -> int:
        """将过期的协作任务标记为过期。

        Returns:
            int: 过期的任务数
        """
        now = datetime.now(timezone.utc)
        stmt = select(FriendCollabQuest).where(
            and_(
                FriendCollabQuest.status.in_(["pending_invite", "active"]),
                FriendCollabQuest.expires_at.is_not(None),
                FriendCollabQuest.expires_at < now,
            )
        )
        result = await self.db.execute(stmt)
        quests = result.scalars().all()

        count = 0
        for quest in quests:
            quest.status = "expired"
            quest.updated_at = now
            count += 1

        if count > 0:
            await self.db.flush()
        return count
