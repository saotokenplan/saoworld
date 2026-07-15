"""私聊消息仓储层。

提供私聊消息的数据库操作方法。
"""

import uuid
from typing import Any

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import PrivateMessage


class PrivateMessageRepository:
    """私聊消息仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        """初始化仓储层。

        Args:
            db: 数据库会话
        """
        self.db = db

    async def send_message(
        self,
        sender_id: uuid.UUID,
        receiver_id: uuid.UUID,
        content: str,
    ) -> PrivateMessage:
        """发送私聊消息。

        Args:
            sender_id: 发送者ID
            receiver_id: 接收者ID
            content: 消息内容

        Returns:
            创建的私聊消息对象
        """
        message = PrivateMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            is_read=False,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_conversation(
        self,
        player_id: uuid.UUID,
        friend_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PrivateMessage]:
        """获取两人间对话历史。

        Args:
            player_id: 当前玩家ID
            friend_id: 好友ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            消息列表（按创建时间倒序）
        """
        query = (
            select(PrivateMessage)
            .where(
                or_(
                    and_(
                        PrivateMessage.sender_id == player_id,
                        PrivateMessage.receiver_id == friend_id,
                    ),
                    and_(
                        PrivateMessage.sender_id == friend_id,
                        PrivateMessage.receiver_id == player_id,
                    ),
                )
            )
            .order_by(PrivateMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_recent_conversations(
        self,
        player_id: uuid.UUID,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """获取最近对话列表。

        返回与每个好友的最新一条消息。

        Args:
            player_id: 当前玩家ID
            limit: 返回数量限制

        Returns:
            对话摘要列表，每个元素包含 friend_id 和 latest_message
        """
        # 子查询：获取每个对话的最新消息ID
        latest_message_subq = (
            select(
                func.max(PrivateMessage.message_id).label("latest_message_id"),
            )
            .where(
                or_(
                    PrivateMessage.sender_id == player_id,
                    PrivateMessage.receiver_id == player_id,
                )
            )
            .group_by(
                case(
                    (PrivateMessage.sender_id == player_id, PrivateMessage.receiver_id),
                    else_=PrivateMessage.sender_id,
                )
            )
            .subquery()
        )

        # 主查询：获取最新消息详情
        query = (
            select(PrivateMessage)
            .where(PrivateMessage.message_id.in_(select(latest_message_subq)))
            .order_by(PrivateMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        messages = list(result.scalars().all())

        # 构建对话列表
        conversations = []
        for msg in messages:
            friend_id = msg.receiver_id if msg.sender_id == player_id else msg.sender_id
            conversations.append({
                "friend_id": friend_id,
                "latest_message": msg,
            })
        return conversations

    async def mark_as_read(
        self,
        message_id: uuid.UUID,
        receiver_id: uuid.UUID,
    ) -> bool:
        """标记消息为已读。

        Args:
            message_id: 消息ID
            receiver_id: 接收者ID（校验权限）

        Returns:
            是否成功更新
        """
        query = (
            select(PrivateMessage)
            .where(
                PrivateMessage.message_id == message_id,
                PrivateMessage.receiver_id == receiver_id,
            )
        )
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if message is None:
            return False

        if not message.is_read:
            message.is_read = True
            await self.db.flush()
        return True

    async def get_unread_count(
        self,
        receiver_id: uuid.UUID,
    ) -> int:
        """获取未读消息数。

        Args:
            receiver_id: 接收者ID

        Returns:
            未读消息数
        """
        query = (
            select(func.count())
            .select_from(PrivateMessage)
            .where(
                PrivateMessage.receiver_id == receiver_id,
                PrivateMessage.is_read == False,  # noqa: E712
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_unread_messages(
        self,
        receiver_id: uuid.UUID,
        limit: int = 50,
    ) -> list[PrivateMessage]:
        """获取未读消息列表。

        Args:
            receiver_id: 接收者ID
            limit: 返回数量限制

        Returns:
            未读消息列表
        """
        query = (
            select(PrivateMessage)
            .where(
                PrivateMessage.receiver_id == receiver_id,
                PrivateMessage.is_read == False,  # noqa: E712
            )
            .order_by(PrivateMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_message(
        self,
        message_id: uuid.UUID,
        sender_id: uuid.UUID,
    ) -> bool:
        """删除消息（仅发送者可删）。

        Args:
            message_id: 消息ID
            sender_id: 发送者ID（校验权限）

        Returns:
            是否成功删除
        """
        query = (
            select(PrivateMessage)
            .where(
                PrivateMessage.message_id == message_id,
                PrivateMessage.sender_id == sender_id,
            )
        )
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if message is None:
            return False

        await self.db.delete(message)
        await self.db.flush()
        return True

    async def get_message_by_id(
        self,
        message_id: uuid.UUID,
    ) -> PrivateMessage | None:
        """根据ID获取消息。

        Args:
            message_id: 消息ID

        Returns:
            消息对象或None
        """
        query = select(PrivateMessage).where(PrivateMessage.message_id == message_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()