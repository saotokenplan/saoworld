from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import PlayerTrade, TradeCoin, TradeItem
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.wallet_repo import WalletRepository


class TradeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_trade(
        self,
        initiator_id: Any,
        recipient_id: Any,
        offer_items: list[dict] = [],
        offer_coins: int = 0,
        request_items: list[dict] = [],
        request_coins: int = 0,
    ) -> PlayerTrade:
        trade = PlayerTrade(
            initiator_id=initiator_id,
            recipient_id=recipient_id,
            status="pending",
        )
        self.db.add(trade)
        await self.db.flush()

        for item in offer_items:
            trade_item = TradeItem(
                trade_id=trade.trade_id,
                from_player_id=initiator_id,
                item_key=item["item_key"],
                item_type=item["item_type"],
                quantity=item["quantity"],
            )
            self.db.add(trade_item)

        if offer_coins > 0:
            trade_coin = TradeCoin(
                trade_id=trade.trade_id,
                from_player_id=initiator_id,
                amount=offer_coins,
            )
            self.db.add(trade_coin)

        for item in request_items:
            trade_item = TradeItem(
                trade_id=trade.trade_id,
                from_player_id=recipient_id,
                item_key=item["item_key"],
                item_type=item["item_type"],
                quantity=item["quantity"],
            )
            self.db.add(trade_item)

        if request_coins > 0:
            trade_coin = TradeCoin(
                trade_id=trade.trade_id,
                from_player_id=recipient_id,
                amount=request_coins,
            )
            self.db.add(trade_coin)

        await self.db.commit()
        await self.db.refresh(trade)
        return trade

    async def get_trade_by_id(self, trade_id: Any) -> PlayerTrade | None:
        result = await self.db.execute(
            select(PlayerTrade).where(PlayerTrade.trade_id == trade_id)
        )
        return result.scalar_one_or_none()

    async def get_trades_by_player(
        self, player_id: Any, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[PlayerTrade], int]:
        query = select(PlayerTrade).where(
            (PlayerTrade.initiator_id == player_id) | (PlayerTrade.recipient_id == player_id)
        )

        if status is not None:
            query = query.where(PlayerTrade.status == status)

        count_query = select(func.count()).select_from(PlayerTrade).where(
            (PlayerTrade.initiator_id == player_id) | (PlayerTrade.recipient_id == player_id)
        )
        if status is not None:
            count_query = count_query.where(PlayerTrade.status == status)

        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        query = query.order_by(PlayerTrade.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        trades = result.scalars().all()
        return trades, total

    async def accept_trade(self, trade_id: Any, player_id: Any) -> PlayerTrade | None:
        trade = await self.get_trade_by_id(trade_id)
        if trade is None or trade.status != "pending":
            return None

        if trade.recipient_id != player_id:
            return None

        inventory_repo = InventoryRepository(self.db)
        wallet_repo = WalletRepository(self.db)

        offer_items = await self.get_trade_items(trade_id, trade.initiator_id)
        request_items = await self.get_trade_items(trade_id, trade.recipient_id)
        offer_coins = await self.get_trade_coins(trade_id, trade.initiator_id)
        request_coins = await self.get_trade_coins(trade_id, trade.recipient_id)

        for item in offer_items:
            await inventory_repo.remove_item(trade.initiator_id, item.item_key, item.quantity)
            await inventory_repo.add_item(
                trade.recipient_id, item.item_key, item.item_type, item.quantity
            )

        for item in request_items:
            await inventory_repo.remove_item(trade.recipient_id, item.item_key, item.quantity)
            await inventory_repo.add_item(
                trade.initiator_id, item.item_key, item.item_type, item.quantity
            )

        if offer_coins:
            for coin in offer_coins:
                await wallet_repo.transfer_coins(
                    trade.initiator_id, trade.recipient_id, coin.amount, "trade_send"
                )

        if request_coins:
            for coin in request_coins:
                await wallet_repo.transfer_coins(
                    trade.recipient_id, trade.initiator_id, coin.amount, "trade_send"
                )

        trade.status = "completed"
        await self.db.commit()
        await self.db.refresh(trade)
        return trade

    async def reject_trade(self, trade_id: Any, player_id: Any) -> PlayerTrade | None:
        trade = await self.get_trade_by_id(trade_id)
        if trade is None or trade.status != "pending":
            return None

        if trade.recipient_id != player_id:
            return None

        trade.status = "rejected"
        await self.db.commit()
        await self.db.refresh(trade)
        return trade

    async def cancel_trade(self, trade_id: Any, player_id: Any) -> PlayerTrade | None:
        trade = await self.get_trade_by_id(trade_id)
        if trade is None:
            return None

        if trade.status not in ["pending"]:
            return None

        if trade.initiator_id != player_id:
            return None

        trade.status = "cancelled"
        await self.db.commit()
        await self.db.refresh(trade)
        return trade

    async def get_trade_items(self, trade_id: Any, from_player_id: Any) -> list[TradeItem]:
        result = await self.db.execute(
            select(TradeItem).where(
                TradeItem.trade_id == trade_id,
                TradeItem.from_player_id == from_player_id,
            )
        )
        return result.scalars().all()

    async def get_trade_coins(self, trade_id: Any, from_player_id: Any) -> list[TradeCoin]:
        result = await self.db.execute(
            select(TradeCoin).where(
                TradeCoin.trade_id == trade_id,
                TradeCoin.from_player_id == from_player_id,
            )
        )
        return result.scalars().all()

    async def get_player_trades(
        self, player_id: Any, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[PlayerTrade], int]:
        return await self.get_trades_by_player(player_id, status, limit, offset)