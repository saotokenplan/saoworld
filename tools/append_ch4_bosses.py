"""Append 2 new Chapter 4 bosses to monster_list.json."""
import json
from pathlib import Path

MONSTER_FILE = Path("/workspace/game/data/monsters/monster_list.json")


def make_boss(
    monster_key: str,
    name: str,
    chapter_id: str,
    region_key: str,
    level: int,
    hp: int,
    attack: int,
    defense: int,
    speed: int,
    description: str,
    aggression: str,
    attack_pattern: str,
    special_behaviors: list[str],
    loot_table: list[dict],
    basic_skills: list[dict],
    boss_rank: str,
    phase_count: int,
    phase_names: list[str],
    special_skills: list[dict],
    enrage_threshold: float,
    reward: dict,
) -> dict:
    return {
        "monster_key": monster_key,
        "name": name,
        "monster_type": "boss",
        "chapter_id": chapter_id,
        "region_key": region_key,
        "level": level,
        "hp": hp,
        "attack": attack,
        "defense": defense,
        "speed": speed,
        "description": description,
        "behavior_pattern": {
            "aggression": aggression,
            "attack_pattern": attack_pattern,
            "special_behaviors": special_behaviors,
        },
        "loot_table": loot_table,
        "skills": basic_skills,
        "is_boss": True,
        "boss_rank": boss_rank,
        "phase_count": phase_count,
        "phase_names": phase_names,
        "special_skills": special_skills,
        "enrage_threshold": enrage_threshold,
        "reward": reward,
        "min_reputation": 0,
    }


# ==================== Starfall Titan ====================
starfall_titan = make_boss(
    monster_key="boss_starfall_titan",
    name="星陨泰坦",
    chapter_id="chapter_04",
    region_key="region_starfall_wastes",
    level=35,
    hp=4500,
    attack=58,
    defense=22,
    speed=6,
    description=(
        "远古星门残留能量激活的守护者，由陨石核心与远古金属构成的巨大人形生命体。"
        "它原本是远古文明用来守护星门的战争机器，在天裂事件中被异星能量重新激活。"
        "它拥有操控重力场的能力，能将周围的物质压缩成 projectile 攻击入侵者。"
        "随着战斗的进行，它会逐步激活体内沉睡的星陨能量，进入更危险的战斗阶段。"
    ),
    aggression="aggressive",
    attack_pattern="mixed",
    special_behaviors=["enrage", "phase_change", "gravity_field"],
    loot_table=[
        {"item_key": "item_starfall_titan_core", "drop_rate": 1.0, "quantity_min": 1, "quantity_max": 1},
        {"item_key": "item_ancient_core_fragment", "drop_rate": 1.0, "quantity_min": 1, "quantity_max": 1},
        {"item_key": "item_starfall_essence", "drop_rate": 0.9, "quantity_min": 3, "quantity_max": 6},
        {"item_key": "item_gold_coin", "drop_rate": 0.9, "quantity_min": 80, "quantity_max": 150},
    ],
    basic_skills=[
        {"skill_key": "skill_gravity_smash", "name": "重力重击", "damage_multiplier": 1.3, "cooldown": 0},
        {"skill_key": "skill_meteor_throw", "name": "陨石投掷", "damage_multiplier": 1.5, "cooldown": 3},
    ],
    boss_rank="mythic",
    phase_count=3,
    phase_names=["苏醒阶段", "重力阶段", "星陨阶段"],
    special_skills=[
        {"skill_key": "skill_gravity_field", "name": "重力场", "description": "展开重力场，使范围内玩家移动速度降低50%并受到持续伤害", "cooldown": 10},
        {"skill_key": "skill_meteor_shower", "name": "陨石雨", "description": "召唤多颗陨石从天而降，覆盖大片区域造成范围伤害", "cooldown": 15},
        {"skill_key": "skill_gravity_compression", "name": "重力压缩", "description": "将周围物质压缩成 projectile 攻击玩家，需要躲到掩体后躲避", "cooldown": 12},
        {"skill_key": "skill_starfall_awakening", "name": "星陨觉醒", "description": "激活体内星陨能量，攻击力大幅提升并附带能量伤害", "cooldown": 18},
        {"skill_key": "skill_ultimate_collapse", "name": "终极坍缩", "description": "蓄力后释放重力坍缩，将所有玩家吸向中心并造成毁灭性伤害", "cooldown": 25},
    ],
    enrage_threshold=0.25,
    reward={
        "experience": 18000,
        "items": [
            {"item_key": "item_starfall_titan_core", "quantity": 1},
            {"item_key": "item_ancient_core_fragment", "quantity": 1},
            {"item_key": "item_starfall_essence", "quantity": 5},
        ],
    },
)


