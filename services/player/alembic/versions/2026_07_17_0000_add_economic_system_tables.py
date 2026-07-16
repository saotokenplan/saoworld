"""add economic system tables: player_wallets, wallet_transactions, player_trades, trade_items, trade_coins, auction_listings, auction_bids

Revision ID: 2026_07_17_0000
Revises: 2026_07_16_1800
Create Date: 2026-07-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_07_17_0000"
down_revision: Union[str, None] = "2026_07_16_1800"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "player_wallets",
        sa.Column("wallet_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("gold_coins", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("gold_coins >= 0", name="player_wallets_gold_check"),
        sa.PrimaryKeyConstraint("wallet_id"),
    )
    op.create_index("player_wallets_player_id_idx", "player_wallets", ["player_id"], unique=True)

    op.create_table(
        "wallet_transactions",
        sa.Column("transaction_id", sa.UUID(), nullable=False),
        sa.Column("wallet_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("transaction_type", sa.String(32), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("balance_before", sa.Integer(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("reference_id", sa.UUID(), nullable=True),
        sa.Column("reference_type", sa.String(32), nullable=True),
        sa.Column("description", sa.String(256), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("amount != 0", name="wallet_transactions_amount_check"),
        sa.CheckConstraint("balance_before >= 0", name="wallet_transactions_before_check"),
        sa.CheckConstraint("balance_after >= 0", name="wallet_transactions_after_check"),
        sa.PrimaryKeyConstraint("transaction_id"),
    )
    op.create_index("wallet_transactions_wallet_id_idx", "wallet_transactions", ["wallet_id"])
    op.create_index("wallet_transactions_player_id_idx", "wallet_transactions", ["player_id"])
    op.create_index("wallet_transactions_type_idx", "wallet_transactions", ["transaction_type"])
    op.create_index("wallet_transactions_reference_idx", "wallet_transactions", ["reference_type", "reference_id"])

    op.create_table(
        "player_trades",
        sa.Column("trade_id", sa.UUID(), nullable=False),
        sa.Column("initiator_id", sa.UUID(), nullable=False),
        sa.Column("recipient_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("trade_fee", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'cancelled', 'completed', 'expired')", name="player_trades_status_check"),
        sa.CheckConstraint("trade_fee >= 0", name="player_trades_fee_check"),
        sa.PrimaryKeyConstraint("trade_id"),
    )
    op.create_index("player_trades_initiator_id_idx", "player_trades", ["initiator_id"])
    op.create_index("player_trades_recipient_id_idx", "player_trades", ["recipient_id"])
    op.create_index("player_trades_status_idx", "player_trades", ["status"])
    op.create_index("player_trades_expires_idx", "player_trades", ["expires_at"])

    op.create_table(
        "trade_items",
        sa.Column("trade_item_id", sa.UUID(), nullable=False),
        sa.Column("trade_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("item_key", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("is_offer", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("quantity > 0", name="trade_items_quantity_check"),
        sa.PrimaryKeyConstraint("trade_item_id"),
    )
    op.create_index("trade_items_trade_id_idx", "trade_items", ["trade_id"])
    op.create_index("trade_items_player_id_idx", "trade_items", ["player_id"])

    op.create_table(
        "trade_coins",
        sa.Column("trade_coin_id", sa.UUID(), nullable=False),
        sa.Column("trade_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("is_offer", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("amount > 0", name="trade_coins_amount_check"),
        sa.PrimaryKeyConstraint("trade_coin_id"),
    )
    op.create_index("trade_coins_trade_id_idx", "trade_coins", ["trade_id"])
    op.create_index("trade_coins_player_id_idx", "trade_coins", ["player_id"])

    op.create_table(
        "auction_listings",
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("seller_id", sa.UUID(), nullable=False),
        sa.Column("item_key", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("starting_price", sa.Integer(), nullable=False),
        sa.Column("current_price", sa.Integer(), nullable=False),
        sa.Column("buyout_price", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("bid_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_bidder_id", sa.UUID(), nullable=True),
        sa.Column("last_bid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("auction_tax", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("quantity > 0", name="auction_listings_quantity_check"),
        sa.CheckConstraint("starting_price > 0", name="auction_listings_start_price_check"),
        sa.CheckConstraint("current_price >= starting_price", name="auction_listings_current_price_check"),
        sa.CheckConstraint("status IN ('active', 'completed', 'cancelled', 'expired')", name="auction_listings_status_check"),
        sa.CheckConstraint("auction_tax >= 0", name="auction_listings_tax_check"),
        sa.PrimaryKeyConstraint("listing_id"),
    )
    op.create_index("auction_listings_seller_id_idx", "auction_listings", ["seller_id"])
    op.create_index("auction_listings_item_key_idx", "auction_listings", ["item_key"])
    op.create_index("auction_listings_status_idx", "auction_listings", ["status"])
    op.create_index("auction_listings_expires_idx", "auction_listings", ["expires_at"])

    op.create_table(
        "auction_bids",
        sa.Column("bid_id", sa.UUID(), nullable=False),
        sa.Column("listing_id", sa.UUID(), nullable=False),
        sa.Column("bidder_id", sa.UUID(), nullable=False),
        sa.Column("bid_amount", sa.Integer(), nullable=False),
        sa.Column("is_winning", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_buyout", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("bid_amount > 0", name="auction_bids_amount_check"),
        sa.PrimaryKeyConstraint("bid_id"),
    )
    op.create_index("auction_bids_listing_id_idx", "auction_bids", ["listing_id"])
    op.create_index("auction_bids_bidder_id_idx", "auction_bids", ["bidder_id"])
    op.create_index("auction_bids_winning_idx", "auction_bids", ["listing_id", "is_winning"])


def downgrade() -> None:
    op.drop_index("auction_bids_winning_idx", table_name="auction_bids")
    op.drop_index("auction_bids_bidder_id_idx", table_name="auction_bids")
    op.drop_index("auction_bids_listing_id_idx", table_name="auction_bids")
    op.drop_table("auction_bids")

    op.drop_index("auction_listings_expires_idx", table_name="auction_listings")
    op.drop_index("auction_listings_status_idx", table_name="auction_listings")
    op.drop_index("auction_listings_item_key_idx", table_name="auction_listings")
    op.drop_index("auction_listings_seller_id_idx", table_name="auction_listings")
    op.drop_table("auction_listings")

    op.drop_index("trade_coins_player_id_idx", table_name="trade_coins")
    op.drop_index("trade_coins_trade_id_idx", table_name="trade_coins")
    op.drop_table("trade_coins")

    op.drop_index("trade_items_player_id_idx", table_name="trade_items")
    op.drop_index("trade_items_trade_id_idx", table_name="trade_items")
    op.drop_table("trade_items")

    op.drop_index("player_trades_expires_idx", table_name="player_trades")
    op.drop_index("player_trades_status_idx", table_name="player_trades")
    op.drop_index("player_trades_recipient_id_idx", table_name="player_trades")
    op.drop_index("player_trades_initiator_id_idx", table_name="player_trades")
    op.drop_table("player_trades")

    op.drop_index("wallet_transactions_reference_idx", table_name="wallet_transactions")
    op.drop_index("wallet_transactions_type_idx", table_name="wallet_transactions")
    op.drop_index("wallet_transactions_player_id_idx", table_name="wallet_transactions")
    op.drop_index("wallet_transactions_wallet_id_idx", table_name="wallet_transactions")
    op.drop_table("wallet_transactions")

    op.drop_index("player_wallets_player_id_idx", table_name="player_wallets")
    op.drop_table("player_wallets")
