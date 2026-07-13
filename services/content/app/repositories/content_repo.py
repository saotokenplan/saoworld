import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import ContentPackage, ReleaseRecord, RollbackRecord


VALID_TRANSITIONS: dict[str, set[str]] = {
    "packaged": {"gray"},
    "gray": {"live", "rolled_back"},
    "live": {"archived", "rolled_back"},
    "archived": set(),
    "rolled_back": set(),
}


def is_player_in_gray_scope(
    gray_scope: dict[str, Any] | None,
    player_id: str,
    player_region_id: str | None = None,
) -> bool:
    if gray_scope is None or not gray_scope:
        return False

    player_ids = gray_scope.get("player_ids", [])
    if player_ids:
        return str(player_id) in [str(pid) for pid in player_ids]

    player_percent = gray_scope.get("player_percent")
    if player_percent is not None and isinstance(player_percent, (int, float)) and 0 < player_percent <= 100:
        hash_input = f"{player_id}_gray_bucket"
        hash_val = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_val % 100) + 1
        result: bool = bucket <= player_percent
        return result

    region_ids = gray_scope.get("region_ids", [])
    if region_ids and player_region_id:
        return str(player_region_id) in [str(rid) for rid in region_ids]

    return False


class ContentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_package_by_id(self, package_id: uuid.UUID) -> ContentPackage | None:
        result = await self.db.execute(
            select(ContentPackage).where(ContentPackage.content_package_id == package_id)
        )
        return result.scalar_one_or_none()

    async def get_package_by_vote_cycle_id(self, vote_cycle_id: uuid.UUID) -> ContentPackage | None:
        result = await self.db.execute(
            select(ContentPackage).where(ContentPackage.source_vote_cycle_id == vote_cycle_id)
        )
        return result.scalar_one_or_none()

    async def get_packages_by_vote_cycle_ids(
        self, vote_cycle_ids: list[uuid.UUID]
    ) -> list[ContentPackage]:
        """根据多个投票周期 ID 批量查询内容包。

        Args:
            vote_cycle_ids: 投票周期 ID 列表

        Returns:
            匹配的内容包列表（保持输入顺序无关，由数据库排序）
        """
        if not vote_cycle_ids:
            return []

        result = await self.db.execute(
            select(ContentPackage)
            .where(ContentPackage.source_vote_cycle_id.in_(vote_cycle_ids))
            .order_by(ContentPackage.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_visible_packages(
        self,
        chapter_id: str | None = None,
        player_id: str | None = None,
        player_region_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ContentPackage], int]:
        if not player_id:
            query = select(ContentPackage).where(
                ContentPackage.status.in_(["gray", "live"])
            )
            count_query = select(func.count(ContentPackage.content_package_id)).where(
                ContentPackage.status.in_(["gray", "live"])
            )

            if chapter_id:
                query = query.where(ContentPackage.chapter_id == chapter_id)
                count_query = count_query.where(ContentPackage.chapter_id == chapter_id)

            query = query.order_by(ContentPackage.released_at.desc().nullslast())
            query = query.offset(offset).limit(limit)

            result = await self.db.execute(query)
            packages = list(result.scalars().all())

            count_result = await self.db.execute(count_query)
            total = count_result.scalar_one()

            return packages, total

        query = select(ContentPackage).where(
            ContentPackage.status.in_(["gray", "live"])
        )
        if chapter_id:
            query = query.where(ContentPackage.chapter_id == chapter_id)
        query = query.order_by(ContentPackage.released_at.desc().nullslast())

        result = await self.db.execute(query)
        all_packages = list(result.scalars().all())

        visible_packages: list[ContentPackage] = []
        for pkg in all_packages:
            if pkg.status == "live":
                visible_packages.append(pkg)
            elif pkg.status == "gray":
                if is_player_in_gray_scope(
                    pkg.gray_scope_jsonb, player_id, player_region_id
                ):
                    visible_packages.append(pkg)

        total = len(visible_packages)
        paginated = visible_packages[offset : offset + limit]

        return paginated, total

    async def list_all_packages(
        self,
        chapter_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ContentPackage], int]:
        query = select(ContentPackage)
        count_query = select(func.count(ContentPackage.content_package_id))

        conditions: list[Any] = []
        if chapter_id:
            conditions.append(ContentPackage.chapter_id == chapter_id)
        if status:
            conditions.append(ContentPackage.status == status)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        query = query.order_by(ContentPackage.created_at.desc())
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        packages = list(result.scalars().all())

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        return packages, total

    async def create_package(
        self,
        chapter_id: str,
        package_version: str,
        title: str,
        payload: dict[str, Any],
        region_id: uuid.UUID | None = None,
        source_vote_cycle_id: uuid.UUID | None = None,
        source_request_id: uuid.UUID | None = None,
        summary: str | None = None,
        schema_version: int = 1,
    ) -> ContentPackage:
        pkg = ContentPackage(
            chapter_id=chapter_id,
            region_id=region_id,
            package_version=package_version,
            source_vote_cycle_id=source_vote_cycle_id,
            source_request_id=source_request_id,
            title=title,
            summary=summary,
            status="packaged",
            payload_jsonb=payload,
            schema_version=schema_version,
        )
        self.db.add(pkg)
        await self.db.flush()
        await self.db.refresh(pkg)
        return pkg

    def can_transition(self, from_status: str, to_status: str) -> bool:
        return to_status in VALID_TRANSITIONS.get(from_status, set())

    async def release_package(
        self,
        package_id: uuid.UUID,
        release_mode: str,
        operator_id: str,
        reason: str,
        trace_id: str,
        gray_scope: dict[str, Any] | None = None,
    ) -> ContentPackage:
        pkg = await self.get_package_by_id(package_id)
        if not pkg:
            raise ValueError("PACKAGE_NOT_FOUND")

        target_status = "gray" if release_mode == "gray" else "live"
        if not self.can_transition(pkg.status, target_status):
            raise ValueError("INVALID_PACKAGE_STATE")

        if release_mode == "full" and pkg.status != "gray":
            raise ValueError("INVALID_PACKAGE_STATE")

        pkg.status = target_status
        pkg.released_at = datetime.now(timezone.utc)
        if gray_scope:
            pkg.gray_scope_jsonb = gray_scope

        release_record = ReleaseRecord(
            content_package_id=package_id,
            release_mode=release_mode,
            status="completed",
            gray_scope_jsonb=gray_scope,
            operator_id=operator_id,
            reason=reason,
            trace_id=trace_id,
            released_at=datetime.now(timezone.utc),
        )
        self.db.add(release_record)

        await self.db.flush()
        await self.db.refresh(pkg)
        return pkg

    async def rollback_package(
        self,
        package_id: uuid.UUID,
        target_version: str,
        reason: str,
        operator_id: str,
        trace_id: str,
    ) -> ContentPackage:
        pkg = await self.get_package_by_id(package_id)
        if not pkg:
            raise ValueError("PACKAGE_NOT_FOUND")

        if not self.can_transition(pkg.status, "rolled_back"):
            raise ValueError("INVALID_PACKAGE_STATE")

        pkg.status = "rolled_back"

        rollback_record = RollbackRecord(
            content_package_id=package_id,
            target_version=target_version,
            rollback_reason=reason,
            operator_type="ops",
            operator_id=operator_id,
            status="completed",
            trace_id=trace_id,
            rolled_back_at=datetime.now(timezone.utc),
        )
        self.db.add(rollback_record)

        await self.db.flush()
        await self.db.refresh(pkg)
        return pkg
