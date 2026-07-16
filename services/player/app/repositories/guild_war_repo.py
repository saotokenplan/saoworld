"""公会战仓储层。"""

import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import and_, or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import GuildWar, GuildWarParticipant


class GuildWarRepository:
    """公会战仓储层。"""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def declare_war(
        self,
        challenger_guild_id: uuid.UUID,
        defender_guild_id: uuid.UUID,
        war_type: str,
        reward_config: dict | None = None,
    ) -> GuildWar:
        """宣战。

        Args:
            challenger_guild_id: 宣战方公会ID
            defender_guild_id: 防守方公会ID
            war_type: 战争类型
            reward_config: 奖励配置

        Returns:
            GuildWar: 公会战记录
        """
        war = GuildWar(
            war_id=uuid.uuid4(),
            challenger_guild_id=challenger_guild_id,
            defender_guild_id=defender_guild_id,
            status="declared",
            war_type=war_type,
            reward_jsonb=reward_config,
        )
        self.db.add(war)
        await self.db.flush()
        return war

    async def accept_war(self, war_id: uuid.UUID) -> GuildWar | None:
        """接受宣战。

        Args:
            war_id: 公会战ID

        Returns:
            GuildWar | None: 更新后的公会战，不存在返回 None
        """
        war = await self.get_war(war_id)
        if war is None:
            return None

        war.status = "accepted"
        war.accepted_at = datetime.now(timezone.utc)
        war.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return war

    async def cancel_war(self, war_id: uuid.UUID, guild_id: uuid.UUID) -> GuildWar | None:
        """取消公会战。

        Args:
            war_id: 公会战ID
            guild_id: 取消方公会ID（用于验证）

        Returns:
            GuildWar | None: 更新后的公会战，不存在返回 None
        """
        war = await self.get_war(war_id)
        if war is None:
            return None

        war.status = "cancelled"
        war.ended_at = datetime.now(timezone.utc)
        war.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return war

    async def start_war(self, war_id: uuid.UUID) -> GuildWar | None:
        """开始公会战。

        Args:
            war_id: 公会战ID

        Returns:
            GuildWar | None: 更新后的公会战，不存在返回 None
        """
        war = await self.get_war(war_id)
        if war is None:
            return None

        war.status = "in_progress"
        war.started_at = datetime.now(timezone.utc)
        war.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return war

    async def complete_war(
        self, war_id: uuid.UUID, winner_guild_id: uuid.UUID
    ) -> GuildWar | None:
        """完成公会战。

        Args:
            war_id: 公会战ID
            winner_guild_id: 获胜公会ID

        Returns:
            GuildWar | None: 更新后的公会战，不存在返回 None
        """
        war = await self.get_war(war_id)
        if war is None:
            return None

        war.status = "completed"
        war.winner_guild_id = winner_guild_id
        war.ended_at = datetime.now(timezone.utc)
        war.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return war

    async def get_war(self, war_id: uuid.UUID) -> GuildWar | None:
        """获取公会战详情。

        Args:
            war_id: 公会战ID

        Returns:
            GuildWar | None: 公会战记录，不存在返回 None
        """
        stmt = select(GuildWar).where(GuildWar.war_id == war_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_wars(
        self, guild_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[GuildWar], int]:
        """获取公会进行中的战争。

        Args:
            guild_id: 公会ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            tuple[list[GuildWar], int]: 战争列表和总数
        """
        base_filter = and_(
            or_(
                GuildWar.challenger_guild_id == guild_id,
                GuildWar.defender_guild_id == guild_id,
            ),
            GuildWar.status.in_(["declared", "accepted", "in_progress"]),
        )

        count_stmt = select(func.count(GuildWar.war_id)).where(base_filter)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            select(GuildWar)
            .where(base_filter)
            .order_by(GuildWar.declared_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        wars = result.scalars().all()

        return wars, total

    async def get_guild_war_history(
        self, guild_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[GuildWar], int]:
        """获取公会战争历史。

        Args:
            guild_id: 公会ID
            limit: 每页数量
            offset: 偏移量

        Returns:
            tuple[list[GuildWar], int]: 战争列表和总数
        """
        base_filter = and_(
            or_(
                GuildWar.challenger_guild_id == guild_id,
                GuildWar.defender_guild_id == guild_id,
            ),
            GuildWar.status.in_(["completed", "cancelled"]),
        )

        count_stmt = select(func.count(GuildWar.war_id)).where(base_filter)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar() or 0

        stmt = (
            select(GuildWar)
            .where(base_filter)
            .order_by(GuildWar.ended_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        wars = result.scalars().all()

        return wars, total

    async def join_war(
        self, war_id: uuid.UUID, guild_id: uuid.UUID, player_id: uuid.UUID
    ) -> GuildWarParticipant:
        """加入公会战。

        Args:
            war_id: 公会战ID
            guild_id: 公会ID
            player_id: 玩家ID

        Returns:
            GuildWarParticipant: 参与记录
        """
        participant = GuildWarParticipant(
            participant_id=uuid.uuid4(),
            war_id=war_id,
            guild_id=guild_id,
            player_id=player_id,
        )
        self.db.add(participant)
        await self.db.flush()
        return participant

    async def record_kill(self, participant_id: uuid.UUID) -> GuildWarParticipant | None:
        """记录击杀。

        Args:
            participant_id: 参与者ID

        Returns:
            GuildWarParticipant | None: 更新后的参与记录，不存在返回 None
        """
        stmt = select(GuildWarParticipant).where(
            GuildWarParticipant.participant_id == participant_id
        )
        result = await self.db.execute(stmt)
        participant = result.scalar_one_or_none()

        if participant is None:
            return None

        participant.kills += 1
        participant.contribution_score += 10
        participant.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return participant

    async def get_war_participants(
        self, war_id: uuid.UUID, guild_id: uuid.UUID
    ) -> Sequence[GuildWarParticipant]:
        """获取公会战某方参与成员。

        Args:
            war_id: 公会战ID
            guild_id: 公会ID

        Returns:
            list[GuildWarParticipant]: 参与成员列表
        """
        stmt = (
            select(GuildWarParticipant)
            .where(
                and_(
                    GuildWarParticipant.war_id == war_id,
                    GuildWarParticipant.guild_id == guild_id,
                )
            )
            .order_by(GuildWarParticipant.contribution_score.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_war_scoreboard(
        self, war_id: uuid.UUID
    ) -> tuple[Sequence[GuildWarParticipant], Sequence[GuildWarParticipant]]:
        """获取公会战记分板。

        Args:
            war_id: 公会战ID

        Returns:
            tuple: (挑战方参与成员列表, 防守方参与成员列表)
        """
        war = await self.get_war(war_id)
        if war is None:
            return [], []

        challenger_participants = await self.get_war_participants(
            war_id, war.challenger_guild_id
        )
        defender_participants = await self.get_war_participants(
            war_id, war.defender_guild_id
        )

        return challenger_participants, defender_participants

    async def is_player_in_war(
        self, war_id: uuid.UUID, player_id: uuid.UUID
    ) -> bool:
        """检查玩家是否已加入某场公会战。

        Args:
            war_id: 公会战ID
            player_id: 玩家ID

        Returns:
            bool: 是否已加入
        """
        stmt = select(GuildWarParticipant).where(
            and_(
                GuildWarParticipant.war_id == war_id,
                GuildWarParticipant.player_id == player_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_player_participant(
        self, war_id: uuid.UUID, player_id: uuid.UUID
    ) -> GuildWarParticipant | None:
        """获取玩家在某场公会战中的参与记录。

        Args:
            war_id: 公会战ID
            player_id: 玩家ID

        Returns:
            GuildWarParticipant | None: 参与记录，不存在返回 None
        """
        stmt = select(GuildWarParticipant).where(
            and_(
                GuildWarParticipant.war_id == war_id,
                GuildWarParticipant.player_id == player_id,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def has_active_war_between(
        self, guild_id_a: uuid.UUID, guild_id_b: uuid.UUID
    ) -> bool:
        """检查两个公会之间是否有进行中的战争。

        Args:
            guild_id_a: 公会A ID
            guild_id_b: 公会B ID

        Returns:
            bool: 是否存在进行中的战争
        """
        stmt = select(GuildWar).where(
            and_(
                or_(
                    and_(
                        GuildWar.challenger_guild_id == guild_id_a,
                        GuildWar.defender_guild_id == guild_id_b,
                    ),
                    and_(
                        GuildWar.challenger_guild_id == guild_id_b,
                        GuildWar.defender_guild_id == guild_id_a,
                    ),
                ),
                GuildWar.status.in_(["declared", "accepted", "in_progress"]),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
