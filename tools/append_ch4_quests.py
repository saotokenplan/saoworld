"""Append 14 new Chapter 4 quests to quest_list.json."""
import json
from pathlib import Path

QUEST_FILE = Path("/workspace/game/data/quests/quest_list.json")


def make_quest(
    quest_id: str,
    title: str,
    description: str,
    qtype: str,
    chapter: str,
    status: str,
    prerequisites: list[str],
    objectives: list[dict],
    rewards: dict,
    start_npc: str | None,
    end_npc: str | None,
    region: str,
) -> dict:
    return {
        "quest_id": quest_id,
        "title": title,
        "description": description,
        "type": qtype,
        "chapter": chapter,
        "status": status,
        "prerequisites": prerequisites,
        "objectives": objectives,
        "rewards": rewards,
        "failure_condition": None,
        "start_npc": start_npc,
        "end_npc": end_npc,
        "region": region,
    }


# ==================== Starfall main quest chain (5) ====================
starfall_main1 = make_quest(
    quest_id="quest_starfall_ch4_main1",
    title="荒原抵达",
    description="抵达星陨荒原，向丰收商会勘探队长马库斯·铁钻报到，了解天裂事件的核心区域情况",
    qtype="main",
    chapter="chapter_04",
    status="available",
    prerequisites=["quest_glacier_ch3_main5"],
    objectives=[
        {"id": "obj_enter_starfall", "description": "进入星陨荒原区域", "type": "location", "target": "loc_starfall_observatory"},
        {"id": "obj_talk_surveyor", "description": "与马库斯·铁钻交谈", "type": "npc", "target": "npc_starfall_surveyor"},
        {"id": "obj_survey_observatory", "description": "视察陨星观察站", "type": "explore", "target": "loc_starfall_observatory"},
        {"id": "obj_accept_survey_mission", "description": "接受勘探任务", "type": "story", "target": "accept_mission"}
    ],
    rewards={"experience": 800, "reputation": {"faction_harvest": 80}, "gold": 100},
    start_npc=None,
    end_npc="npc_starfall_surveyor",
    region="region_starfall_wastes",
)

starfall_main2 = make_quest(
    quest_id="quest_starfall_ch4_main2",
    title="异星能量",
    description="深入辐射荒原收集异星能量样本，遭遇流浪商人老杰克，得知天裂核心的光柱方向并非向上而是向下的异常现象",
    qtype="main",
    chapter="chapter_04",
    status="locked",
    prerequisites=["quest_starfall_ch4_main1"],
    objectives=[
        {"id": "obj_enter_radiation", "description": "进入辐射荒原", "type": "location", "target": "loc_radiation_wastes"},
        {"id": "obj_collect_samples", "description": "收集异星能量样本", "type": "collect", "target": 5},
        {"id": "obj_defeat_mutants", "description": "击退变异生物", "type": "combat", "target": 6},
        {"id": "obj_meet_jack", "description": "与老杰克·星尘交谈", "type": "npc", "target": "npc_starfall_merchant"},
        {"id": "obj_learn_underground", "description": "得知光柱方向异常", "type": "story", "target": "underground_truth"}
    ],
    rewards={"experience": 1200, "reputation": {"faction_harvest": 100}, "gold": 200},
    start_npc="npc_starfall_surveyor",
    end_npc="npc_starfall_merchant",
    region="region_starfall_wastes",
)

