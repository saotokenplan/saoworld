import uuid
from typing import Any, Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import Region, WorldSkeleton

VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "locked": {"active"},
    "active": {"unstable", "archived", "locked"},
    "unstable": {"active", "archived", "locked"},
    "archived": set(),
}


class WorldRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_visible_regions(
        self, chapter_id: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[Region], int]:
        count_stmt = select(sa_func.count(Region.region_id)).where(Region.visible)
        if chapter_id:
            count_stmt = count_stmt.where(Region.chapter_id == chapter_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[Region]] = (
            select(Region)
            .where(Region.visible)
            .order_by(Region.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        if chapter_id:
            stmt = stmt.where(Region.chapter_id == chapter_id)

        result = await self.db.execute(stmt)
        regions = result.scalars().all()
        return regions, total

    async def get_region_by_id(self, region_id: uuid.UUID) -> Region | None:
        stmt: Select[tuple[Region]] = select(Region).where(Region.region_id == region_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_region(
        self,
        *,
        chapter_id: str,
        title: str,
        summary: str | None = None,
        status: str = "locked",
        visible: bool = False,
        unlock_condition: dict[str, Any] | None = None,
    ) -> Region:
        region = Region(
            chapter_id=chapter_id,
            title=title,
            summary=summary,
            status=status,
            visible=visible,
            unlock_condition_jsonb=unlock_condition,
        )
        self.db.add(region)
        await self.db.flush()
        return region

    async def update_region_status(
        self, region_id: uuid.UUID, new_status: str
    ) -> Region | None:
        region = await self.get_region_by_id(region_id)
        if region is None:
            return None
        region.status = new_status
        await self.db.flush()
        return region

    async def list_all_regions(
        self,
        chapter_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[Region], int]:
        count_stmt = select(sa_func.count(Region.region_id))
        if chapter_id:
            count_stmt = count_stmt.where(Region.chapter_id == chapter_id)
        if status:
            count_stmt = count_stmt.where(Region.status == status)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[Region]] = (
            select(Region)
            .order_by(Region.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        if chapter_id:
            stmt = stmt.where(Region.chapter_id == chapter_id)
        if status:
            stmt = stmt.where(Region.status == status)

        result = await self.db.execute(stmt)
        regions = result.scalars().all()
        return regions, total

    @staticmethod
    def is_valid_status_transition(current_status: str, new_status: str) -> bool:
        allowed = VALID_STATUS_TRANSITIONS.get(current_status, set())
        return new_status in allowed

    async def create_skeleton(
        self,
        *,
        world_version: str,
        chapter_id: str,
        regions: dict[str, Any],
        factions: dict[str, Any],
        forbidden_tags: list[str],
        reserved_characters: dict[str, Any] | None = None,
        reward_limits: dict[str, Any] | None = None,
        is_active: bool = True,
    ) -> WorldSkeleton:
        skeleton = WorldSkeleton(
            world_version=world_version,
            chapter_id=chapter_id,
            regions=regions,
            factions=factions,
            forbidden_tags=forbidden_tags,
            reserved_characters=reserved_characters,
            reward_limits=reward_limits,
            is_active=is_active,
        )
        self.db.add(skeleton)
        await self.db.flush()
        return skeleton

    async def get_current_skeleton(self) -> WorldSkeleton | None:
        stmt: Select[tuple[WorldSkeleton]] = (
            select(WorldSkeleton)
            .where(WorldSkeleton.is_active)
            .order_by(WorldSkeleton.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_skeleton_by_version(self, world_version: str) -> WorldSkeleton | None:
        stmt: Select[tuple[WorldSkeleton]] = select(WorldSkeleton).where(
            WorldSkeleton.world_version == world_version
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_skeleton(
        self,
        skeleton_id: uuid.UUID,
        **kwargs: Any,
    ) -> WorldSkeleton | None:
        skeleton = await self.db.get(WorldSkeleton, skeleton_id)
        if skeleton is None:
            return None
        for key, value in kwargs.items():
            setattr(skeleton, key, value)
        await self.db.flush()
        return skeleton

    async def deactivate_skeleton(self, skeleton_id: uuid.UUID) -> WorldSkeleton | None:
        return await self.update_skeleton(skeleton_id, is_active=False)
