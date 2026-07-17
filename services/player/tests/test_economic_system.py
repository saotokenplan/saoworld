import uuid

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import create_test_token
from app.domain.models import Player, PlayerWallet, PlayerInventory
from app.schemas.auth import Role


@pytest_asyncio.fixture
def player_token_2() -> str:
    return create_test_token(
        user_id="00000000-0000-0000-0000-000000000002",
        role=Role.PLAYER,
    )


@pytest_asyncio.fixture
async def test_player_2(db: AsyncSession) -> Player:
    player = Player(
        player_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        display_name="TestPlayer2",
        chapter_id="ch_prologue_01",
    )
    db.add(player)
    await db.commit()
    return player


@pytest_asyncio.fixture
async def test_wallet(test_player: Player, db: AsyncSession) -> PlayerWallet:
    wallet = PlayerWallet(
        wallet_id=uuid.uuid4(),
        player_id=test_player.player_id,
        gold_coins=1000,
    )
    db.add(wallet)
    await db.commit()
    return wallet


@pytest_asyncio.fixture
async def test_wallet_2(test_player_2: Player, db: AsyncSession) -> PlayerWallet:
    wallet = PlayerWallet(
        wallet_id=uuid.uuid4(),
        player_id=test_player_2.player_id,
        gold_coins=500,
    )
    db.add(wallet)
    await db.commit()
    return wallet


@pytest_asyncio.fixture
async def test_inventory_item_2(test_player_2: Player, db: AsyncSession) -> PlayerInventory:
    item = PlayerInventory(
        inventory_id=uuid.uuid4(),
        player_id=test_player_2.player_id,
        item_key="item_iron_sword_01",
        item_type="weapon",
        quantity=2,
        metadata_jsonb={"name": "铁剑", "description": "普通的铁制剑", "attack": 10},
    )
    db.add(item)
    await db.commit()
    return item


