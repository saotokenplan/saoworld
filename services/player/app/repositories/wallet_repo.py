from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import PlayerWallet, WalletTransaction

MAX_GOLD = 9999999


class WalletRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_wallet(self, player_id: Any) -> PlayerWallet:
        result = await self.db.execute(
            select(PlayerWallet).where(PlayerWallet.player_id == player_id)
        )
        wallet = result.scalar_one_or_none()

        if wallet is None:
            wallet = PlayerWallet(player_id=player_id, gold_coins=0)
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)

        return wallet

    async def get_wallet(self, player_id: Any) -> PlayerWallet | None:
        result = await self.db.execute(
            select(PlayerWallet).where(PlayerWallet.player_id == player_id)
        )
        return result.scalar_one_or_none()

    async def add_coins(
        self, player_id: Any, amount: int, transaction_type: str, description: str | None = None,
        reference_id: str | None = None
    ) -> PlayerWallet | None:
        wallet = await self.get_or_create_wallet(player_id)
        if wallet is None:
            return None

        balance_before = wallet.gold_coins
        balance_after = balance_before + amount

        if balance_after > MAX_GOLD:
            return None

        wallet.gold_coins = balance_after

        transaction = WalletTransaction(
            wallet_id=wallet.wallet_id,
            player_id=player_id,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            reference_id=reference_id,
        )
        self.db.add(transaction)

        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet

    async def spend_coins(
        self, player_id: Any, amount: int, transaction_type: str, description: str | None = None,
        reference_id: str | None = None
    ) -> PlayerWallet | None:
        wallet = await self.get_wallet(player_id)
        if wallet is None or wallet.gold_coins < amount:
            return None

        balance_before = wallet.gold_coins
        balance_after = balance_before - amount

        wallet.gold_coins = balance_after

        transaction = WalletTransaction(
            wallet_id=wallet.wallet_id,
            player_id=player_id,
            transaction_type=transaction_type,
            amount=-amount,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            reference_id=reference_id,
        )
        self.db.add(transaction)

        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet

    async def transfer_coins(
        self, from_player_id: Any, to_player_id: Any, amount: int, reference_id: str | None = None
    ) -> bool:
        from_wallet = await self.get_wallet(from_player_id)
        to_wallet = await self.get_or_create_wallet(to_player_id)

        if from_wallet is None or from_wallet.gold_coins < amount:
            return False

        from_balance_before = from_wallet.gold_coins
        from_wallet.gold_coins -= amount
        from_balance_after = from_wallet.gold_coins

        to_balance_before = to_wallet.gold_coins
        to_wallet.gold_coins += amount
        to_balance_after = to_wallet.gold_coins

        from_transaction = WalletTransaction(
            wallet_id=from_wallet.wallet_id,
            player_id=from_player_id,
            transaction_type="trade_send",
            amount=-amount,
            balance_before=from_balance_before,
            balance_after=from_balance_after,
            description="交易转账",
            reference_id=reference_id,
        )
        self.db.add(from_transaction)

        to_transaction = WalletTransaction(
            wallet_id=to_wallet.wallet_id,
            player_id=to_player_id,
            transaction_type="trade_receive",
            amount=amount,
            balance_before=to_balance_before,
            balance_after=to_balance_after,
            description="交易收款",
            reference_id=reference_id,
        )
        self.db.add(to_transaction)

        await self.db.commit()
        return True

    async def get_transactions(
        self, player_id: Any, transaction_type: str | None = None,
        limit: int = 20, offset: int = 0
    ) -> tuple[list[WalletTransaction], int]:
        query = select(WalletTransaction).where(WalletTransaction.player_id == player_id)

        if transaction_type is not None:
            query = query.where(WalletTransaction.transaction_type == transaction_type)

        count_query = select(func.count()).select_from(WalletTransaction).where(
            WalletTransaction.player_id == player_id
        )
        if transaction_type is not None:
            count_query = count_query.where(WalletTransaction.transaction_type == transaction_type)

        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        query = query.order_by(WalletTransaction.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        return transactions, total