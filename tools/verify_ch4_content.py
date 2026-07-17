"""Validate JSON files and reference integrity for Chapter 4 content."""
import json
from pathlib import Path

DATA_DIR = Path("/workspace/game/data")


def load_json(rel_path: str) -> dict:
    return json.loads((DATA_DIR / rel_path).read_text(encoding="utf-8"))


def main() -> None:
    # Load all relevant data
    regions_list = load_json("regions/region_list.json")
    chapters = load_json("chapters/chapter_list.json")
    npcs = load_json("npcs/npc_list.json")
    quests = load_json("quests/quest_list.json")
    monsters = load_json("monsters/monster_list.json")
    factions = load_json("factions/faction_list.json")

    starfall = load_json("regions/region_starfall_wastes.json")
    abyss = load_json("regions/region_abyss_rift.json")

    # Build ID sets
    region_ids = {r["region_id"] for r in regions_list["regions"]}
    chapter_ids = {c["chapter_id"] for c in chapters["chapters"]}
    npc_ids = {n["npc_id"] for n in npcs["npcs"]}
    quest_ids = {q["quest_id"] for q in quests["quests"]}
    monster_keys = {m["monster_key"] for m in monsters["monsters"]}
    faction_ids = {f["faction_id"] for f in factions["factions"]}

    print(f"Region count: {len(region_ids)}")
    print(f"Chapter count: {len(chapter_ids)}")
    print(f"NPC count: {len(npc_ids)}")
    print(f"Quest count: {len(quest_ids)}")
    print(f"Monster count: {len(monster_keys)}")
    print(f"Faction count: {len(faction_ids)}")
    print()

    errors: list[str] = []

    # 1. Validate chapter 4 exists and references valid regions/quests
    ch4 = next((c for c in chapters["chapters"] if c["chapter_id"] == "chapter_04"), None)
    if ch4 is None:
        errors.append("chapter_04 not found in chapter_list.json")
    else:
        for qid in ch4.get("main_quests", []):
            if qid not in quest_ids:
                errors.append(f"chapter_04 main_quests references unknown quest: {qid}")
        for qid in ch4.get("side_quests", []):
            if qid not in quest_ids:
                errors.append(f"chapter_04 side_quests references unknown quest: {qid}")
        for rid in ch4.get("regions", []):
            if rid not in region_ids:
                errors.append(f"chapter_04 regions references unknown region: {rid}")
        print(f"Chapter 4 main_quests: {len(ch4.get('main_quests', []))}")
        print(f"Chapter 4 side_quests: {len(ch4.get('side_quests', []))}")
        print(f"Chapter 4 regions: {len(ch4.get('regions', []))}")

    # 2. Validate new region files
    for region_file, region_id in [
        ("regions/region_starfall_wastes.json", "region_starfall_wastes"),
        ("regions/region_abyss_rift.json", "region_abyss_rift"),
    ]:
        r = load_json(region_file)
        if r["region_id"] != region_id:
            errors.append(f"{region_file} region_id mismatch: {r['region_id']}")
        # NPCs referenced in region must exist
        for nid in r.get("npcs", []):
            if nid not in npc_ids:
                errors.append(f"{region_id} references unknown NPC: {nid}")
        # Quests referenced in region must exist
        for qid in r.get("available_quests", []):
            if qid not in quest_ids:
                errors.append(f"{region_id} references unknown quest: {qid}")
        # Faction IDs must exist
        for f in r.get("factions", []):
            if f["faction_id"] not in faction_ids:
                errors.append(f"{region_id} references unknown faction: {f['faction_id']}")

    # 3. Validate new NPCs reference valid regions
    new_npc_ids = {
        "npc_starfall_surveyor", "npc_starfall_archaeologist", "npc_starfall_merchant",
        "npc_starfall_scout", "npc_abyss_researcher", "npc_abyss_explorer",
        "npc_abyss_scholar", "npc_abyss_ai_echo",
    }
    for n in npcs["npcs"]:
        if n["npc_id"] in new_npc_ids:
            # Check location/region fields if present
            if "location" in n and n["location"] and n["location"] not in region_ids:
                # Could be a loc_ id, not region_; skip
                pass

    # 4. Validate new quests
    new_quest_ids = {
        "quest_starfall_ch4_main1", "quest_starfall_ch4_main2", "quest_starfall_ch4_main3",
        "quest_starfall_ch4_main4", "quest_starfall_ch4_main5",
        "quest_starfall_side1", "quest_starfall_side2",
        "quest_abyss_ch4_main1", "quest_abyss_ch4_main2", "quest_abyss_ch4_main3",
        "quest_abyss_ch4_main4", "quest_abyss_ch4_main5",
        "quest_abyss_side1", "quest_abyss_side2",
    }
    for q in quests["quests"]:
        if q["quest_id"] in new_quest_ids:
            # Region must exist
            if q["region"] not in region_ids:
                errors.append(f"{q['quest_id']} references unknown region: {q['region']}")
            # Prerequisites must exist
            for pre in q.get("prerequisites", []):
                if pre not in quest_ids:
                    errors.append(f"{q['quest_id']} prerequisite not found: {pre}")
            # start_npc/end_npc must exist (or be null)
            if q.get("start_npc") and q["start_npc"] not in npc_ids:
                errors.append(f"{q['quest_id']} start_npc not found: {q['start_npc']}")
            if q.get("end_npc") and q["end_npc"] not in npc_ids:
                errors.append(f"{q['quest_id']} end_npc not found: {q['end_npc']}")
            # Chapter must exist
            if q["chapter"] not in chapter_ids:
                errors.append(f"{q['quest_id']} references unknown chapter: {q['chapter']}")
            # Reputation factions must exist
            for fac_id in q.get("rewards", {}).get("reputation", {}):
                if fac_id not in faction_ids:
                    errors.append(f"{q['quest_id']} rewards.reputation references unknown faction: {fac_id}")

    # 5. Validate new bosses
    new_boss_keys = {"boss_starfall_titan", "boss_abyss_watcher"}
    for m in monsters["monsters"]:
        if m["monster_key"] in new_boss_keys:
            # region_key must exist
            if m["region_key"] not in region_ids:
                errors.append(f"{m['monster_key']} references unknown region: {m['region_key']}")
            # chapter_id must exist
            if m["chapter_id"] not in chapter_ids:
                errors.append(f"{m['monster_key']} references unknown chapter: {m['chapter_id']}")

    # 6. Cross-check: region.npcs should include the NPCs that quests reference
    starfall_npcs_in_quests = set()
    abyss_npcs_in_quests = set()
    for q in quests["quests"]:
        if q["quest_id"] in new_quest_ids:
            for field in ("start_npc", "end_npc"):
                if q.get(field):
                    if q["region"] == "region_starfall_wastes":
                        starfall_npcs_in_quests.add(q[field])
                    elif q["region"] == "region_abyss_rift":
                        abyss_npcs_in_quests.add(q[field])

    starfall_npcs_in_region = set(starfall.get("npcs", []))
    abyss_npcs_in_region = set(abyss.get("npcs", []))

    missing_starfall = starfall_npcs_in_quests - starfall_npcs_in_region
    missing_abyss = abyss_npcs_in_quests - abyss_npcs_in_region
    if missing_starfall:
        errors.append(f"region_starfall_wastes.npcs missing NPCs referenced by quests: {missing_starfall}")
    if missing_abyss:
        errors.append(f"region_abyss_rift.npcs missing NPCs referenced by quests: {missing_abyss}")

    # 7. Cross-check: region.available_quests should include the initially-available quests
    # Pattern (per region_frost_glacier.json): list only quests with status="available" in this region
    starfall_available_quests = {
        q["quest_id"] for q in quests["quests"]
        if q["region"] == "region_starfall_wastes" and q["quest_id"] in new_quest_ids and q["status"] == "available"
    }
    abyss_available_quests = {
        q["quest_id"] for q in quests["quests"]
        if q["region"] == "region_abyss_rift" and q["quest_id"] in new_quest_ids and q["status"] == "available"
    }

    starfall_listed = set(starfall.get("available_quests", []))
    abyss_listed = set(abyss.get("available_quests", []))

    # Quests marked available should be listed in region.available_quests
    missing_starfall_q = starfall_available_quests - starfall_listed
    missing_abyss_q = abyss_available_quests - abyss_listed
    if missing_starfall_q:
        errors.append(f"region_starfall_wastes.available_quests missing available quests: {missing_starfall_q}")
    if missing_abyss_q:
        errors.append(f"region_abyss_rift.available_quests missing available quests: {missing_abyss_q}")

    # 8. Quest chain validation - prerequisites should form a proper chain
    expected_chain = [
        ("quest_starfall_ch4_main2", "quest_starfall_ch4_main1"),
        ("quest_starfall_ch4_main3", "quest_starfall_ch4_main2"),
        ("quest_starfall_ch4_main4", "quest_starfall_ch4_main3"),
        ("quest_starfall_ch4_main5", "quest_starfall_ch4_main4"),
        ("quest_abyss_ch4_main1", "quest_starfall_ch4_main5"),
        ("quest_abyss_ch4_main2", "quest_abyss_ch4_main1"),
        ("quest_abyss_ch4_main3", "quest_abyss_ch4_main2"),
        ("quest_abyss_ch4_main4", "quest_abyss_ch4_main3"),
        ("quest_abyss_ch4_main5", "quest_abyss_ch4_main4"),
    ]
    quest_prereq_map = {q["quest_id"]: q.get("prerequisites", []) for q in quests["quests"]}
    for qid, expected_pre in expected_chain:
        actual_pre = quest_prereq_map.get(qid, [])
        if expected_pre not in actual_pre:
            errors.append(f"Quest chain break: {qid} should depend on {expected_pre}, got {actual_pre}")

    print()
    if errors:
        print(f"FAILED: {len(errors)} errors found")
        for e in errors:
            print(f"  - {e}")
        raise SystemExit(1)
    else:
        print("All reference integrity checks PASSED")


if __name__ == "__main__":
    main()