starfall_main3 = make_quest(
    quest_id="quest_starfall_ch4_main3",
    title="远古星门",
    description="前往远古星门遗迹，协助暗影面纱考古学家塞拉芬娜·暗纹解读星门符文，得知天裂事件与地底深渊的关联",
    qtype="main",
    chapter="chapter_04",
    status="locked",
    prerequisites=["quest_starfall_ch4_main2"],
    objectives=[
        {"id": "obj_reach_stargate", "description": "前往远古星门", "type": "location", "target": "loc_ancient_stargate"},
        {"id": "obj_talk_archaeologist", "description": "与塞拉芬娜·暗纹交谈", "type": "npc", "target": "npc_starfall_archaeologist"},
        {"id": "obj_help_decipher", "description": "协助解读星门符文", "type": "explore", "target": 4},
        {"id": "obj_defend_ruins", "description": "击退入侵遗迹的变异生物", "type": "combat", "target": 8},
        {"id": "obj_learn_door_truth", "description": "得知天裂与地底深渊的关联", "type": "story", "target": "door_truth"}
    ],
    rewards={"experience": 1500, "reputation": {"faction_shadowveil": 120, "faction_harvest": 50}, "gold": 250},
    start_npc="npc_starfall_merchant",
    end_npc="npc_starfall_archaeologist",
    region="region_starfall_wastes",
)

starfall_main4 = make_quest(
    quest_id="quest_starfall_ch4_main4",
    title="天裂核心",
    description="在天裂核心边缘收集能量波动数据，与自由领地侦察兵艾拉·疾风合作，确认地底才是天裂事件的真正源头",
    qtype="main",
    chapter="chapter_04",
    status="locked",
    prerequisites=["quest_starfall_ch4_main3"],
    objectives=[
        {"id": "obj_meet_scout", "description": "与艾拉·疾风会面", "type": "npc", "target": "npc_starfall_scout"},
        {"id": "obj_approach_core", "description": "接近天裂核心边缘", "type": "location", "target": "loc_rift_core"},
        {"id": "obj_record_energy", "description": "记录能量波动数据", "type": "story", "target": 3},
        {"id": "obj_survive_distortion", "description": "在空间扭曲中存活", "type": "combat", "target": 4},
        {"id": "obj_confirm_source", "description": "确认地底是真正源头", "type": "story", "target": "confirm_source"}
    ],
    rewards={"experience": 2000, "reputation": {"faction_freehold": 150, "faction_shadowveil": 80}, "gold": 300},
    start_npc="npc_starfall_archaeologist",
    end_npc="npc_starfall_scout",
    region="region_starfall_wastes",
)

starfall_main5 = make_quest(
    quest_id="quest_starfall_ch4_main5",
    title="真相碎片",
    description="击败星陨泰坦——远古星门残留能量激活的守护者，获取它守护的远古核心碎片，开启通往深渊裂隙的入口",
    qtype="main",
    chapter="chapter_04",
    status="locked",
    prerequisites=["quest_starfall_ch4_main4"],
    objectives=[
        {"id": "obj_locate_titan", "description": "找到星陨泰坦的位置", "type": "explore", "target": "loc_rift_core"},
        {"id": "obj_defeat_titan", "description": "击败星陨泰坦", "type": "combat", "target": "boss_starfall_titan"},
        {"id": "obj_collect_fragment", "description": "获取远古核心碎片", "type": "collect", "target": 1},
        {"id": "obj_activate_rift_entrance", "description": "激活深渊裂隙入口", "type": "story", "target": "activate_entrance"},
        {"id": "obj_report_scout", "description": "向艾拉·疾风报告", "type": "npc", "target": "npc_starfall_scout"}
    ],
    rewards={"experience": 3000, "reputation": {"faction_freehold": 200, "faction_harvest": 100, "faction_shadowveil": 100}, "gold": 500},
    start_npc="npc_starfall_scout",
    end_npc="npc_starfall_scout",
    region="region_starfall_wastes",
)

# ==================== Starfall side quests (2) ====================
starfall_side1 = make_quest(
    quest_id="quest_starfall_side1",
    title="辐射样本采集",
    description="帮助丰收商会勘探队长马库斯收集辐射荒原上不同区域的辐射样本，用于分析异星能量的分布规律",
    qtype="side",
    chapter="chapter_04",
    status="available",
    prerequisites=["quest_starfall_ch4_main1"],
    objectives=[
        {"id": "obj_talk_surveyor", "description": "与马库斯·铁钻交谈", "type": "npc", "target": "npc_starfall_surveyor"},
        {"id": "obj_collect_shallow", "description": "采集浅层辐射样本", "type": "collect", "target": 3},
        {"id": "obj_collect_deep", "description": "采集深层辐射样本", "type": "collect", "target": 2},
        {"id": "obj_defeat_mutants", "description": "击退采集路线上的变异生物", "type": "combat", "target": 5},
        {"id": "obj_return_surveyor", "description": "将样本交给马库斯", "type": "npc", "target": "npc_starfall_surveyor"}
    ],
    rewards={"experience": 1000, "reputation": {"faction_harvest": 100}, "gold": 200},
    start_npc="npc_starfall_surveyor",
    end_npc="npc_starfall_surveyor",
    region="region_starfall_wastes",
)

