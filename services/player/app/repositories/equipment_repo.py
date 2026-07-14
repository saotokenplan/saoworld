import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import PlayerErrorCodes, raise_player_error
from app.domain.models import PlayerEquipment
from app.repositories.inventory_repo import InventoryRepository
from fastapi import status

VALID_SLOTS = {"head", "chest", "legs", "feet", "weapon", "off_hand", "ring", "necklace"}
EQUIPMENT_ITEM_TYPES = {"weapon", "armor", "accessory"}


class EquipmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_equipment(
        self, player_id: uuid.UUID
    ) -> Sequence[PlayerEquipment]:
        stmt: Select[tuple[PlayerEquipment]] = (
            select(PlayerEquipment)
            .where(PlayerEquipment.player_id == player_id)
            .order_by(PlayerEquipment.equipped_at.asc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_equipment_by_slot(
        self, player_id: uuid.UUID, slot: str
    ) -> PlayerEquipment | None:
        stmt: Select[tuple[PlayerEquipment]] = select(PlayerEquipment).where(
            PlayerEquipment.player_id == player_id,
            PlayerEquipment.slot == slot,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_equipment_stats(
        self, player_id: uuid.UUID
    ) -> dict[str, int]:
        equipment = await self.get_equipment(player_id)
        total_stats: dict[str, int] = {}
        for equip in equipment:
            if equip.stats_jsonb and isinstance(equip.stats_jsonb, dict):
                for stat_key, stat_value in equip.stats_jsonb.items():
                    if isinstance(stat_value, int | float):
                        total_stats[stat_key] = total_stats.get(stat_key, 0) + int(stat_value)
        return total_stats

    async def can_equip_item(
        self,
        player_id: uuid.UUID,
        item_key: str,
        item_type: str,
        level_requirement: int = 1,
    ) -> tuple[bool, str | None]:
        if item_type not in EQUIPMENT_ITEM_TYPES:
            return False, f"物品类型 {item_type} 不可装备"

        from app.repositories.player_repo import PlayerRepository

        player_repo = PlayerRepository(self.db)
        player = await player_repo.get_player_by_id(player_id)
        if player is None:
            return False, "玩家不存在"

        if player.level < level_requirement:
            return False, f"等级不足，需要 {level_requirement} 级，当前 {player.level} 级"

        inv_repo = InventoryRepository(self.db)
        inv_item = await inv_repo.get_item(player_id, item_key)
        if inv_item is None or inv_item.quantity < 1:
            return False, "背包中没有该物品"

        return True, None

    async def equip_item(
        self,
        player_id: uuid.UUID,
        item_key: str,
        slot: str,
        item_stats: dict[str, Any] | None = None,
    ) -> PlayerEquipment:
        if slot not in VALID_SLOTS:
            raise_player_error(
                PlayerErrorCodes.INVALID_EQUIPMENT_SLOT,
                f"无效的装备槽位: {slot}",
                "req_equip_item",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        existing = await self.get_equipment_by_slot(player_id, slot)
        if existing is not None:
            raise_player_error(
                PlayerErrorCodes.EQUIPMENT_SLOT_OCCUPIED,
                f"装备槽位 {slot} 已被占用",
                "req_equip_item",
                status_code=status.HTTP_409_CONFLICT,
            )

        inv_repo = InventoryRepository(self.db)
        inv_item = await inv_repo.get_item(player_id, item_key)
        if inv_item is None or inv_item.quantity < 1:
            raise_player_error(
                PlayerErrorCodes.ITEM_NOT_FOUND,
                f"背包中没有物品: {item_key}",
                "req_equip_item",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if inv_item.item_type != "equipment":
            raise_player_error(
                PlayerErrorCodes.ITEM_NOT_EQUIPPABLE,
                f"物品类型 {inv_item.item_type} 不可装备",
                "req_equip_item",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        await inv_repo.remove_item(player_id, item_key, quantity=1)

        equipment = PlayerEquipment(
            equipment_id=uuid.uuid4(),
            player_id=player_id,
            slot=slot,
            item_key=item_key,
            item_instance_id=uuid.uuid4(),
            level=0,
            stats_jsonb=item_stats,
            equipped_at=datetime.now(timezone.utc),
        )
        self.db.add(equipment)
        await self.db.flush()
        return equipment

    async def unequip_item(
        self, player_id: uuid.UUID, slot: str
    ) -> PlayerEquipment:
        if slot not in VALID_SLOTS:
            raise_player_error(
                PlayerErrorCodes.INVALID_EQUIPMENT_SLOT,
                f"无效的装备槽位: {slot}",
                "req_unequip_item",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        equipment = await self.get_equipment_by_slot(player_id, slot)
        if equipment is None:
            raise_player_error(
                PlayerErrorCodes.CANNOT_UNEQUIP_EMPTY_SLOT,
                f"槽位 {slot} 为空，无法卸下",
                "req_unequip_item",
                status_code=status.HTTP_409_CONFLICT,
            )

        inv_repo = InventoryRepository(self.db)
        await inv_repo.add_item(
            player_id=player_id,
            item_key=equipment.item_key,
            item_type="equipment",
            quantity=1,
        )

        await self.db.delete(equipment)
        await self.db.flush()
        return equipment
