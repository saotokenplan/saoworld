import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from app.core.db import Base, async_sessionmaker, engine
from app.domain.models import OpsEvent


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        from sqlalchemy import select, func

        result = await session.execute(select(func.count()).select_from(OpsEvent))
        count = result.scalar()
        if count > 0:
            print(f"Ops events already exist ({count}), skipping seed.")
            return

        now = datetime.now(timezone.utc)
        events = [
            OpsEvent(
                event_id=uuid.uuid4(),
                event_name="公测双倍经验",
                event_type="double_reward",
                status="active",
                start_at=now,
                end_at=now + timedelta(days=14),
                target_scope="all",
                target_scope_jsonb={},
                reward_config_jsonb={
                    "reward_type": "experience",
                    "multiplier": 2.0,
                    "description": "公测期间所有任务经验双倍",
                },
                multiplier_config_jsonb={
                    "experience_multiplier": 2.0,
                },
                description="公测期间，玩家完成任务获得双倍经验值，帮助快速提升等级",
                rules_jsonb={
                    "valid_quest_types": ["main", "side", "daily"],
                    "exclude_quest_types": [],
                    "minimum_player_level": 1,
                },
                created_by="dev_seed",
                schema_version=1,
            ),
            OpsEvent(
                event_id=uuid.uuid4(),
                event_name="公测双倍贡献度",
                event_type="double_reward",
                status="active",
                start_at=now,
                end_at=now + timedelta(days=14),
                target_scope="all",
                target_scope_jsonb={},
                reward_config_jsonb={
                    "reward_type": "contribution",
                    "multiplier": 2.0,
                    "description": "公测期间所有贡献度双倍",
                },
                multiplier_config_jsonb={
                    "contribution_multiplier": 2.0,
                },
                description="公测期间，玩家完成任务获得双倍贡献度，提升投票权重",
                rules_jsonb={
                    "valid_actions": ["quest_complete", "vote_submit", "npc_interact"],
                    "minimum_contribution_threshold": 0,
                },
                created_by="dev_seed",
                schema_version=1,
            ),
            OpsEvent(
                event_id=uuid.uuid4(),
                event_name="公测登录礼包",
                event_type="login_bonus",
                status="active",
                start_at=now,
                end_at=now + timedelta(days=7),
                target_scope="all",
                target_scope_jsonb={},
                reward_config_jsonb={
                    "reward_type": "login_bonus",
                    "daily_rewards": [
                        {"day": 1, "items": [{"item_key": "gold", "quantity": 100}]},
                        {"day": 2, "items": [{"item_key": "gold", "quantity": 200}]},
                        {"day": 3, "items": [{"item_key": "experience_potion", "quantity": 1}]},
                        {"day": 4, "items": [{"item_key": "gold", "quantity": 300}]},
                        {"day": 5, "items": [{"item_key": "contribution_token", "quantity": 50}]},
                        {"day": 6, "items": [{"item_key": "gold", "quantity": 500}]},
                        {"day": 7, "items": [{"item_key": "rare_equipment_box", "quantity": 1}]},
                    ],
                },
                multiplier_config_jsonb=None,
                description="公测期间连续登录7天，每天获得丰厚奖励",
                rules_jsonb={
                    "requirement": "daily_login",
                    "consecutive_days": True,
                    "reset_on_miss": False,
                },
                created_by="dev_seed",
                schema_version=1,
            ),
        ]

        for event in events:
            session.add(event)

        await session.commit()

        print("Seeded public beta events:")
        for event in events:
            print(f"  - {event.event_name} ({event.event_id})")
            print(f"    Type: {event.event_type}")
            print(f"    Status: {event.status}")
            print(f"    Duration: {event.start_at} to {event.end_at}")


if __name__ == "__main__":
    asyncio.run(seed())