starfall_side2 = make_quest(
    quest_id="quest_starfall_side2",
    title="失踪勘探队",
    description="调查失踪的前一队商会勘探队员，找回他们携带的研究笔记，协助暗影面纱考古学家塞拉芬娜解读星门符文",
    qtype="side",
    chapter="chapter_04",
    status="available",
    prerequisites=["quest_starfall_ch4_main1"],
    objectives=[
        {"id": "obj_talk_archaeologist", "description": "与塞拉芬娜·暗纹交谈", "type": "npc", "target": "npc_starfall_archaeologist"},
        {"id": "obj_find_camp", "description": "找到失踪勘探队的最后营地", "type": "explore", "target": "lost_camp"},
        {"id": "obj_find_clues", "description": "寻找失踪线索", "type": "explore", "target": 3},
        {"id": "obj_defeat_predator", "description": "击败袭击勘探队的变异生物", "type": "combat", "target": 4},
        {"id": "obj_recover_notes", "description": "找回研究笔记", "type": "collect", "target": 1},
        {"id": "obj_return_archaeologist", "description": "将笔记交给塞拉芬娜", "type": "npc", "target": "npc_starfall_archaeologist"}
    ],
    rewards={"experience": 1200, "reputation": {"faction_shadowveil": 120, "faction_harvest": 60}, "gold": 250},
    start_npc="npc_starfall_archaeologist",
    end_npc="npc_starfall_archaeologist",
    region="region_starfall_wastes",
)

# ==================== Abyss main quest chain (5) ====================
abyss_main1 = make_quest(
    quest_id="quest_abyss_ch4_main1",
    title="地底入口",
    description="从天裂核心进入深渊裂隙，与暗影面纱首席研究员维克多·深渊会面，了解远古文明的最终秘密",
    qtype="main",
    chapter="chapter_04",
    status="locked",
    prerequisites=["quest_starfall_ch4_main5"],
    objectives=[
        {"id": "obj_enter_abyss", "description": "进入深渊裂隙", "type": "location", "target": "loc_rift_entrance"},
        {"id": "obj_talk_researcher", "description": "与维克多·深渊交谈", "type": "npc", "target": "npc_abyss_researcher"},
        {"id": "obj_survey_entrance", "description": "视察裂隙入口营地", "type": "explore", "target": "loc_rift_entrance"},
        {"id": "obj_accept_descent", "description": "接受下降任务", "type": "story", "target": "accept_descent"}
    ],
    rewards={"experience": 2500, "reputation": {"faction_shadowveil": 150}, "gold": 300},
    start_npc=None,
    end_npc="npc_abyss_researcher",
    region="region_abyss_rift",
)

abyss_main2 = make_quest(
    quest_id="quest_abyss_ch4_main2",
    title="水晶回响",
    description="深入水晶大厅，与铁卫联盟探险家托尔·铁靴会合，记录水晶共振频率以追踪远古文明的核心知识位置",
    qtype="main",
    chapter="chapter_04",
    status="locked",
    prerequisites=["quest_abyss_ch4_main1"],
    objectives=[
        {"id": "obj_reach_crystal_hall", "description": "前往水晶大厅", "type": "location", "target": "loc_crystal_hall"},
        {"id": "obj_talk_explorer", "description": "与托尔·铁靴交谈", "type": "npc", "target": "npc_abyss_explorer"},
        {"id": "obj_record_resonance", "description": "记录水晶共振频率", "type": "explore", "target": 5},
        {"id": "obj_defend_creatures", "description": "击退地底生物", "type": "combat", "target": 8},
        {"id": "obj_locate_core_source", "description": "定位核心知识位置", "type": "story", "target": "locate_source"}
    ],
    rewards={"experience": 3000, "reputation": {"faction_ironward": 120, "faction_shadowveil": 100}, "gold": 400},
    start_npc="npc_abyss_researcher",
    end_npc="npc_abyss_explorer",
    region="region_abyss_rift",
)

