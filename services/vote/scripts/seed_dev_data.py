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
                title="探索迷雾森林",
                summary="玩家深入北部迷雾森林，揭开古老遗迹的秘密",
                description="一条探索向的主线，新增森林区域和3个NPC",
                region_scope=["forest_north"],
                risk_tags=["content_risk"],
                status="active",
            ),
            VoteCandidate(
                candidate_id=uuid.uuid4(),
                vote_cycle_id=cycle_id,
                title="重建边境哨所",
                summary="协助村民重建被摧毁的边境哨所，开启贸易路线",
                description="一条建设向的主线，新增建造系统和商人NPC",
                region_scope=["border_outpost"],
                risk_tags=["economy_risk"],
                status="active",
            ),
            VoteCandidate(
                candidate_id=uuid.uuid4(),
                vote_cycle_id=cycle_id,
                title="追踪暗影盗贼",
                summary="追查在城镇中行窃的神秘盗贼组织",
                description=None,
                region_scope=["town_square"],
                risk_tags=[],
                status="active",
            ),
        ]
        cycle = VoteCycle(
            vote_cycle_id=cycle_id,
            chapter_id="ch_prologue_01",
            status="open",
            starts_at=now - timedelta(hours=1),
            ends_at=now + timedelta(hours=23),
            created_by="dev_seed",
            created_reason="MVP development seed data",
            candidates=candidates,
        )
        session.add(cycle)
        await session.commit()

        print(f"Seeded vote cycle: {cycle_id}")
        print(f"  Chapter: {cycle.chapter_id}")
        print(f"  Status: {cycle.status}")
        print(f"  Candidates:")
        for c in candidates:
            print(f"    - {c.title} ({c.candidate_id})")


if __name__ == "__main__":
    asyncio.run(seed())
