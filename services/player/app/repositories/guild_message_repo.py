"""公会消息仓储层。

提供公会消息的数据库操作方法。
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import GuildMessage


class GuildMessageRepository:
    """公会消息仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        """初始化仓储层。

        Args:
            db: 数据库会话
        """
        self.db = db

    async def send_message(
        self,
        guild_id: uuid.UUID,
        sender_id: uuid.UUID,
        content: str,
    ) -> GuildMessage:
        """发送公会消息。

        Args:
            guild_id: 公会ID
            sender_id: 发送者玩家ID
            content: 消息内容

        Returns:
            创建的公会消息对象
        """
        message = GuildMessage(
            guild_id=guild_id,
            sender_id=sender_id,
            content=content,
            is_read=False,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_guild_messages(
        self,
        guild_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[GuildMessage], int]:
        """获取公会消息列表。

        Args:
            guild_id: 公会ID
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            消息列表（按创建时间倒序）和总数
        """
        count_query = (
            select(func.count())
            .select_from(GuildMessage)
            .where(GuildMessage.guild_id == guild_id)
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(GuildMessage)
            .where(GuildMessage.guild_id == guild_id)
            .order_by(GuildMessage.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        messages = list(result.scalars().all())
        return messages, total

    async def mark_messages_as_read(
        self,
        guild_id: uuid.UUID,
        player_id: uuid.UUID,
    ) -> int:
        """批量标记公会消息已读。

        Args:
            guild_id: 公会ID
            player_id: 玩家ID

        Returns:
            更新的消息数量
        """
        query = (
            select(GuildMessage)
            .where(
                GuildMessage.guild_id == guild_id,
                GuildMessage.sender_id != player_id,
                GuildMessage.is_read == False,  # noqa: E712
            )
        )
        result = await self.db.execute(query)
        messages = result.scalars().all()

        count = 0
        for message in messages:
            if not message.is_read:
                message.is_read = True
                count += 1

        if count > 0:
            await self.db.flush()

        return count

    async def get_unread_count(
        self,
        guild_id: uuid.UUID,
        player_id: uuid.UUID,
    ) -> int:
        """获取未读消息数。

        Args:
            guild_id: 公会ID
            player_id: 玩家ID

        Returns:
            未读消息数
        """
        query = (
            select(func.count())
            .select_from(GuildMessage)
            .where(
                GuildMessage.guild_id == guild_id,
                GuildMessage.sender_id != player_id,
                GuildMessage.is_read == False,  # noqa: E712
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def delete_message(
        self,
        guild_id: uuid.UUID,
        message_id: uuid.UUID,
        player_id: uuid.UUID,
        is_leader_or_officer: bool = False,
    ) -> bool:
        """删除消息。

        发送者或会长/官员可删除消息。

        Args:
            guild_id: 公会ID
            message_id: 消息ID
            player_id: 当前玩家ID（用于权限校验）
            is_leader_or_officer: 是否为会长或官员

        Returns:
            是否成功删除
        """
        query = (
            select(GuildMessage)
            .where(
                GuildMessage.guild_id == guild_id,
                GuildMessage.message_id == message_id,
            )
        )
        result = await self.db.execute(query)
        message = result.scalar_one_or_none()

        if message is None:
            return False

        if message.sender_id != player_id and not is_leader_or_officer:
            return False

        await self.db.delete(message)
        await self.db.flush()
        return True

    async def get_recent_messages(
        self,
        guild_id: uuid.UUID,
        limit: int = 20,
    ) -> list[GuildMessage]:
        """获取最近 N 条消息。

        Args:
            guild_id: 公会ID
            limit: 返回数量限制

        Returns:
            消息列表（按创建时间倒序）
        """
        query = (
            select(GuildMessage)
            .where(GuildMessage.guild_id == guild_id)
            .order_by(GuildMessage.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_message_by_id(
        self,
        guild_id: uuid.UUID,
        message_id: uuid.UUID,
    ) -> GuildMessage | None:
        """根据ID获取消息。

        Args:
            guild_id: 公会ID
            message_id: 消息ID

        Returns:
            消息对象或None
        """
        query = (
            select(GuildMessage)
            .where(
                GuildMessage.guild_id == guild_id,
                GuildMessage.message_id == message_id,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()