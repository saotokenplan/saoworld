import uuid
from typing import Any


class BossDataAdapter:
    """Boss数据转换适配器。

    将 AI 生成的Boss数据转换为 world-service 兼容的格式。
    """

    REQUIRED_FIELDS = [
        "monster_key",
        "name",
        "chapter_id",
        "region_key",
        "level",
        "hp",
        "attack",
        "defense",
        "speed",
        "description",
        "behavior_pattern",
        "loot_table",
        "skills",
        "is_boss",
        "boss_rank",
        "phase_count",
        "special_skills",
        "enrage_threshold",
        "reward",
    ]

    VALID_BOSS_RANKS = ["legendary", "mythic"]

    def __init__(self, chapter_id: str = "chapter_01"):
        self.chapter_id = chapter_id

    def adapt(self, raw_boss_data: dict[str, Any]) -> dict[str, Any]:
        """将原始Boss数据转换为 world-service 兼容格式。

        Args:
            raw_boss_data: AI 生成的原始Boss数据

        Returns:
            转换后的Boss数据，符合 world-service MonsterDefinition 模型
        """
        adapted: dict[str, Any] = {}

        adapted["monster_key"] = self._normalize_monster_key(raw_boss_data.get("monster_key"))
        adapted["name"] = raw_boss_data.get("name", "")
        adapted["monster_type"] = "boss"
        adapted["chapter_id"] = raw_boss_data.get("chapter_id", self.chapter_id)
        adapted["region_key"] = self._normalize_region_key(raw_boss_data.get("region_key"))
        adapted["level"] = self._normalize_int(raw_boss_data.get("level"), min_val=5, max_val=60, default=10)
        adapted["hp"] = self._normalize_int(raw_boss_data.get("hp"), min_val=100, default=500)
        adapted["attack"] = self._normalize_int(raw_boss_data.get("attack"), min_val=10, default=30)
        adapted["defense"] = self._normalize_int(raw_boss_data.get("defense"), min_val=5, default=10)
        adapted["speed"] = self._normalize_int(raw_boss_data.get("speed"), min_val=1, default=5)
        adapted["description"] = raw_boss_data.get("description") or None
        adapted["behavior_pattern"] = self._normalize_behavior_pattern(raw_boss_data.get("behavior_pattern"))
        adapted["loot_table"] = self._normalize_loot_table(raw_boss_data.get("loot_table"))
        adapted["skills"] = self._normalize_skills(raw_boss_data.get("skills"))
        adapted["min_reputation"] = self._normalize_int(raw_boss_data.get("min_reputation"), min_val=0, default=0)
        adapted["is_boss"] = True
        adapted["boss_rank"] = self._normalize_boss_rank(raw_boss_data.get("boss_rank"))
        adapted["phase_count"] = self._normalize_int(raw_boss_data.get("phase_count"), min_val=1, max_val=5, default=1)
        adapted["special_skills"] = self._normalize_special_skills(raw_boss_data.get("special_skills"))
        adapted["enrage_threshold"] = self._normalize_enrage_threshold(raw_boss_data.get("enrage_threshold"))
        adapted["reward"] = self._normalize_reward(raw_boss_data.get("reward"))

        return adapted

    def validate_completeness(self, boss_data: dict[str, Any]) -> tuple[float, list[str]]:
        """验证Boss数据字段完整度。

        Args:
            boss_data: Boss数据

        Returns:
            (完整度百分比, 缺失字段列表)
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            value = boss_data.get(field)
            if value is None:
                missing.append(field)
            elif isinstance(value, str) and not value.strip():
                missing.append(field)
            elif isinstance(value, (list, dict)) and len(value) == 0:
                if field in ["special_skills", "skills", "loot_table", "reward"]:
                    missing.append(field)

        total = len(self.REQUIRED_FIELDS)
        present = total - len(missing)
        completeness = present / total

        return completeness, missing

    def ensure_minimum_completeness(
        self, boss_data: dict[str, Any], min_completeness: float = 0.95
    ) -> dict[str, Any]:
        """确保Boss数据达到最小完整度要求。

        Args:
            boss_data: Boss数据
            min_completeness: 最小完整度要求（默认 0.95）

        Returns:
            填充默认值后的Boss数据

        Raises:
            ValueError: 完整度低于最小值
        """
        completeness, missing = self.validate_completeness(boss_data)
        if completeness < min_completeness:
            raise ValueError(
                f"Boss data completeness {completeness:.2%} below required {min_completeness:.2%}. "
                f"Missing fields: {', '.join(missing)}"
            )

        return self._fill_defaults(boss_data)

    def _fill_defaults(self, boss_data: dict[str, Any]) -> dict[str, Any]:
        """填充缺失字段的默认值。"""
        defaults = {
            "monster_key": f"boss_{uuid.uuid4().hex[:8]}",
            "name": "Unknown Boss",
            "monster_type": "boss",
            "chapter_id": self.chapter_id,
            "region_key": "region_unknown",
            "level": 10,
            "hp": 500,
            "attack": 30,
            "defense": 10,
            "speed": 5,
            "description": "A fearsome boss creature.",
            "behavior_pattern": {"aggression": "aggressive", "attack_pattern": "mixed", "special_behaviors": ["enrage"]},
            "loot_table": [{"item_key": "item_boss_loot", "drop_rate": 1.0}],
            "skills": [{"skill_key": "skill_boss_attack", "name": "Boss Attack", "damage_multiplier": 1.5}],
            "min_reputation": 0,
            "is_boss": True,
            "boss_rank": "legendary",
            "phase_count": 1,
            "special_skills": [{"skill_key": "skill_boss_special", "name": "Special Attack", "cooldown": 10}],
            "enrage_threshold": 0.3,
            "reward": {"experience": 1000, "items": []},
        }

        for key, default in defaults.items():
            value = boss_data.get(key)
            if value is None:
                boss_data[key] = default
            elif isinstance(value, str) and not value.strip():
                boss_data[key] = default
            elif isinstance(value, (list, dict)) and len(value) == 0:
                boss_data[key] = default

        return boss_data

    def _normalize_monster_key(self, monster_key: str | None) -> str:
        """规范化怪物 key。"""
        if not monster_key:
            return f"boss_{uuid.uuid4().hex[:8]}"
        if not monster_key.startswith("boss_"):
            return f"boss_{monster_key}"
        return monster_key

    def _normalize_region_key(self, region_key: str | None) -> str:
        """规范化区域 key。"""
        if not region_key:
            return "region_unknown"
        if not region_key.startswith("region_"):
            return f"region_{region_key}"
        return region_key

    def _normalize_int(self, value: Any, min_val: int = 0, max_val: int | None = None, default: int = 0) -> int:
        """规范化整数值。"""
        try:
            result = int(value)
        except (TypeError, ValueError):
            return default
        result = max(min_val, result)
        if max_val is not None:
            result = min(max_val, result)
        return result

    def _normalize_boss_rank(self, boss_rank: str | None) -> str:
        """规范化Boss等级。"""
        if not boss_rank:
            return "legendary"
        if boss_rank.lower() in self.VALID_BOSS_RANKS:
            return boss_rank.lower()
        return "legendary"

    def _normalize_behavior_pattern(self, behavior_pattern: Any) -> dict[str, Any]:
        """规范化行为模式。"""
        if isinstance(behavior_pattern, dict):
            return behavior_pattern
        return {"aggression": "aggressive", "attack_pattern": "mixed", "special_behaviors": ["enrage"]}

    def _normalize_loot_table(self, loot_table: Any) -> list[dict[str, Any]]:
        """规范化掉落表。"""
        if isinstance(loot_table, list):
            return loot_table
        return []

    def _normalize_skills(self, skills: Any) -> list[dict[str, Any]]:
        """规范化技能列表。"""
        if isinstance(skills, list):
            return skills
        return []

    def _normalize_special_skills(self, special_skills: Any) -> list[dict[str, Any]]:
        """规范化特殊技能列表。"""
        if isinstance(special_skills, list):
            return special_skills
        return []

    def _normalize_enrage_threshold(self, enrage_threshold: Any) -> float:
        """规范化狂暴阈值（0.0-1.0）。"""
        try:
            result = float(enrage_threshold)
        except (TypeError, ValueError):
            return 0.3
        return max(0.0, min(1.0, result))

    def _normalize_reward(self, reward: Any) -> dict[str, Any]:
        """规范化奖励数据。"""
        if isinstance(reward, dict):
            if "items" not in reward:
                reward["items"] = []
            if "experience" not in reward:
                reward["experience"] = 0
            return reward
        return {"experience": 1000, "items": []}


boss_data_adapter = BossDataAdapter()