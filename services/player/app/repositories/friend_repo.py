"""好友关系仓储层。"""

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import Select, and_, or_, select, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Friendship


class FriendRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def send_friend_request(
        self, player_id: uuid.UUID, friend_id: uuid.UUID
    ) -> Friendship:
        """发送好友请求。

        幂等：如果已有 pending 请求，返回原记录。
        如果对方已向自己发送 pending 请求，自动接受。

        Args:
            player_id: 发起者ID
            friend_id: 目标玩家ID

        Returns:
            Friendship: 好友关系记录
        """
        # 检查对方是否已向自己发送 pending 请求 → 自动接受
        reverse_stmt: Select[tuple[Friendship]] = select(Friendship).where(
            and_(
                Friendship.player_id == friend_id,
                Friendship.friend_id == player_id,
                Friendship.status == "pending",
            )
        )
        reverse_result = await self.db.execute(reverse_stmt)
        reverse_friendship = reverse_result.scalar_one_or_none()

        if reverse_friendship is not None:
            reverse_friendship.status = "accepted"
            reverse_friendship.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            return reverse_friendship

        # 检查是否已有记录（任意方向、任意状态）
        existing_stmt = select(Friendship).where(
            or_(
                and_(
                    Friendship.player_id == player_id,
                    Friendship.friend_id == friend_id,
                ),
                and_(
                    Friendship.player_id == friend_id,
                    Friendship.friend_id == player_id,
                ),
            )
        )
        existing_result = await self.db.execute(existing_stmt)
        existing = existing_result.scalar_one_or_none()

        if existing is not None:
            return existing

        friendship = Friendship(
            friendship_id=uuid.uuid4(),
            player_id=player_id,
            friend_id=friend_id,
            status="pending",
        )
        self.db.add(friendship)
        await self.db.flush()
        return friendship

    async def accept_friend_request(
        self, player_id: uuid.UUID, friend_id: uuid.UUID
    ) -> Friendship | None:
        """接受好友请求。

        只有目标玩家（friend_id）可以接受发起者（player_id）的请求。

        Args:
            player_id: 原始请求的发起者ID
            friend_id: 接受者（当前玩家）ID

        Returns:
            Friendship | None: 更新后的好友关系，未找到返回 None
        """
        stmt = select(Friendship).where(
            and_(
                Friendship.player_id == player_id,
                Friendship.friend_id == friend_id,
                Friendship.status == "pending",
            )
        )
        result = await self.db.execute(stmt)
        friendship = result.scalar_one_or_none()

        if friendship is None:
            return None

        friendship.status = "accepted"
        friendship.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return friendship

    async def reject_friend_request(
        self, player_id: uuid.UUID, friend_id: uuid.UUID
    ) -> Friendship | None:
        """拒绝好友请求。

        Args:
            player_id: 原始请求的发起者ID
            friend_id: 拒绝者（当前玩家）ID

        Returns:
            Friendship | None: 更新后的好友关系，未找到返回 None
        """
        stmt = select(Friendship).where(
            and_(
                Friendship.player_id == player_id,
                Friendship.friend_id == friend_id,
                Friendship.status == "pending",
            )
        )
        result = await self.db.execute(stmt)
        friendship = result.scalar_one_or_none()

        if friendship is None:
            return None

        friendship.status = "rejected"
        friendship.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return friendship

    async def delete_friend(
        self, player_id: uuid.UUID, friend_id: uuid.UUID
    ) -> bool:
        """删除好友关系（双向删除）。

        Args:
            player_id: 当前玩家ID
            friend_id: 好友ID

        Returns:
            bool: 是否成功删除
        """
        stmt = select(Friendship).where(
            or_(
                and_(
                    Friendship.player_id == player_id,
                    Friendship.friend_id == friend_id,
                ),
                and_(
                    Friendship.player_id == friend_id,
                    Friendship.friend_id == player_id,
                ),
            )
        )
        result = await self.db.execute(stmt)
        friendship = result.scalar_one_or_none()

        if friendship is None:
            return False

        await self.db.delete(friendship)
        await self.db.flush()
        return True

    async def block_friend(
        self, player_id: uuid.UUID, friend_id: uuid.UUID
    ) -> Friendship | None:
        """拉黑好友。

        Args:
            player_id: 当前玩家ID
            friend_id: 被拉黑的玩家ID

        Returns:
            Friendship | None: 更新后的好友关系，未找到返回 None
        """
        stmt = select(Friendship).where(
            or_(
                and_(
                    Friendship.player_id == player_id,
                    Friendship.friend_id == friend_id,
                ),
                and_(
                    Friendship.player_id == friend_id,
                    Friendship.friend_id == player_id,
                ),
            )
        )
        result = await self.db.execute(stmt)
        friendship = result.scalar_one_or_none()

        if friendship is None:
            # 创建新的 blocked 记录
            friendship = Friendship(
                friendship_id=uuid.uuid4(),
                player_id=player_id,
                friend_id=friend_id,
                status="blocked",
            )
            self.db.add(friendship)
            await self.db.flush()
            return friendship

        friendship.status = "blocked"
        friendship.player_id = player_id
        friendship.friend_id = friend_id
        friendship.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return friendship

    async def get_friends(
        self, player_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Friendship], int]:
        """获取好友列表（分页）。

        Args:
            player_id: 当前玩家ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            tuple[list[Friendship], int]: 好友列表和总数
        """
        # 查询作为发起者的已接受好友
        # 查询作为接受者的已接受好友
        base_filter = and_(
            or_(
                Friendship.player_id == player_id,
                Friendship.friend_id == player_id,
            ),
            Friendship.status == "accepted",
        )

        # 计算总数
        count_stmt = select(sa_func.count()).select_from(Friendship).where(base_filter)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 查询列表
        stmt = (
            select(Friendship)
            .where(base_filter)
            .order_by(Friendship.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        friendships = result.scalars().all()

        return friendships, total

    async def get_pending_requests(
        self, player_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Friendship], int]:
        """获取待处理的好友请求（别人发给自己的）。

        Args:
            player_id: 当前玩家ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            tuple[list[Friendship], int]: 请求列表和总数
        """
        base_filter = and_(
            Friendship.friend_id == player_id,
            Friendship.status == "pending",
        )

        count_stmt = select(sa_func.count()).select_from(Friendship).where(base_filter)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            select(Friendship)
            .where(base_filter)
            .order_by(Friendship.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        friendships = result.scalars().all()

        return friendships, total

    async def get_friendship(
        self, player_id: uuid.UUID, friend_id: uuid.UUID
    ) -> Friendship | None:
        """查询两人间的好友关系。

        Args:
            player_id: 玩家ID
            friend_id: 好友ID

        Returns:
            Friendship | None: 好友关系，不存在返回 None
        """
        stmt = select(Friendship).where(
            or_(
                and_(
                    Friendship.player_id == player_id,
                    Friendship.friend_id == friend_id,
                ),
                and_(
                    Friendship.player_id == friend_id,
                    Friendship.friend_id == player_id,
                ),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def are_friends(
        self, player_id: uuid.UUID, friend_id: uuid.UUID
    ) -> bool:
        """判断两人是否为好友。

        Args:
            player_id: 玩家ID
            friend_id: 好友ID

        Returns:
            bool: 是否为好友
        """
        stmt = select(Friendship).where(
            or_(
                and_(
                    Friendship.player_id == player_id,
                    Friendship.friend_id == friend_id,
                    Friendship.status == "accepted",
                ),
                and_(
                    Friendship.player_id == friend_id,
                    Friendship.friend_id == player_id,
                    Friendship.status == "accepted",
                ),
            )
        ).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar() is not None

    async def get_friend_count(self, player_id: uuid.UUID) -> int:
        """获取好友数量。

        Args:
            player_id: 玩家ID

        Returns:
            int: 好友数量
        """
        stmt = select(sa_func.count()).select_from(Friendship).where(
            and_(
                or_(
                    Friendship.player_id == player_id,
                    Friendship.friend_id == player_id,
                ),
                Friendship.status == "accepted",
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def is_blocked(
        self, player_id: uuid.UUID, friend_id: uuid.UUID
    ) -> bool:
        """检查是否被对方拉黑。

        Args:
            player_id: 当前玩家ID
            friend_id: 对方玩家ID

        Returns:
            bool: 是否被拉黑
        """
        stmt = select(Friendship).where(
            and_(
                Friendship.player_id == friend_id,
                Friendship.friend_id == player_id,
                Friendship.status == "blocked",
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