abyss_main3 = make_quest(
    quest_id="quest_abyss_ch4_main3",
    title="深渊之眼",
    description="前往深渊之眼，与自由领地学者琳娜·书页合作破译深渊之眼附近的水晶记忆，得知远古文明引发天裂的真正原因",
    qtype="main",
    chapter="chapter_04",
    status="locked",
    prerequisites=["quest_abyss_ch4_main2"],
    objectives=[
        {"id": "obj_reach_eye", "description": "前往深渊之眼", "type": "location", "target": "loc_abyss_eye"},
        {"id": "obj_talk_scholar", "description": "与琳娜·书页交谈", "type": "npc", "target": "npc_abyss_scholar"},
        {"id": "obj_survive_distortion", "description": "在空间扭曲中存活", "type": "combat", "target": 5},
        {"id": "obj_decipher_crystal", "description": "破译水晶记忆", "type": "explore", "target": 4},
        {"id": "obj_learn_sacrifice", "description": "得知远古文明的牺牲真相", "type": "story", "target": "sacrifice_truth"}
    ],
    rewards={"experience": 4000, "reputation": {"faction_freehold": 150, "faction_shadowveil": 120}, "gold": 500},
    start_npc="npc_abyss_explorer",
    end_npc="npc_abyss_scholar",
    region="region_abyss_rift",
)

abyss_main4 = make_quest(
    quest_id="quest_abyss_ch4_main4",
    title="远古核心",
    description="深入远古核心室，与远古守护AI残影对话，得知虚空使者的存在与封印松动的危机",
    qtype="main",
    chapter="chapter_04",
    status="locked",
    prerequisites=["quest_abyss_ch4_main3"],
    objectives=[
        {"id": "obj_reach_core_chamber", "description": "前往远古核心室", "type": "location", "target": "loc_ancient_core_chamber"},
        {"id": "obj_meet_ai_echo", "description": "与远古 AI 残影对话", "type": "npc", "target": "npc_abyss_ai_echo"},
        {"id": "obj_defend_mechanisms", "description": "击退失控的远古守护机制", "type": "combat", "target": 6},
        {"id": "obj_learn_void_truth", "description": "得知虚空使者的存在", "type": "story", "target": "void_truth"},
        {"id": "obj_learn_seal_failure", "description": "得知封印松动的危机", "type": "story", "target": "seal_failure"}
    ],
    rewards={"experience": 5000, "reputation": {"faction_shadowveil": 200, "faction_freehold": 100}, "gold": 600},
    start_npc="npc_abyss_scholar",
    end_npc="npc_abyss_ai_echo",
    region="region_abyss_rift",
)

abyss_main5 = make_quest(
    quest_id="quest_abyss_ch4_main5",
    title="终极真相",
    description="击败深渊监视者——远古文明遗留的失控守护AI，获取其核心并带回远古核心室，由残影指引完成封印加固仪式，闭合天裂之谜",
    qtype="main",
    chapter="chapter_04",
    status="locked",
    prerequisites=["quest_abyss_ch4_main4"],
    objectives=[
        {"id": "obj_locate_watcher", "description": "找到深渊监视者", "type": "explore", "target": "loc_abyss_eye"},
        {"id": "obj_defeat_watcher", "description": "击败深渊监视者", "type": "combat", "target": "boss_abyss_watcher"},
        {"id": "obj_collect_watcher_core", "description": "获取深渊监视者核心", "type": "collect", "target": 1},
        {"id": "obj_return_ai_echo", "description": "回到远古核心室", "type": "location", "target": "loc_ancient_core_chamber"},
        {"id": "obj_complete_ritual", "description": "完成封印加固仪式", "type": "story", "target": "complete_seal"}
    ],
    rewards={"experience": 8000, "reputation": {"faction_shadowveil": 300, "faction_ironward": 150, "faction_freehold": 150, "faction_harvest": 100}, "gold": 1000},
    start_npc="npc_abyss_ai_echo",
    end_npc="npc_abyss_ai_echo",
    region="region_abyss_rift",
)

