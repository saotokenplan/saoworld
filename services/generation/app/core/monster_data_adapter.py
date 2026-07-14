"""怪物数据转换适配器模块。

将 AI 生成的怪物数据转换为 world-service 兼容的格式。
"""

import uuid
from typing import Any


class MonsterDataAdapter:
    """怪物数据转换适配器。"""

    REQUIRED_FIELDS = [
        "monster_key",
        "name",
        "monster_type",
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
    ]

    VALID_MONSTER_TYPES = [
        "beast", "humanoid", "undead", "mechanical",
        "elemental", "demon", "dragon", "boss",
    ]

    def __init__(self, chapter_id: str = "chapter_01"):
        self.chapter_id = chapter_id

    def adapt(self, raw_monster_data: dict[str, Any]) -> dict[str, Any]:
        """将原始怪物数据转换为 world-service 兼容格式。

        Args:
            raw_monster_data: AI 生成的原始怪物数据

        Returns:
            转换后的怪物数据，符合 world-service MonsterDefinition 模型
        """
        adapted: dict[str, Any] = {}

        adapted["monster_key"] = self._normalize_monster_key(raw_monster_data.get("monster_key"))
        adapted["name"] = raw_monster_data.get("name", "")
        adapted["monster_type"] = self._normalize_monster_type(raw_monster_data.get("monster_type"))
        adapted["chapter_id"] = raw_monster_data.get("chapter_id", self.chapter_id)
        adapted["region_key"] = self._normalize_region_key(raw_monster_data.get("region_key"))
        adapted["level"] = self._normalize_int(raw_monster_data.get("level"), min_val=1, max_val=60, default=1)
        adapted["hp"] = self._normalize_int(raw_monster_data.get("hp"), min_val=1, default=10)
        adapted["attack"] = self._normalize_int(raw_monster_data.get("attack"), min_val=0, default=5)
        adapted["defense"] = self._normalize_int(raw_monster_data.get("defense"), min_val=0, default=0)
        adapted["speed"] = self._normalize_int(raw_monster_data.get("speed"), min_val=0, default=5)
        adapted["description"] = raw_monster_data.get("description") or None
        adapted["behavior_pattern"] = self._normalize_behavior_pattern(raw_monster_data.get("behavior_pattern"))
        adapted["loot_table"] = self._normalize_loot_table(raw_monster_data.get("loot_table"))
        adapted["skills"] = self._normalize_skills(raw_monster_data.get("skills"))

        return adapted

    def validate_completeness(self, monster_data: dict[str, Any]) -> tuple[float, list[str]]:
        """验证怪物数据字段完整度。

        Args:
            monster_data: 怪物数据

        Returns:
            (完整度百分比, 缺失字段列表)
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            value = monster_data.get(field)
            if value is None:
                missing.append(field)
            elif isinstance(value, str) and not value.strip():
                missing.append(field)
            elif isinstance(value, (list, dict)) and len(value) == 0:
                missing.append(field)

        total = len(self.REQUIRED_FIELDS)
        present = total - len(missing)
        completeness = present / total

        return completeness, missing

    def ensure_minimum_completeness(
        self, monster_data: dict[str, Any], min_completeness: float = 0.95
    ) -> dict[str, Any]:
        """确保怪物数据达到最小完整度要求。

        Args:
            monster_data: 怪物数据
            min_completeness: 最小完整度要求（默认 0.95）

        Returns:
            填充默认值后的怪物数据

        Raises:
            ValueError: 完整度低于最小值
        """
        completeness, missing = self.validate_completeness(monster_data)
        if completeness < min_completeness:
            raise ValueError(
                f"Monster data completeness {completeness:.2%} below required {min_completeness:.2%}. "
                f"Missing fields: {', '.join(missing)}"
            )

        return self._fill_defaults(monster_data)

    def _fill_defaults(self, monster_data: dict[str, Any]) -> dict[str, Any]:
        """填充缺失字段的默认值。"""
        defaults = {
            "monster_key": f"monster_{uuid.uuid4().hex[:8]}",
            "name": "Unknown Monster",
            "monster_type": "beast",
            "chapter_id": self.chapter_id,
            "region_key": "region_unknown",
            "level": 1,
            "hp": 10,
            "attack": 5,
            "defense": 0,
            "speed": 5,
            "description": "A mysterious creature.",
            "behavior_pattern": {"aggression": "passive", "attack_pattern": "melee", "special_behaviors": []},
            "loot_table": [{"item_key": "item_generic_loot", "drop_rate": 0.5}],
            "skills": [{"skill_key": "skill_basic_attack", "name": "Basic Attack", "damage_multiplier": 1.0}],
        }

        for key, default in defaults.items():
            value = monster_data.get(key)
            if value is None:
                monster_data[key] = default
            elif isinstance(value, str) and not value.strip():
                monster_data[key] = default
            elif isinstance(value, (list, dict)) and len(value) == 0:
                monster_data[key] = default

        return monster_data

    def _normalize_monster_key(self, monster_key: str | None) -> str:
        """规范化怪物 key。"""
        if not monster_key:
            return f"monster_{uuid.uuid4().hex[:8]}"
        if not monster_key.startswith("monster_"):
            return f"monster_{monster_key}"
        return monster_key

    def _normalize_monster_type(self, monster_type: str | None) -> str:
        """规范化怪物类型。"""
        if not monster_type:
            return "beast"
        if monster_type.lower() in self.VALID_MONSTER_TYPES:
            return monster_type.lower()
        return "beast"

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

    def _normalize_behavior_pattern(self, behavior_pattern: Any) -> dict[str, Any]:
        """规范化行为模式。"""
        if isinstance(behavior_pattern, dict):
            return behavior_pattern
        return {"aggression": "passive", "attack_pattern": "melee", "special_behaviors": []}

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


monster_data_adapter = MonsterDataAdapter()
