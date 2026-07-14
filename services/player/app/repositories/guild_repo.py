"""公会仓储层。"""

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import and_, delete, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Guild, GuildMember


class GuildRepository:
    """公会仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_guild(
        self,
        name: str,
        leader_id: uuid.UUID,
        description: str | None = None,
        max_members: int = 50,
    ) -> Guild:
        """创建公会。

        同时创建会长成员记录。

        Args:
            name: 公会名称
            leader_id: 会长玩家ID
            description: 公会描述
            max_members: 最大成员数

        Returns:
            Guild: 公会记录
        """
        guild = Guild(
            guild_id=uuid.uuid4(),
            name=name,
            leader_id=leader_id,
            description=description,
            level=1,
            member_count=1,
            max_members=max_members,
        )
        self.db.add(guild)

        # 创建会长成员记录
        member = GuildMember(
            guild_member_id=uuid.uuid4(),
            guild_id=guild.guild_id,
            player_id=leader_id,
            role="leader",
        )
        self.db.add(member)

        await self.db.flush()
        return guild

    async def get_guild_by_id(self, guild_id: uuid.UUID) -> Guild | None:
        """获取公会详情。

        Args:
            guild_id: 公会ID

        Returns:
            Guild | None: 公会记录，不存在返回 None
        """
        stmt = select(Guild).where(Guild.guild_id == guild_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_guild_by_name(self, name: str) -> Guild | None:
        """按名称查询公会。

        Args:
            name: 公会名称

        Returns:
            Guild | None: 公会记录，不存在返回 None
        """
        stmt = select(Guild).where(Guild.name == name)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_guild_by_player(self, player_id: uuid.UUID) -> Guild | None:
        """获取玩家所在公会。

        Args:
            player_id: 玩家ID

        Returns:
            Guild | None: 公会记录，未加入返回 None
        """
        stmt = (
            select(Guild)
            .join(GuildMember, Guild.guild_id == GuildMember.guild_id)
            .where(GuildMember.player_id == player_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_guild_member_by_player(
        self, player_id: uuid.UUID
    ) -> GuildMember | None:
        """获取玩家的公会成员记录。

        Args:
            player_id: 玩家ID

        Returns:
            GuildMember | None: 公会成员记录，未加入返回 None
        """
        stmt = select(GuildMember).where(GuildMember.player_id == player_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_guild(
        self,
        guild_id: uuid.UUID,
        description: str | None = None,
        announcement: str | None = None,
    ) -> Guild | None:
        """更新公会信息。

        Args:
            guild_id: 公会ID
            description: 公会描述
            announcement: 公会公告

        Returns:
            Guild | None: 更新后的公会，不存在返回 None
        """
        guild = await self.get_guild_by_id(guild_id)
        if guild is None:
            return None

        if description is not None:
            guild.description = description
        if announcement is not None:
            guild.announcement = announcement

        guild.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return guild

    async def delete_guild(self, guild_id: uuid.UUID) -> bool:
        """删除公会。

        先删除所有成员记录，再删除公会。

        Args:
            guild_id: 公会ID

        Returns:
            bool: 是否成功删除
        """
        guild = await self.get_guild_by_id(guild_id)
        if guild is None:
            return False

        # 删除所有成员记录
        stmt = (
            select(GuildMember.guild_member_id)
            .where(GuildMember.guild_id == guild_id)
        )
        result = await self.db.execute(stmt)
        member_ids = result.scalars().all()

        for member_id in member_ids:
            await self.db.execute(
                delete(GuildMember).where(
                    GuildMember.guild_member_id == member_id
                )
            )

        # 删除公会
        await self.db.delete(guild)
        await self.db.flush()
        return True

    async def add_member(
        self, guild_id: uuid.UUID, player_id: uuid.UUID, role: str = "member"
    ) -> GuildMember | None:
        """添加成员。

        检查玩家是否已在其他公会，检查公会是否已满。

        Args:
            guild_id: 公会ID
            player_id: 玩家ID
            role: 成员角色

        Returns:
            GuildMember | None: 成员记录，失败返回 None
        """
        # 检查公会是否存在
        guild = await self.get_guild_by_id(guild_id)
        if guild is None:
            return None

        # 检查公会是否已满
        if guild.member_count >= guild.max_members:
            return None

        # 检查玩家是否已加入其他公会
        existing = await self.get_guild_by_player(player_id)
        if existing is not None:
            return None

        member = GuildMember(
            guild_member_id=uuid.uuid4(),
            guild_id=guild_id,
            player_id=player_id,
            role=role,
        )
        self.db.add(member)

        # 更新成员数
        guild.member_count += 1
        guild.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return member

    async def remove_member(
        self, guild_id: uuid.UUID, player_id: uuid.UUID
    ) -> bool:
        """移除成员。

        不能移除会长。

        Args:
            guild_id: 公会ID
            player_id: 玩家ID

        Returns:
            bool: 是否成功移除
        """
        # 检查公会是否存在
        guild = await self.get_guild_by_id(guild_id)
        if guild is None:
            return False

        # 查找成员记录
        stmt = select(GuildMember).where(
            and_(
                GuildMember.guild_id == guild_id,
                GuildMember.player_id == player_id,
            )
        )
        result = await self.db.execute(stmt)
        member = result.scalar_one_or_none()

        if member is None:
            return False

        # 不能移除会长
        if member.role == "leader":
            return False

        await self.db.delete(member)

        # 更新成员数
        guild.member_count -= 1
        guild.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return True

    async def transfer_leader(
        self, guild_id: uuid.UUID, new_leader_id: uuid.UUID
    ) -> bool:
        """转让会长。

        将新会长设为 leader，原会长降为 officer。

        Args:
            guild_id: 公会ID
            new_leader_id: 新会长玩家ID

        Returns:
            bool: 是否成功转让
        """
        guild = await self.get_guild_by_id(guild_id)
        if guild is None:
            return False

        # 检查新会长是否为本公会成员
        new_leader_member = await self.get_member(guild_id, new_leader_id)
        if new_leader_member is None:
            return False

        old_leader_id = guild.leader_id

        # 将原会长降为 officer
        old_leader_member = await self.get_member(guild_id, old_leader_id)
        if old_leader_member is not None:
            old_leader_member.role = "officer"

        # 将新会长设为 leader
        new_leader_member.role = "leader"

        # 更新公会 leader_id
        guild.leader_id = new_leader_id
        guild.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return True

    async def set_member_role(
        self, guild_id: uuid.UUID, player_id: uuid.UUID, role: str
    ) -> GuildMember | None:
        """设置成员角色。

        不能修改会长角色。

        Args:
            guild_id: 公会ID
            player_id: 玩家ID
            role: 新角色

        Returns:
            GuildMember | None: 更新后的成员，失败返回 None
        """
        member = await self.get_member(guild_id, player_id)
        if member is None:
            return None

        # 不能修改会长角色
        if member.role == "leader":
            return None

        member.role = role
        await self.db.flush()
        return member

    async def get_member(
        self, guild_id: uuid.UUID, player_id: uuid.UUID
    ) -> GuildMember | None:
        """获取公会成员记录。

        Args:
            guild_id: 公会ID
            player_id: 玩家ID

        Returns:
            GuildMember | None: 成员记录，不存在返回 None
        """
        stmt = select(GuildMember).where(
            and_(
                GuildMember.guild_id == guild_id,
                GuildMember.player_id == player_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_members(
        self, guild_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[GuildMember], int]:
        """获取公会成员列表（分页）。

        Args:
            guild_id: 公会ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            tuple[list[GuildMember], int]: 成员列表和总数
        """
        base_filter = GuildMember.guild_id == guild_id

        # 计算总数
        count_stmt = (
            select(sa_func.count())
            .select_from(GuildMember)
            .where(base_filter)
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        # 查询列表（按角色排序：leader > officer > member，然后按加入时间）
        stmt = (
            select(GuildMember)
            .where(base_filter)
            .order_by(
                GuildMember.role.desc(),  # leader > officer > member
                GuildMember.joined_at.asc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        members = result.scalars().all()

        return members, total

    async def get_member_count(self, guild_id: uuid.UUID) -> int:
        """获取成员数量。

        Args:
            guild_id: 公会ID

        Returns:
            int: 成员数量
        """
        stmt = (
            select(sa_func.count())
            .select_from(GuildMember)
            .where(GuildMember.guild_id == guild_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def is_guild_leader(
        self, guild_id: uuid.UUID, player_id: uuid.UUID
    ) -> bool:
        """判断玩家是否为公会会长。

        Args:
            guild_id: 公会ID
            player_id: 玩家ID

        Returns:
            bool: 是否为会长
        """
        guild = await self.get_guild_by_id(guild_id)
        return guild is not None and guild.leader_id == player_id

    async def is_guild_officer(
        self, guild_id: uuid.UUID, player_id: uuid.UUID
    ) -> bool:
        """判断玩家是否为公会官员（含会长）。

        Args:
            guild_id: 公会ID
            player_id: 玩家ID

        Returns:
            bool: 是否为官员
        """
        member = await self.get_member(guild_id, player_id)
        return member is not None and member.role in ("leader", "officer")

    async def is_guild_member(
        self, guild_id: uuid.UUID, player_id: uuid.UUID
    ) -> bool:
        """判断玩家是否为公会成员。

        Args:
            guild_id: 公会ID
            player_id: 玩家ID

        Returns:
            bool: 是否为成员
        """
        member = await self.get_member(guild_id, player_id)
        return member is not None