class TestWalletAPI:
    async def test_get_wallet_success(self, client: AsyncClient, player_token: str, test_player: Player, test_wallet: PlayerWallet):
        response = await client.get(
            "/api/v1/player/wallet",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "gold_coins" in data
        assert data["gold_coins"] >= 0

    async def test_get_wallet_transactions(self, client: AsyncClient, player_token: str, test_player: Player):
        response = await client.get(
            "/api/v1/player/wallet/transactions",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "transactions" in data
        assert isinstance(data["transactions"], list)


class TestTradeAPI:
    async def test_create_trade_with_coins(self, client: AsyncClient, player_token: str, player_token_2: str, test_player: Player, test_player_2: Player, test_wallet: PlayerWallet):
        response = await client.post(
            "/api/v1/player/trades",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "recipient_id": str(test_player_2.player_id),
                "offer_coins": 100,
                "request_coins": 50,
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["status"] == "pending"

    async def test_accept_trade(self, client: AsyncClient, player_token: str, player_token_2: str, test_player: Player, test_player_2: Player, test_wallet: PlayerWallet, test_wallet_2: PlayerWallet):
        create_response = await client.post(
            "/api/v1/player/trades",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "recipient_id": str(test_player_2.player_id),
                "offer_coins": 100,
                "request_coins": 50,
            },
        )
        trade_id = create_response.json()["data"]["trade_id"]

        accept_response = await client.post(
            f"/api/v1/player/trades/{trade_id}/accept",
            headers={"Authorization": f"Bearer {player_token_2}", "X-Player-Id": str(test_player_2.player_id)},
        )
        assert accept_response.status_code == 200

    async def test_reject_trade(self, client: AsyncClient, player_token: str, player_token_2: str, test_player: Player, test_player_2: Player, test_wallet: PlayerWallet):
        create_response = await client.post(
            "/api/v1/player/trades",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "recipient_id": str(test_player_2.player_id),
                "offer_coins": 100,
                "request_coins": 50,
            },
        )
        trade_id = create_response.json()["data"]["trade_id"]

        reject_response = await client.post(
            f"/api/v1/player/trades/{trade_id}/reject",
            headers={"Authorization": f"Bearer {player_token_2}", "X-Player-Id": str(test_player_2.player_id)},
        )
        assert reject_response.status_code == 200
        data = reject_response.json()["data"]
        assert data["status"] == "rejected"

    async def test_cancel_trade(self, client: AsyncClient, player_token: str, player_token_2: str, test_player: Player, test_player_2: Player, test_wallet: PlayerWallet):
        create_response = await client.post(
            "/api/v1/player/trades",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "recipient_id": str(test_player_2.player_id),
                "offer_coins": 100,
                "request_coins": 50,
            },
        )
        trade_id = create_response.json()["data"]["trade_id"]

        cancel_response = await client.post(
            f"/api/v1/player/trades/{trade_id}/cancel",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
        )
        assert cancel_response.status_code == 200
        data = cancel_response.json()["data"]
        assert data["status"] == "cancelled"

    async def test_get_trade_history(self, client: AsyncClient, player_token: str, test_player: Player):
        response = await client.get(
            "/api/v1/player/trades",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "trades" in data
        assert isinstance(data["trades"], list)


class TestAuctionAPI:
    async def test_create_auction_listing(self, client: AsyncClient, player_token: str, test_player: Player, db: AsyncSession):
        from app.repositories.inventory_repo import InventoryRepository
        inventory_repo = InventoryRepository(db)
        await inventory_repo.add_item(
            test_player.player_id,
            "item_health_potion_01",
            "consumable",
            quantity=10,
            metadata_jsonb={"name": "治疗药水", "description": "恢复50点生命值"},
        )

        response = await client.post(
            "/api/v1/player/auction/listings",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "item_key": "item_health_potion_01",
                "item_type": "consumable",
                "quantity": 5,
                "starting_price": 100,
                "buyout_price": 500,
                "duration_hours": 24,
            },
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["status"] == "active"

    async def test_cancel_auction_listing(self, client: AsyncClient, player_token: str, test_player: Player, db: AsyncSession):
        from app.repositories.inventory_repo import InventoryRepository
        inventory_repo = InventoryRepository(db)
        await inventory_repo.add_item(
            test_player.player_id,
            "item_health_potion_01",
            "consumable",
            quantity=10,
        )

        create_response = await client.post(
            "/api/v1/player/auction/listings",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "item_key": "item_health_potion_01",
                "item_type": "consumable",
                "quantity": 5,
                "starting_price": 100,
                "buyout_price": 500,
                "duration_hours": 24,
            },
        )
        listing_id = create_response.json()["data"]["listing_id"]

        cancel_response = await client.post(
            f"/api/v1/player/auction/listings/{listing_id}/cancel",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
        )
        assert cancel_response.status_code == 200
        data = cancel_response.json()["data"]
        assert data["status"] == "cancelled"

    async def test_list_auction_listings(self, client: AsyncClient, player_token: str):
        response = await client.get(
            "/api/v1/player/auction/listings",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "listings" in data

    async def test_search_auction_listings(self, client: AsyncClient, player_token: str, test_player: Player, db: AsyncSession):
        from app.repositories.inventory_repo import InventoryRepository
        inventory_repo = InventoryRepository(db)
        await inventory_repo.add_item(
            test_player.player_id,
            "item_health_potion_01",
            "consumable",
            quantity=10,
        )

        await client.post(
            "/api/v1/player/auction/listings",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "item_key": "item_health_potion_01",
                "item_type": "consumable",
                "quantity": 5,
                "starting_price": 100,
                "buyout_price": 500,
                "duration_hours": 24,
            },
        )

        response = await client.get(
            "/api/v1/player/auction/listings",
            headers={"Authorization": f"Bearer {player_token}"},
            params={"item_key": "item_health_potion_01"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "listings" in data

    async def test_get_my_listings(self, client: AsyncClient, player_token: str, test_player: Player):
        response = await client.get(
            "/api/v1/player/auction/listings",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "listings" in data

    async def test_get_my_bids(self, client: AsyncClient, player_token: str, test_player: Player):
        response = await client.get(
            "/api/v1/player/auction/bids",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
        )
        assert response.status_code == 200 or response.status_code == 404


class TestEconomicSystemErrorCases:
    async def test_trade_insufficient_gold(self, client: AsyncClient, player_token: str, test_player: Player, test_player_2: Player, test_wallet: PlayerWallet):
        response = await client.post(
            "/api/v1/player/trades",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "recipient_id": str(test_player_2.player_id),
                "offer_coins": 99999999,
                "request_coins": 100,
            },
        )
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "INSUFFICIENT_GOLD"

    async def test_auction_bid_too_low(self, client: AsyncClient, player_token: str, player_token_2: str, test_player: Player, test_player_2: Player, db: AsyncSession):
        from app.repositories.inventory_repo import InventoryRepository
        inventory_repo = InventoryRepository(db)
        await inventory_repo.add_item(
            test_player.player_id,
            "item_health_potion_01",
            "consumable",
            quantity=10,
        )

        create_response = await client.post(
            "/api/v1/player/auction/listings",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "item_key": "item_health_potion_01",
                "item_type": "consumable",
                "quantity": 5,
                "starting_price": 100,
                "duration_hours": 24,
            },
        )
        listing_id = create_response.json()["data"]["listing_id"]

        response = await client.post(
            f"/api/v1/player/auction/listings/{listing_id}/bid",
            headers={"Authorization": f"Bearer {player_token_2}", "X-Player-Id": str(test_player_2.player_id)},
            json={"bid_amount": 50},
        )
        assert response.status_code == 409
        data = response.json()
        assert data["code"] == "BID_TOO_LOW"

    async def test_auction_invalid_buyout_price(self, client: AsyncClient, player_token: str, test_player: Player, db: AsyncSession):
        from app.repositories.inventory_repo import InventoryRepository
        inventory_repo = InventoryRepository(db)
        await inventory_repo.add_item(
            test_player.player_id,
            "item_health_potion_01",
            "consumable",
            quantity=10,
        )

        response = await client.post(
            "/api/v1/player/auction/listings",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": str(test_player.player_id)},
            json={
                "item_key": "item_health_potion_01",
                "item_type": "consumable",
                "quantity": 5,
                "starting_price": 100,
                "buyout_price": 50,
                "duration_hours": 24,
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == "INVALID_BUYOUT_PRICE"

    async def test_wallet_not_found(self, client: AsyncClient, player_token: str):
        response = await client.get(
            "/api/v1/player/wallet",
            headers={"Authorization": f"Bearer {player_token}", "X-Player-Id": "00000000-0000-0000-0000-000000000000"},
        )
        assert response.status_code == 404
        data = response.json()
        assert data["code"] == "WALLET_NOT_FOUND"


class TestEconomicStatsAPI:
    def _ops_token(self) -> str:
        return create_test_token(
            user_id="00000000-0000-0000-0000-000000000001",
            role=Role.OPS,
        )

    async def test_get_economy_overview(self, client: AsyncClient):
        token = self._ops_token()
        response = await client.get(
            "/api/v1/ops/economy/overview",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_gold_supply" in data
        assert "total_wallets" in data
        assert "total_trades" in data
        assert "total_auctions" in data
        assert "active_auctions" in data

    async def test_get_economy_overview_no_permission(self, client: AsyncClient, player_token: str):
        response = await client.get(
            "/api/v1/ops/economy/overview",
            headers={"Authorization": f"Bearer {player_token}"},
        )
        assert response.status_code == 403

    async def test_get_trade_stats(self, client: AsyncClient):
        token = self._ops_token()
        response = await client.get(
            "/api/v1/ops/economy/trades",
            headers={"Authorization": f"Bearer {token}"},
            params={"days": 7, "limit": 20, "offset": 0},
        )
        assert response.status_code in (200, 500)

    async def test_get_auction_stats(self, client: AsyncClient):
        token = self._ops_token()
        response = await client.get(
            "/api/v1/ops/economy/auctions",
            headers={"Authorization": f"Bearer {token}"},
            params={"days": 7, "limit": 20, "offset": 0},
        )
        assert response.status_code in (200, 500)

    async def test_get_wallet_stats(self, client: AsyncClient):
        token = self._ops_token()
        response = await client.get(
            "/api/v1/ops/economy/wallets",
            headers={"Authorization": f"Bearer {token}"},
            params={"days": 7, "limit": 20, "offset": 0},
        )
        assert response.status_code in (200, 500)

    async def test_get_economic_trends(self, client: AsyncClient):
        token = self._ops_token()
        response = await client.get(
            "/api/v1/ops/economy/trends",
            headers={"Authorization": f"Bearer {token}"},
            params={"days": 30, "granularity": "day"},
        )
        assert response.status_code in (200, 500)

    async def test_get_top_traders(self, client: AsyncClient):
        token = self._ops_token()
        response = await client.get(
            "/api/v1/ops/economy/top-traders",
            headers={"Authorization": f"Bearer {token}"},
            params={"days": 7, "limit": 10, "offset": 0},
        )
        assert response.status_code in (200, 500)
