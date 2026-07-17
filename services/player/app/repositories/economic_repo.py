from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models import AuctionListing, PlayerTrade, PlayerWallet, WalletTransaction


class EconomicRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_economy_overview(self) -> dict[str, Any]:
        total_trades_result = await self.db.execute(
            select(func.count(PlayerTrade.trade_id))
        )
        total_trades = total_trades_result.scalar() or 0

        completed_trades_result = await self.db.execute(
            select(func.count(PlayerTrade.trade_id)).where(
                PlayerTrade.status == "completed"
            )
        )
        completed_trades = completed_trades_result.scalar() or 0

        total_auctions_result = await self.db.execute(
            select(func.count(AuctionListing.listing_id))
        )
        total_auctions = total_auctions_result.scalar() or 0

        active_auctions_result = await self.db.execute(
            select(func.count(AuctionListing.listing_id)).where(
                AuctionListing.status == "active"
            )
        )
        active_auctions = active_auctions_result.scalar() or 0

        sold_auctions_result = await self.db.execute(
            select(func.count(AuctionListing.listing_id)).where(
                AuctionListing.status == "sold"
            )
        )
        sold_auctions = sold_auctions_result.scalar() or 0

        total_wallets_result = await self.db.execute(
            select(func.count(PlayerWallet.wallet_id))
        )
        total_wallets = total_wallets_result.scalar() or 0

        total_gold_supply_result = await self.db.execute(
            select(func.sum(PlayerWallet.gold_coins))
        )
        total_gold_supply = total_gold_supply_result.scalar() or 0

        total_transactions_result = await self.db.execute(
            select(func.count(WalletTransaction.transaction_id))
        )
        total_transactions = total_transactions_result.scalar() or 0

        trade_completion_rate = (
            round(completed_trades / total_trades * 100, 2) if total_trades > 0 else 0.0
        )

        return {
            "total_trades": total_trades,
            "completed_trades": completed_trades,
            "trade_completion_rate": trade_completion_rate,
            "total_auctions": total_auctions,
            "active_auctions": active_auctions,
            "sold_auctions": sold_auctions,
            "total_wallets": total_wallets,
            "total_gold_supply": total_gold_supply,
            "total_transactions": total_transactions,
        }

    async def get_trade_stats(
        self, days: int = 7, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        count_query = select(func.count(func.distinct(func.date(PlayerTrade.created_at)))).where(
            PlayerTrade.created_at >= start_date
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(
                func.date(PlayerTrade.created_at).label("date"),
                func.count(PlayerTrade.trade_id).label("total_trades"),
                func.sum(
                    func.case(
                        (PlayerTrade.status == "completed", 1),
                        else_=0,
                    )
                ).label("completed_trades"),
                func.sum(
                    func.case(
                        (PlayerTrade.status == "cancelled", 1),
                        else_=0,
                    )
                ).label("cancelled_trades"),
            )
            .where(PlayerTrade.created_at >= start_date)
            .group_by(func.date(PlayerTrade.created_at))
            .order_by(func.date(PlayerTrade.created_at).desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        rows = result.all()

        stats = []
        for row in rows:
            date_val = row.date
            total_trades = row.total_trades
            completed_trades = row.completed_trades
            completion_rate = (
                round(completed_trades / total_trades * 100, 2)
                if total_trades > 0
                else 0.0
            )
            stats.append(
                {
                    "date": str(date_val),
                    "total_trades": total_trades,
                    "completed_trades": completed_trades,
                    "cancelled_trades": row.cancelled_trades,
                    "completion_rate": completion_rate,
                }
            )

        return stats, total

    async def get_auction_stats(
        self, days: int = 7, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        count_query = select(func.count(func.distinct(func.date(AuctionListing.created_at)))).where(
            AuctionListing.created_at >= start_date
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(
                func.date(AuctionListing.created_at).label("date"),
                func.count(AuctionListing.listing_id).label("total_listings"),
                func.sum(
                    func.case(
                        (AuctionListing.status == "sold", 1),
                        else_=0,
                    )
                ).label("sold_listings"),
                func.sum(
                    func.case(
                        (AuctionListing.status == "active", 1),
                        else_=0,
                    )
                ).label("active_listings"),
                func.sum(
                    func.case(
                        (AuctionListing.status == "sold", AuctionListing.current_price),
                        else_=0,
                    )
                ).label("total_volume"),
            )
            .where(AuctionListing.created_at >= start_date)
            .group_by(func.date(AuctionListing.created_at))
            .order_by(func.date(AuctionListing.created_at).desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        rows = result.all()

        stats = []
        for row in rows:
            date_val = row.date
            total_listings = row.total_listings
            sold_listings = row.sold_listings
            sell_through_rate = (
                round(sold_listings / total_listings * 100, 2)
                if total_listings > 0
                else 0.0
            )
            stats.append(
                {
                    "date": str(date_val),
                    "total_listings": total_listings,
                    "sold_listings": sold_listings,
                    "active_listings": row.active_listings,
                    "total_volume": row.total_volume or 0,
                    "sell_through_rate": sell_through_rate,
                }
            )

        return stats, total

    async def get_wallet_stats(
        self, days: int = 7, limit: int = 20, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        count_query = select(func.count(func.distinct(func.date(WalletTransaction.created_at)))).where(
            WalletTransaction.created_at >= start_date
        )
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(
                func.date(WalletTransaction.created_at).label("date"),
                func.count(WalletTransaction.transaction_id).label("total_transactions"),
                func.count(func.distinct(WalletTransaction.player_id)).label(
                    "active_players"
                ),
                func.sum(
                    func.case(
                        (WalletTransaction.amount > 0, WalletTransaction.amount),
                        else_=0,
                    )
                ).label("total_income"),
                func.sum(
                    func.case(
                        (WalletTransaction.amount < 0, func.abs(WalletTransaction.amount)),
                        else_=0,
                    )
                ).label("total_expense"),
            )
            .where(WalletTransaction.created_at >= start_date)
            .group_by(func.date(WalletTransaction.created_at))
            .order_by(func.date(WalletTransaction.created_at).desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        rows = result.all()

        stats = []
        for row in rows:
            stats.append(
                {
                    "date": str(row.date),
                    "total_transactions": row.total_transactions,
                    "active_players": row.active_players,
                    "total_income": row.total_income or 0,
                    "total_expense": row.total_expense or 0,
                }
            )

        return stats, total

    async def get_economic_trends(
        self, days: int = 30, granularity: str = "day"
    ) -> list[dict[str, Any]]:
        if granularity not in ("day", "week"):
            granularity = "day"

        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        if granularity == "day":
            date_func = func.date(PlayerTrade.created_at)
        else:
            date_func = func.date_trunc("week", PlayerTrade.created_at)

        trade_query = (
            select(
                date_func.label("period"),
                func.count(PlayerTrade.trade_id).label("trade_count"),
                func.sum(
                    func.case(
                        (PlayerTrade.status == "completed", 1),
                        else_=0,
                    )
                ).label("completed_trades"),
            )
            .where(PlayerTrade.created_at >= start_date)
            .group_by(date_func)
            .order_by(date_func.asc())
        )

        trade_result = await self.db.execute(trade_query)
        trade_rows = {str(row.period): row for row in trade_result.all()}

        if granularity == "day":
            auction_date_func = func.date(AuctionListing.created_at)
        else:
            auction_date_func = func.date_trunc("week", AuctionListing.created_at)

        auction_query = (
            select(
                auction_date_func.label("period"),
                func.count(AuctionListing.listing_id).label("auction_count"),
                func.sum(
                    func.case(
                        (AuctionListing.status == "sold", AuctionListing.current_price),
                        else_=0,
                    )
                ).label("auction_volume"),
            )
            .where(AuctionListing.created_at >= start_date)
            .group_by(auction_date_func)
            .order_by(auction_date_func.asc())
        )

        auction_result = await self.db.execute(auction_query)
        auction_rows = {str(row.period): row for row in auction_result.all()}

        all_periods = sorted(set(list(trade_rows.keys()) + list(auction_rows.keys())))

        trends = []
        for period in all_periods:
            trade_row = trade_rows.get(period)
            auction_row = auction_rows.get(period)
            trends.append(
                {
                    "period": period,
                    "trade_count": trade_row.trade_count if trade_row else 0,
                    "completed_trades": trade_row.completed_trades if trade_row else 0,
                    "auction_count": auction_row.auction_count if auction_row else 0,
                    "auction_volume": auction_row.auction_volume or 0 if auction_row else 0,
                }
            )

        return trends

    async def get_top_traders(
        self, days: int = 7, limit: int = 10, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        subquery = (
            select(
                PlayerTrade.initiator_id.label("player_id"),
                func.count(PlayerTrade.trade_id).label("trade_count"),
            )
            .where(
                PlayerTrade.created_at >= start_date,
                PlayerTrade.status == "completed",
            )
            .group_by(PlayerTrade.initiator_id)
            .subquery()
        )

        count_query = select(func.count()).select_from(subquery)
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0

        query = (
            select(subquery.c.player_id, subquery.c.trade_count)
            .order_by(subquery.c.trade_count.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        rows = result.all()

        top_traders = []
        for row in rows:
            top_traders.append(
                {
                    "player_id": str(row.player_id),
                    "trade_count": row.trade_count,
                }
            )

        return top_traders, total
