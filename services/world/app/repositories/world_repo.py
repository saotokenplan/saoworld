import uuid
from typing import Any, Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import NPC, ItemDefinition, MonsterDefinition, QuestDefinition, Region, WorldSkeleton

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


class NpcRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_npcs(
        self,
        chapter_id: str | None = None,
        faction_key: str | None = None,
        player_reputation: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[NPC], int]:
        count_stmt = select(sa_func.count(NPC.npc_id))
        if chapter_id:
            count_stmt = count_stmt.where(NPC.chapter_id == chapter_id)
        if faction_key:
            count_stmt = count_stmt.where(NPC.faction_key == faction_key)
        if player_reputation is not None:
            count_stmt = count_stmt.where(NPC.min_reputation <= player_reputation)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[NPC]] = (
            select(NPC).order_by(NPC.created_at.asc()).limit(limit).offset(offset)
        )
        if chapter_id:
            stmt = stmt.where(NPC.chapter_id == chapter_id)
        if faction_key:
            stmt = stmt.where(NPC.faction_key == faction_key)
        if player_reputation is not None:
            stmt = stmt.where(NPC.min_reputation <= player_reputation)

        result = await self.db.execute(stmt)
        npcs = result.scalars().all()
        return npcs, total

    async def get_npc_by_id(self, npc_id: uuid.UUID) -> NPC | None:
        stmt: Select[tuple[NPC]] = select(NPC).where(NPC.npc_id == npc_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_npc_by_key(self, npc_key: str) -> NPC | None:
        stmt: Select[tuple[NPC]] = select(NPC).where(NPC.npc_key == npc_key)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_npc_by_key_for_chapter(self, npc_key: str, chapter_id: str) -> NPC | None:
        stmt: Select[tuple[NPC]] = select(NPC).where(
            (NPC.npc_key == npc_key) & (NPC.chapter_id == chapter_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_npc(
        self,
        *,
        npc_key: str,
        chapter_id: str,
        name: str,
        title: str | None = None,
        faction_key: str | None = None,
        role: str | None = None,
        location_key: str | None = None,
        description: str | None = None,
        personality: list[str] | None = None,
        dialogues: list[dict[str, Any]] | None = None,
        related_quests: list[str] | None = None,
        rewards: dict[str, Any] | None = None,
        min_reputation: int = 0,
        interaction_restrictions: dict[str, Any] | None = None,
    ) -> NPC:
        npc = NPC(
            npc_key=npc_key,
            chapter_id=chapter_id,
            name=name,
            title=title,
            faction_key=faction_key,
            role=role,
            location_key=location_key,
            description=description,
            personality=personality,
            dialogues=dialogues,
            related_quests=related_quests,
            rewards=rewards,
            min_reputation=min_reputation,
            interaction_restrictions_jsonb=interaction_restrictions,
        )
        self.db.add(npc)
        await self.db.flush()
        return npc


class QuestDefinitionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_quests(
        self,
        chapter_id: str | None = None,
        quest_type: str | None = None,
        region_key: str | None = None,
        player_reputation: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[QuestDefinition], int]:
        count_stmt = select(sa_func.count(QuestDefinition.quest_id))
        if chapter_id:
            count_stmt = count_stmt.where(QuestDefinition.chapter_id == chapter_id)
        if quest_type:
            count_stmt = count_stmt.where(QuestDefinition.quest_type == quest_type)
        if region_key:
            count_stmt = count_stmt.where(QuestDefinition.region_key == region_key)
        if player_reputation is not None:
            count_stmt = count_stmt.where(QuestDefinition.min_reputation <= player_reputation)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[QuestDefinition]] = (
            select(QuestDefinition)
            .order_by(QuestDefinition.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        if chapter_id:
            stmt = stmt.where(QuestDefinition.chapter_id == chapter_id)
        if quest_type:
            stmt = stmt.where(QuestDefinition.quest_type == quest_type)
        if region_key:
            stmt = stmt.where(QuestDefinition.region_key == region_key)
        if player_reputation is not None:
            stmt = stmt.where(QuestDefinition.min_reputation <= player_reputation)

        result = await self.db.execute(stmt)
        quests = result.scalars().all()
        return quests, total

    async def get_quest_by_id(self, quest_id: uuid.UUID) -> QuestDefinition | None:
        stmt: Select[tuple[QuestDefinition]] = select(QuestDefinition).where(
            QuestDefinition.quest_id == quest_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_quest_by_key(self, quest_key: str) -> QuestDefinition | None:
        stmt: Select[tuple[QuestDefinition]] = select(QuestDefinition).where(
            QuestDefinition.quest_key == quest_key
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_quest_by_key_for_chapter(
        self, quest_key: str, chapter_id: str
    ) -> QuestDefinition | None:
        stmt: Select[tuple[QuestDefinition]] = select(QuestDefinition).where(
            (QuestDefinition.quest_key == quest_key) & (QuestDefinition.chapter_id == chapter_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_quest(
        self,
        *,
        quest_key: str,
        chapter_id: str,
        title: str,
        quest_type: str,
        description: str | None = None,
        region_key: str | None = None,
        start_npc_key: str | None = None,
        end_npc_key: str | None = None,
        prerequisites: list[str] | None = None,
        objectives: list[dict[str, Any]],
        rewards: dict[str, Any] | None = None,
        failure_condition: dict[str, Any] | None = None,
        min_reputation: int = 0,
        required_reputation_level: str | None = None,
    ) -> QuestDefinition:
        quest = QuestDefinition(
            quest_key=quest_key,
            chapter_id=chapter_id,
            title=title,
            description=description,
            quest_type=quest_type,
            region_key=region_key,
            start_npc_key=start_npc_key,
            end_npc_key=end_npc_key,
            prerequisites=prerequisites,
            objectives=objectives,
            rewards=rewards,
            failure_condition=failure_condition,
            min_reputation=min_reputation,
            required_reputation_level=required_reputation_level,
        )
        self.db.add(quest)
        await self.db.flush()
        return quest


class ItemDefinitionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_items(
        self,
        item_type: str | None = None,
        rarity: str | None = None,
        chapter_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[ItemDefinition], int]:
        count_stmt = select(sa_func.count(ItemDefinition.item_id))
        if item_type:
            count_stmt = count_stmt.where(ItemDefinition.item_type == item_type)
        if rarity:
            count_stmt = count_stmt.where(ItemDefinition.rarity == rarity)
        if chapter_id:
            count_stmt = count_stmt.where(ItemDefinition.chapter_id == chapter_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[ItemDefinition]] = (
            select(ItemDefinition)
            .order_by(ItemDefinition.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if item_type:
            stmt = stmt.where(ItemDefinition.item_type == item_type)
        if rarity:
            stmt = stmt.where(ItemDefinition.rarity == rarity)
        if chapter_id:
            stmt = stmt.where(ItemDefinition.chapter_id == chapter_id)

        result = await self.db.execute(stmt)
        items = result.scalars().all()
        return items, total

    async def get_item_by_id(self, item_id: uuid.UUID) -> ItemDefinition | None:
        stmt: Select[tuple[ItemDefinition]] = select(ItemDefinition).where(
            ItemDefinition.item_id == item_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_item_by_key(self, item_key: str) -> ItemDefinition | None:
        stmt: Select[tuple[ItemDefinition]] = select(ItemDefinition).where(
            ItemDefinition.item_key == item_key
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_item(
        self,
        *,
        item_key: str,
        item_type: str,
        name: str,
        rarity: str,
        chapter_id: str,
        item_slot: str | None = None,
        description: str | None = None,
        level_requirement: int = 1,
        stats: dict[str, Any] | None = None,
        effects: dict[str, Any] | None = None,
        sell_price: int = 0,
        stackable: bool = False,
    ) -> ItemDefinition:
        item = ItemDefinition(
            item_key=item_key,
            item_type=item_type,
            item_slot=item_slot,
            name=name,
            description=description,
            rarity=rarity,
            chapter_id=chapter_id,
            level_requirement=level_requirement,
            stats_jsonb=stats,
            effects_jsonb=effects,
            sell_price=sell_price,
            stackable=stackable,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def update_item(
        self, item_id: uuid.UUID, **kwargs: Any
    ) -> ItemDefinition | None:
        from sqlalchemy import update as sa_update

        if not kwargs:
            return await self.get_item_by_id(item_id)

        stmt = (
            sa_update(ItemDefinition)
            .where(ItemDefinition.item_id == item_id)
            .values(**kwargs)
            .returning(ItemDefinition)
        )
        result = await self.db.execute(stmt)
        updated = result.scalar_one_or_none()
        await self.db.flush()
        return updated

    async def delete_item(self, item_id: uuid.UUID) -> bool:
        item = await self.get_item_by_id(item_id)
        if item is None:
            return False
        await self.db.delete(item)
        await self.db.flush()
        return True


class MonsterDefinitionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_monsters(
        self,
        monster_type: str | None = None,
        chapter_id: str | None = None,
        region_key: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[MonsterDefinition], int]:
        count_stmt = select(sa_func.count(MonsterDefinition.monster_id))
        if monster_type:
            count_stmt = count_stmt.where(MonsterDefinition.monster_type == monster_type)
        if chapter_id:
            count_stmt = count_stmt.where(MonsterDefinition.chapter_id == chapter_id)
        if region_key:
            count_stmt = count_stmt.where(MonsterDefinition.region_key == region_key)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[MonsterDefinition]] = (
            select(MonsterDefinition)
            .order_by(MonsterDefinition.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if monster_type:
            stmt = stmt.where(MonsterDefinition.monster_type == monster_type)
        if chapter_id:
            stmt = stmt.where(MonsterDefinition.chapter_id == chapter_id)
        if region_key:
            stmt = stmt.where(MonsterDefinition.region_key == region_key)

        result = await self.db.execute(stmt)
        monsters = result.scalars().all()
        return monsters, total

    async def get_monster_by_id(self, monster_id: uuid.UUID) -> MonsterDefinition | None:
        stmt: Select[tuple[MonsterDefinition]] = select(MonsterDefinition).where(
            MonsterDefinition.monster_id == monster_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_monster_by_key(self, monster_key: str) -> MonsterDefinition | None:
        stmt: Select[tuple[MonsterDefinition]] = select(MonsterDefinition).where(
            MonsterDefinition.monster_key == monster_key
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_monster(
        self,
        *,
        monster_key: str,
        name: str,
        monster_type: str,
        chapter_id: str,
        region_key: str | None = None,
        level: int = 1,
        hp: int = 10,
        attack: int = 5,
        defense: int = 0,
        speed: int = 5,
        description: str | None = None,
        behavior_pattern: dict[str, Any] | None = None,
        loot_table: list[dict[str, Any]] | None = None,
        skills: list[dict[str, Any]] | None = None,
        min_reputation: int = 0,
    ) -> MonsterDefinition:
        monster = MonsterDefinition(
            monster_key=monster_key,
            name=name,
            monster_type=monster_type,
            chapter_id=chapter_id,
            region_key=region_key,
            level=level,
            hp=hp,
            attack=attack,
            defense=defense,
            speed=speed,
            description=description,
            behavior_pattern_jsonb=behavior_pattern,
            loot_table_jsonb=loot_table,
            skills_jsonb=skills,
            min_reputation=min_reputation,
        )
        self.db.add(monster)
        await self.db.flush()
        return monster

    async def list_bosses(
        self,
        region_key: str | None = None,
        chapter_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[Sequence[MonsterDefinition], int]:
        count_stmt = select(sa_func.count(MonsterDefinition.monster_id)).where(
            MonsterDefinition.is_boss == True
        )
        if region_key:
            count_stmt = count_stmt.where(MonsterDefinition.region_key == region_key)
        if chapter_id:
            count_stmt = count_stmt.where(MonsterDefinition.chapter_id == chapter_id)
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt: Select[tuple[MonsterDefinition]] = (
            select(MonsterDefinition)
            .where(MonsterDefinition.is_boss == True)
            .order_by(MonsterDefinition.level.desc())
            .limit(limit)
            .offset(offset)
        )
        if region_key:
            stmt = stmt.where(MonsterDefinition.region_key == region_key)
        if chapter_id:
            stmt = stmt.where(MonsterDefinition.chapter_id == chapter_id)

        result = await self.db.execute(stmt)
        bosses = result.scalars().all()
        return bosses, total

    async def get_boss_by_key(self, monster_key: str) -> MonsterDefinition | None:
        stmt: Select[tuple[MonsterDefinition]] = select(MonsterDefinition).where(
            MonsterDefinition.monster_key == monster_key,
            MonsterDefinition.is_boss == True,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_boss(
        self,
        *,
        monster_key: str,
        name: str,
        chapter_id: str,
        region_key: str,
        level: int = 10,
        hp: int = 500,
        attack: int = 30,
        defense: int = 10,
        speed: int = 5,
        description: str | None = None,
        behavior_pattern: dict[str, Any] | None = None,
        loot_table: list[dict[str, Any]] | None = None,
        skills: list[dict[str, Any]] | None = None,
        min_reputation: int = 0,
        boss_rank: str = "legendary",
        phase_count: int = 1,
        special_skills: list[dict[str, Any]] | None = None,
        enrage_threshold: float = 0.3,
        reward: dict[str, Any] | None = None,
    ) -> MonsterDefinition:
        boss = MonsterDefinition(
            monster_key=monster_key,
            name=name,
            monster_type="boss",
            chapter_id=chapter_id,
            region_key=region_key,
            level=level,
            hp=hp,
            attack=attack,
            defense=defense,
            speed=speed,
            description=description,
            behavior_pattern_jsonb=behavior_pattern,
            loot_table_jsonb=loot_table,
            skills_jsonb=skills,
            min_reputation=min_reputation,
            is_boss=True,
            boss_rank=boss_rank,
            phase_count=phase_count,
            special_skills_jsonb=special_skills,
            enrage_threshold=enrage_threshold,
            reward_jsonb=reward,
        )
        self.db.add(boss)
        await self.db.flush()
        return boss