# ==================== Abyss Watcher ====================
abyss_watcher = make_boss(
    monster_key="boss_abyss_watcher",
    name="深渊监视者",
    chapter_id="chapter_04",
    region_key="region_abyss_rift",
    level=48,
    hp=6500,
    attack=70,
    defense=25,
    speed=8,
    description=(
        "远古文明遗留的失控守护AI，由远古水晶与液态金属构成的漂浮生命体。"
        "它原本是远古文明用来监视深渊封印的智能系统，在天裂事件中因封印松动而失控。"
        "它拥有操控水晶能量和空间扭曲的能力，能在战斗中改变战场结构。"
        "它的意识在千万年的孤独中逐渐扭曲，从守护者变成了毁灭者，"
        "试图通过摧毁一切生命来阻止封印彻底崩溃。"
    ),
    aggression="strategic",
    attack_pattern="magic",
    special_behaviors=["enrage", "phase_change", "space_distortion", "summon"],
    loot_table=[
        {"item_key": "item_abyss_watcher_core", "drop_rate": 1.0, "quantity_min": 1, "quantity_max": 1},
        {"item_key": "item_abyss_crystal", "drop_rate": 0.9, "quantity_min": 3, "quantity_max": 6},
        {"item_key": "item_ancient_seal_fragment", "drop_rate": 0.7, "quantity_min": 1, "quantity_max": 2},
        {"item_key": "item_gold_coin", "drop_rate": 0.9, "quantity_min": 100, "quantity_max": 200},
    ],
    basic_skills=[
        {"skill_key": "skill_crystal_beam", "name": "水晶光束", "damage_multiplier": 1.4, "cooldown": 0},
        {"skill_key": "skill_space_rift", "name": "空间裂隙", "damage_multiplier": 1.2, "cooldown": 2},
    ],
    boss_rank="legendary",
    phase_count=4,
    phase_names=["守护阶段", "失控阶段", "扭曲阶段", "终焉阶段"],
    special_skills=[
        {"skill_key": "skill_crystal_barrage", "name": "水晶弹幕", "description": "向四周发射密集的水晶投射物，需要灵活走位躲避", "cooldown": 8},
        {"skill_key": "skill_space_distortion", "name": "空间扭曲", "description": "扭曲战场结构，改变玩家位置和移动方向，需要快速适应", "cooldown": 12},
        {"skill_key": "skill_abyss_gaze", "name": "深渊凝视", "description": "凝视目标区域，3秒后造成毁灭性伤害，需要及时离开标记区域", "cooldown": 15},
        {"skill_key": "skill_summon_crystal_golem", "name": "召唤水晶巨像", "description": "召唤2个水晶巨像仆从协助战斗，巨像被击破时会爆炸造成范围伤害", "cooldown": 20},
        {"skill_key": "skill_seal_breaker", "name": "封印破坏", "description": "释放能量攻击封印本身，玩家需要在限定时间内打断否则被全屏秒杀", "cooldown": 18},
        {"skill_key": "skill_ultimate_void", "name": "终极虚空", "description": "终极技能，将战场拉入虚空空间，所有玩家生命值持续下降且治疗效果降低50%，需要在60秒内击败它否则团灭", "cooldown": 30},
    ],
    enrage_threshold=0.2,
    reward={
        "experience": 25000,
        "items": [
            {"item_key": "item_abyss_watcher_core", "quantity": 1},
            {"item_key": "item_abyss_crystal", "quantity": 5},
            {"item_key": "item_ancient_seal_fragment", "quantity": 2},
            {"item_key": "item_seal_key_fragment", "quantity": 1},
        ],
    },
)


new_bosses = [starfall_titan, abyss_watcher]


def main() -> None:
    data = json.loads(MONSTER_FILE.read_text(encoding="utf-8"))
    existing_keys = {m["monster_key"] for m in data["monsters"]}
    for b in new_bosses:
        if b["monster_key"] in existing_keys:
            raise SystemExit(f"Monster key collision: {b['monster_key']}")
        data["monsters"].append(b)
    MONSTER_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Appended {len(new_bosses)} bosses. Total: {len(data['monsters'])}")


if __name__ == "__main__":
    main()
