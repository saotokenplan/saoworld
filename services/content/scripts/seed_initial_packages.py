import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import async_session_factory as async_session
from app.repositories.content_repo import ContentRepository


async def load_json_file(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def create_ironward_package(db_session) -> None:
    repo = ContentRepository(db_session)

    core_region = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/regions/core_region.json")
    faction_list = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/factions/faction_list.json")
    npc_list = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/npcs/npc_list.json")
    quest_list = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/quests/quest_list.json")
    chapter_list = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/chapters/chapter_list.json")

    ironward_npcs = [
        npc for npc in npc_list["npcs"]
        if npc.get("location") in ["loc_ironward_city", "loc_west_farmlands", "loc_trade_market"]
    ]

    ironward_quests = [
        quest for quest in quest_list["quests"]
        if quest.get("region") == "region_core_ironward"
    ]

    ironward_chapters = [
        chapter for chapter in chapter_list["chapters"]
        if "region_core_ironward" in chapter.get("regions", [])
    ]

    ironward_factions = [
        faction for faction in faction_list["factions"]
        if any(f["faction_id"] == faction["faction_id"] for f in core_region.get("factions", []))
    ]

    payload = {
        "schema_version": 1,
        "region": core_region,
        "factions": ironward_factions,
        "relations": [
            rel for rel in faction_list.get("relations", [])
            if rel["from"] in [f["faction_id"] for f in ironward_factions]
            or rel["to"] in [f["faction_id"] for f in ironward_factions]
        ],
        "npcs": ironward_npcs,
        "quests": ironward_quests,
        "chapters": ironward_chapters,
        "package_type": "region",
        "release_notes": "首期核心区域内容包，包含铁卫城周边区域、铁卫联盟阵营、核心NPC和主线任务",
    }

    pkg = await repo.create_package(
        chapter_id="chapter_01",
        package_version="pkg_ch01_ironward_20260704_01",
        title="铁卫城周边区域包",
        summary="铁卫联盟核心区域内容，包含城市、农田、贸易集市等关键地点，以及主线任务'觉醒之路'",
        payload=payload,
        schema_version=1,
    )

    print(f"Created ironward package: {pkg.content_package_id}")


async def create_grayvalley_package(db_session) -> None:
    repo = ContentRepository(db_session)

    expansion_region = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/regions/expansion_region.json")
    faction_list = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/factions/faction_list.json")
    npc_list = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/npcs/npc_list.json")
    quest_list = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/quests/quest_list.json")
    chapter_list = load_json_file(Path(__file__).parent.parent.parent.parent / "game/data/chapters/chapter_list.json")

    grayvalley_npcs = [
        npc for npc in npc_list["npcs"]
        if npc.get("location") in ["loc_grayvalley_center", "loc_scavenger_camp"]
    ]

    grayvalley_quests = [
        quest for quest in quest_list["quests"]
        if quest.get("region") == "region_expansion_grayvalley"
    ]

    grayvalley_chapters = [
        chapter for chapter in chapter_list["chapters"]
        if "region_expansion_grayvalley" in chapter.get("regions", [])
    ]

    grayvalley_factions = [
        faction for faction in faction_list["factions"]
        if any(f["faction_id"] == faction["faction_id"] for f in expansion_region.get("factions", []))
    ]

    payload = {
        "schema_version": 1,
        "region": expansion_region,
        "factions": grayvalley_factions,
        "relations": [
            rel for rel in faction_list.get("relations", [])
            if rel["from"] in [f["faction_id"] for f in grayvalley_factions]
            or rel["to"] in [f["faction_id"] for f in grayvalley_factions]
        ],
        "npcs": grayvalley_npcs,
        "quests": grayvalley_quests,
        "chapters": grayvalley_chapters,
        "package_type": "region",
        "release_notes": "首期扩展区域内容包，包含灰谷废墟区域、暗影面纱阵营、遗迹探索任务",
    }

    pkg = await repo.create_package(
        chapter_id="chapter_02",
        package_version="pkg_ch02_grayvalley_20260704_01",
        title="灰谷废墟区域包",
        summary="天裂后废弃的旧世界城市遗迹，包含废墟探索、遗物追寻、拾荒者救援等支线任务",
        payload=payload,
        schema_version=1,
    )

    print(f"Created grayvalley package: {pkg.content_package_id}")


async def main():
    async with async_session() as session:
        await create_ironward_package(session)
        await create_grayvalley_package(session)
        await session.commit()
        print("Initial content packages created successfully!")


if __name__ == "__main__":
    asyncio.run(main())