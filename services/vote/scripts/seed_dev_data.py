import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from app.core.db import Base, async_sessionmaker, engine
from app.domain.models import VoteCandidate, VoteCycle


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with SessionLocal() as session:
        from sqlalchemy import select, func

        result = await session.execute(select(func.count()).select_from(VoteCycle))
        count = result.scalar()
        if count > 0:
            print(f"Vote cycles already exist ({count}), skipping seed.")
            return

        now = datetime.now(timezone.utc)
        cycle_id = uuid.uuid4()
        candidates = [
            VoteCandidate(
                candidate_id=uuid.uuid4(),
                vote_cycle_id=cycle_id,
                title="探索幽光森林深处",
                summary="玩家深入幽光森林深处，探索古树遗迹，揭开森林守护者的秘密",
                description="探索向主线，新增森林深处区域、2个关键地点、3个NPC（古树精灵、森林守护者、迷路学者）、2个支线任务（古树的试炼、精灵的请求）",
                region_scope=["region_west_forest"],
                risk_tags=["content_risk"],
                generated_params={
                    "template_type": "quest",
                    "template_id": "quest_main",
                    "count": 3,
                    "region_id": "region_west_forest",
                    "chapter_id": "chapter_02",
                    "theme": "exploration",
                    "difficulty": "medium",
                },
                status="active",
            ),
            VoteCandidate(
                candidate_id=uuid.uuid4(),
                vote_cycle_id=cycle_id,
                title="征服南部绿洲沙漠",
                summary="前往南部绿洲，解开沙漠神庙的秘密，击败沙漠帝王",
                description="战斗向主线，新增沙漠神庙区域、3个关键地点、3个NPC（神庙祭司、沙漠侦察员、商会会长）、2个支线任务（商队救援、稀有商品）",
                region_scope=["region_south_oasis"],
                risk_tags=["combat_risk"],
                generated_params={
                    "template_type": "quest",
                    "template_id": "quest_main",
                    "count": 3,
                    "region_id": "region_south_oasis",
                    "chapter_id": "chapter_02",
                    "theme": "combat",
                    "difficulty": "hard",
                },
                status="active",
            ),
            VoteCandidate(
                candidate_id=uuid.uuid4(),
                vote_cycle_id=cycle_id,
                title="扩展铁卫城周边",
                summary="扩建铁卫城周边区域，增加新的聚落和NPC互动",
                description="建设向主线，新增铁卫城郊区区域、2个关键地点、2个NPC（铁匠、商人）、3个支线任务（装备打造、物资采购、区域声望）",
                region_scope=["core_region"],
                risk_tags=["economy_risk"],
                generated_params={
                    "template_type": "settlement",
                    "template_id": "settlement_base",
                    "count": 1,
                    "region_id": "core_region",
                    "chapter_id": "chapter_01",
                    "theme": "building",
                    "settlement_type": "town",
                },
                status="active",
            ),
        ]
        cycle = VoteCycle(
            vote_cycle_id=cycle_id,
            chapter_id="chapter_02",
            status="open",
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(days=7),
            created_by="dev_seed",
            created_reason="Public beta seed data - chapter 2 vote cycle",
            candidates=candidates,
        )
        session.add(cycle)
        await session.commit()

        print(f"Seeded vote cycle: {cycle_id}")
        print(f"  Chapter: {cycle.chapter_id}")
        print(f"  Status: {cycle.status}")
        print(f"  Duration: {cycle.starts_at} to {cycle.ends_at}")
        print("  Candidates:")
        for c in candidates:
            print(f"    - {c.title} ({c.candidate_id})")
            print(f"      Region Scope: {c.region_scope}")
            print(f"      Generated Params: {c.generated_params}")


if __name__ == "__main__":
    asyncio.run(seed())
