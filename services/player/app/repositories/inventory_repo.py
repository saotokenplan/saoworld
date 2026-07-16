import uuid
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy import Select, func as sa_func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import PlayerErrorCodes, raise_player_error
from app.domain.models import PlayerInventory
from fastapi import status


class InventoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_inventory(
        self, player_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> tuple[Sequence[PlayerInventory], int]:
        count_stmt = select(sa_func.count(PlayerInventory.inventory_id)).where(
            PlayerInventory.player_id == player_id
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        stmt = (
            select(PlayerInventory)
            .where(PlayerInventory.player_id == player_id)
            .order_by(PlayerInventory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return rows, total

    async def get_item(
        self, player_id: uuid.UUID, item_key: str
    ) -> PlayerInventory | None:
        stmt: Select[tuple[PlayerInventory]] = select(PlayerInventory).where(
            PlayerInventory.player_id == player_id,
            PlayerInventory.item_key == item_key,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def add_item(
        self,
        player_id: uuid.UUID,
        item_key: str,
        item_type: str,
        quantity: int = 1,
        metadata_jsonb: dict | None = None,
    ) -> PlayerInventory:
        valid_types = {"consumable", "equipment", "material", "quest_item"}
        if item_type not in valid_types:
            raise_player_error(
                PlayerErrorCodes.INVALID_ITEM_TYPE,
                f"无效的物品类型: {item_type}",
                "req_inventory_add",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        existing = await self.get_item(player_id, item_key)
        if existing is not None:
            existing.quantity += quantity
            if metadata_jsonb is not None:
                existing.metadata_jsonb = metadata_jsonb
            existing.updated_at = datetime.now(timezone.utc)
            await self.db.flush()
            return existing

        item = PlayerInventory(
            inventory_id=uuid.uuid4(),
            player_id=player_id,
            item_key=item_key,
            item_type=item_type,
            quantity=quantity,
            metadata_jsonb=metadata_jsonb,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def remove_item(
        self, player_id: uuid.UUID, item_key: str, quantity: int = 1
    ) -> PlayerInventory:
        item = await self.get_item(player_id, item_key)
        if item is None:
            raise_player_error(
                PlayerErrorCodes.ITEM_NOT_FOUND,
                f"物品不存在: {item_key}",
                "req_inventory_remove",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if item.quantity < quantity:
            raise_player_error(
                PlayerErrorCodes.INSUFFICIENT_QUANTITY,
                f"物品数量不足: {item_key}，当前 {item.quantity}，需要 {quantity}",
                "req_inventory_remove",
                status_code=status.HTTP_409_CONFLICT,
            )

        if item.quantity == quantity:
            await self.db.delete(item)
            await self.db.flush()
            return item

        item.quantity -= quantity
        item.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return item

    async def has_item(
        self, player_id: uuid.UUID, item_key: str, quantity: int = 1
    ) -> bool:
        stmt: Select[tuple[PlayerInventory]] = select(PlayerInventory).where(
            PlayerInventory.player_id == player_id,
            PlayerInventory.item_key == item_key,
            PlayerInventory.quantity >= quantity,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def use_item(
        self, player_id: uuid.UUID, item_key: str, quantity: int = 1
    ) -> PlayerInventory:
        item = await self.get_item(player_id, item_key)
        if item is None:
            raise_player_error(
                PlayerErrorCodes.ITEM_NOT_FOUND,
                f"物品不存在: {item_key}",
                "req_inventory_use",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if item.item_type != "consumable":
            raise_player_error(
                PlayerErrorCodes.INVALID_ITEM_TYPE,
                f"物品类型 {item.item_type} 不可使用，只有消耗品可以使用",
                "req_inventory_use",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        if item.quantity < quantity:
            raise_player_error(
                PlayerErrorCodes.INSUFFICIENT_QUANTITY,
                f"物品数量不足: {item_key}，当前 {item.quantity}，需要 {quantity}",
                "req_inventory_use",
                status_code=status.HTTP_409_CONFLICT,
            )

        if item.quantity == quantity:
            await self.db.delete(item)
            await self.db.flush()
            return item

        item.quantity -= quantity
        item.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        return item
