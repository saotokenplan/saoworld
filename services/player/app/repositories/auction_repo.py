from datetime import datetime, timedelta, timezone
from typing import Any, cast

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import metrics
from app.domain.models import AuctionListing
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.wallet_repo import WalletRepository

AUCTION_TAX_RATE = 0.10


class AuctionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_listing(
        self,
        seller_id: Any,
        item_key: str,
        item_type: str,
        quantity: int,
        starting_price: int,
        buyout_price: int | None,
        duration_hours: int,
    ) -> AuctionListing | None:
        inventory_repo = InventoryRepository(self.db)
        item = await inventory_repo.get_item(seller_id, item_key)
        if item is None or item.quantity < quantity:
            return None

        await inventory_repo.remove_item(seller_id, item_key, quantity)

        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)

        listing = AuctionListing(
            seller_id=seller_id,
            item_key=item_key,
            item_type=item_type,
            quantity=quantity,
            starting_price=starting_price,
            current_price=starting_price,
            buyout_price=buyout_price,
            status="active",
            expires_at=expires_at,
        )
        self.db.add(listing)
        await self.db.commit()
        await self.db.refresh(listing)

        metrics.record_auction_listing_created(str(seller_id))

        return listing

    async def get_listing_by_id(self, listing_id: Any) -> AuctionListing | None:
        result = await self.db.execute(
            select(AuctionListing).where(AuctionListing.listing_id == listing_id)
        )
        return result.scalar_one_or_none()

    async def get_active_listings(
        self,
        item_key: str | None = None,
        item_type: str | None = None,
        min_price: int | None = None,
        max_price: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AuctionListing], int]:
        query = select(AuctionListing).where(AuctionListing.status == "active")

        if item_key is not None:
            query = query.where(AuctionListing.item_key == item_key)

        if item_type is not None:
            query = query.where(AuctionListing.item_type == item_type)

        if min_price is not None:
            query = query.where(AuctionListing.current_price >= min_price)

        if max_price is not None:
            query = query.where(AuctionListing.current_price <= max_price)

        count_query = select(func.count()).select_from(AuctionListing).where(
            AuctionListing.status == "active"
        )
        if item_key is not None:
            count_query = count_query.where(AuctionListing.item_key == item_key)
        if item_type is not None:
            count_query = count_query.where(AuctionListing.item_type == item_type)
        if min_price is not None:
            count_query = count_query.where(AuctionListing.current_price >= min_price)
        if max_price is not None:
            count_query = count_query.where(AuctionListing.current_price <= max_price)

        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        query = query.order_by(AuctionListing.current_price.asc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        listings = cast(list[AuctionListing], list(result.scalars().all()))
        return listings, total

    async def get_seller_listings(
        self, seller_id: Any, status: str | None = None, limit: int = 20, offset: int = 0
    ) -> tuple[list[AuctionListing], int]:
        query = select(AuctionListing).where(AuctionListing.seller_id == seller_id)

        if status is not None:
            query = query.where(AuctionListing.status == status)

        count_query = select(func.count()).select_from(AuctionListing).where(
            AuctionListing.seller_id == seller_id
        )
        if status is not None:
            count_query = count_query.where(AuctionListing.status == status)

        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        query = query.order_by(AuctionListing.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        listings = cast(list[AuctionListing], list(result.scalars().all()))
        return listings, total

    async def get_bidder_listings(
        self, bidder_id: Any, limit: int = 20, offset: int = 0
    ) -> tuple[list[AuctionListing], int]:
        query = select(AuctionListing).where(
            AuctionListing.highest_bidder_id == bidder_id,
            AuctionListing.status == "active",
        )

        count_query = select(func.count()).select_from(AuctionListing).where(
            AuctionListing.highest_bidder_id == bidder_id,
            AuctionListing.status == "active",
        )

        result = await self.db.execute(count_query)
        total = result.scalar() or 0

        query = query.order_by(AuctionListing.created_at.desc()).limit(limit).offset(offset)
        result = await self.db.execute(query)
        listings = cast(list[AuctionListing], list(result.scalars().all()))
        return listings, total

    async def place_bid(self, listing_id: Any, bidder_id: Any, bid_amount: int) -> AuctionListing | None:
        listing = await self.get_listing_by_id(listing_id)
        if listing is None or listing.status != "active":
            return None

        if listing.seller_id == bidder_id:
            return None

        if listing.highest_bidder_id == bidder_id:
            return None

        if bid_amount <= listing.current_price:
            return None

        wallet_repo = WalletRepository(self.db)
        wallet = await wallet_repo.get_wallet(bidder_id)
        if wallet is None or wallet.gold_coins < bid_amount:
            return None

        listing.current_price = bid_amount
        listing.highest_bidder_id = bidder_id

        await self.db.commit()
        await self.db.refresh(listing)

        metrics.record_auction_bid_placed(str(bidder_id))

        return listing

    async def buyout(self, listing_id: Any, buyer_id: Any) -> AuctionListing | None:
        listing = await self.get_listing_by_id(listing_id)
        if listing is None or listing.status != "active":
            return None

        if listing.seller_id == buyer_id:
            return None

        if listing.buyout_price is None:
            return None

        wallet_repo = WalletRepository(self.db)
        buyer_wallet = await wallet_repo.get_wallet(buyer_id)
        if buyer_wallet is None or buyer_wallet.gold_coins < listing.buyout_price:
            return None

        await wallet_repo.spend_coins(
            buyer_id, listing.buyout_price, "auction_buy",
            description=f"拍卖行购买 {listing.item_key}",
            reference_id=str(listing.listing_id),
        )

        tax_amount = int(listing.buyout_price * AUCTION_TAX_RATE)
        seller_amount = listing.buyout_price - tax_amount

        await wallet_repo.add_coins(
            listing.seller_id, seller_amount, "auction_sell",
            description=f"拍卖行出售 {listing.item_key}",
            reference_id=str(listing.listing_id),
        )

        if tax_amount > 0:
            pass

        inventory_repo = InventoryRepository(self.db)
        await inventory_repo.add_item(
            buyer_id, listing.item_key, listing.item_type, listing.quantity
        )

        listing.status = "sold"
        listing.sold_at = datetime.now(timezone.utc)
        listing.buyer_id = buyer_id

        await self.db.commit()
        await self.db.refresh(listing)

        metrics.record_auction_listing_sold(str(listing.seller_id), listing.buyout_price or 0)

        return listing

    async def cancel_listing(self, listing_id: Any, seller_id: Any) -> AuctionListing | None:
        listing = await self.get_listing_by_id(listing_id)
        if listing is None or listing.status != "active":
            return None

        if listing.seller_id != seller_id:
            return None

        inventory_repo = InventoryRepository(self.db)
        await inventory_repo.add_item(
            seller_id, listing.item_key, listing.item_type, listing.quantity
        )

        listing.status = "cancelled"

        await self.db.commit()
        await self.db.refresh(listing)
        return listing

    async def expire_listings(self) -> int:
        now = datetime.now(timezone.utc)
        result = await self.db.execute(
            select(AuctionListing).where(
                AuctionListing.status == "active",
                AuctionListing.expires_at < now,
            )
        )
        expired_listings = result.scalars().all()

        inventory_repo = InventoryRepository(self.db)
        for listing in expired_listings:
            listing.status = "expired"
            await inventory_repo.add_item(
                listing.seller_id, listing.item_key, listing.item_type, listing.quantity
            )

        await self.db.commit()
        return len(expired_listings)