# ==================== Abyss side quests (2) ====================
abyss_side1 = make_quest(
    quest_id="quest_abyss_side1",
    title="水晶采集",
    description="帮助铁卫联盟探险家托尔·铁靴采集特殊共振水晶，校准他的能量探测器，以更好地绘制深渊裂隙地图",
    qtype="side",
    chapter="chapter_04",
    status="available",
    prerequisites=["quest_abyss_ch4_main1"],
    objectives=[
        {"id": "obj_talk_explorer", "description": "与托尔·铁靴交谈", "type": "npc", "target": "npc_abyss_explorer"},
        {"id": "obj_collect_shallow", "description": "采集浅层共振水晶", "type": "collect", "target": 5},
        {"id": "obj_collect_deep", "description": "采集深层共振水晶", "type": "collect", "target": 3},
        {"id": "obj_defend_creatures", "description": "击退采集路线上的地底生物", "type": "combat", "target": 6},
        {"id": "obj_return_explorer", "description": "将水晶交给托尔", "type": "npc", "target": "npc_abyss_explorer"}
    ],
    rewards={"experience": 1500, "reputation": {"faction_ironward": 120}, "gold": 300},
    start_npc="npc_abyss_explorer",
    end_npc="npc_abyss_explorer",
    region="region_abyss_rift",
)

abyss_side2 = make_quest(
    quest_id="quest_abyss_side2",
    title="远古文献解读",
    description="协助自由领地学者琳娜·书页拓印深渊之眼附近的水晶符文，破译远古文明的最后记忆片段",
    qtype="side",
    chapter="chapter_04",
    status="available",
    prerequisites=["quest_abyss_ch4_main1"],
    objectives=[
        {"id": "obj_talk_scholar", "description": "与琳娜·书页交谈", "type": "npc", "target": "npc_abyss_scholar"},
        {"id": "obj_reach_eye", "description": "前往深渊之眼附近", "type": "location", "target": "loc_abyss_eye"},
        {"id": "obj_rubbing_runes", "description": "拓印水晶符文", "type": "collect", "target": 6},
        {"id": "obj_resist_hallucination", "description": "抵抗远古记忆幻觉", "type": "combat", "target": 3},
        {"id": "obj_return_scholar", "description": "将拓印交给琳娜", "type": "npc", "target": "npc_abyss_scholar"}
    ],
    rewards={"experience": 1800, "reputation": {"faction_freehold": 150, "faction_shadowveil": 80}, "gold": 350},
    start_npc="npc_abyss_scholar",
    end_npc="npc_abyss_scholar",
    region="region_abyss_rift",
)


new_quests = [
    starfall_main1, starfall_main2, starfall_main3, starfall_main4, starfall_main5,
    starfall_side1, starfall_side2,
    abyss_main1, abyss_main2, abyss_main3, abyss_main4, abyss_main5,
    abyss_side1, abyss_side2,
]


def main() -> None:
    data = json.loads(QUEST_FILE.read_text(encoding="utf-8"))
    existing_ids = {q["quest_id"] for q in data["quests"]}
    for q in new_quests:
        if q["quest_id"] in existing_ids:
            raise SystemExit(f"Quest ID collision: {q['quest_id']}")
        data["quests"].append(q)
    QUEST_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Appended {len(new_quests)} quests. Total: {len(data['quests'])}")


if __name__ == "__main__":
    main()
