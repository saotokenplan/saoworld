"""任务数据转换适配器模块。

将 AI 生成的任务数据转换为 world-service 兼容的格式。
"""

import uuid
from typing import Any


class QuestDataAdapter:
    """任务数据转换适配器。"""

    REQUIRED_FIELDS = [
        "quest_key",
        "title",
        "description",
        "quest_type",
        "chapter_id",
        "region_key",
        "objectives",
    ]

    VALID_QUEST_TYPES = {"main", "side", "event", "daily"}

    VALID_OBJECTIVE_TYPES = {
        "story",
        "location",
        "npc",
        "combat",
        "explore",
        "collect",
        "rescue",
        "travel",
        "quest",
    }

    def __init__(self, chapter_id: str = "chapter_01"):
        self.chapter_id = chapter_id

    def adapt(self, raw_quest_data: dict[str, Any]) -> dict[str, Any]:
        """将原始任务数据转换为 world-service 兼容格式。

        Args:
            raw_quest_data: AI 生成的原始任务数据

        Returns:
            转换后的任务数据，符合 world-service QuestDefinition 模型
        """
        adapted: dict[str, Any] = {}

        adapted["quest_key"] = self._normalize_quest_key(raw_quest_data.get("quest_key"))
        adapted["chapter_id"] = raw_quest_data.get("chapter_id") or self.chapter_id
        adapted["title"] = raw_quest_data.get("title", "")
        adapted["description"] = raw_quest_data.get("description") or None
        adapted["quest_type"] = self._normalize_quest_type(raw_quest_data.get("quest_type"))
        adapted["region_key"] = self._normalize_region_key(raw_quest_data.get("region_key"))
        adapted["start_npc_key"] = self._normalize_npc_key(raw_quest_data.get("start_npc_key"))
        adapted["end_npc_key"] = self._normalize_npc_key(raw_quest_data.get("end_npc_key"))
        adapted["prerequisites"] = self._normalize_prerequisites(raw_quest_data.get("prerequisites"))
        adapted["objectives"] = self._normalize_objectives(raw_quest_data.get("objectives"))
        adapted["rewards"] = self._normalize_rewards(raw_quest_data.get("rewards"))
        adapted["failure_condition"] = self._normalize_failure_condition(raw_quest_data.get("failure_condition"))

        return adapted

    def validate_completeness(self, quest_data: dict[str, Any]) -> tuple[float, list[str]]:
        """验证任务数据字段完整度。

        Args:
            quest_data: 任务数据

        Returns:
            (完整度百分比, 缺失字段列表)
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            value = quest_data.get(field)
            if value is None:
                missing.append(field)
            elif isinstance(value, str) and not value.strip():
                missing.append(field)
            elif isinstance(value, list) and len(value) == 0:
                missing.append(field)

        total = len(self.REQUIRED_FIELDS)
        present = total - len(missing)
        completeness = present / total

        return completeness, missing

    def ensure_minimum_completeness(
        self, quest_data: dict[str, Any], min_completeness: float = 0.95
    ) -> dict[str, Any]:
        """确保任务数据达到最小完整度要求。

        Args:
            quest_data: 任务数据
            min_completeness: 最小完整度要求（默认 0.95）

        Returns:
            填充默认值后的任务数据

        Raises:
            ValueError: 完整度低于最小值
        """
        completeness, missing = self.validate_completeness(quest_data)
        if completeness < min_completeness:
            raise ValueError(
                f"Quest data completeness {completeness:.2%} below required {min_completeness:.2%}. "
                f"Missing fields: {', '.join(missing)}"
            )

        return self._fill_defaults(quest_data)

    def _fill_defaults(self, quest_data: dict[str, Any]) -> dict[str, Any]:
        """填充缺失字段的默认值。"""
        defaults: dict[str, Any] = {
            "quest_key": f"quest_{uuid.uuid4().hex[:8]}",
            "title": "Unknown Quest",
            "description": "A mysterious quest.",
            "quest_type": "side",
            "chapter_id": self.chapter_id,
            "region_key": "region_unknown",
            "start_npc_key": None,
            "end_npc_key": None,
            "prerequisites": [],
            "objectives": [],
            "rewards": None,
            "failure_condition": None,
        }

        for key, default in defaults.items():
            if quest_data.get(key) is None:
                if key == "objectives":
                    quest_data[key] = [{"id": "obj_1", "description": "Complete the objective", "type": "story", "target": "", "completed": False}]
                elif key == "rewards":
                    quest_data[key] = {"experience": 100, "gold": 50, "reputation": {}, "items": []}
                else:
                    quest_data[key] = default
            elif isinstance(quest_data[key], str) and not quest_data[key].strip():
                quest_data[key] = default
            elif isinstance(quest_data[key], (list, dict)) and len(quest_data[key]) == 0:
                if key == "objectives":
                    quest_data[key] = [{"id": "obj_1", "description": "Complete the objective", "type": "story", "target": "", "completed": False}]
                elif key == "rewards":
                    quest_data[key] = {"experience": 100, "gold": 50, "reputation": {}, "items": []}
                else:
                    quest_data[key] = default

        return quest_data

    def _normalize_quest_key(self, quest_key: str | None) -> str:
        """规范化任务 key。"""
        if not quest_key:
            return f"quest_{uuid.uuid4().hex[:8]}"
        if not quest_key.startswith("quest_"):
            return f"quest_{quest_key}"
        return quest_key

    def _normalize_quest_type(self, quest_type: str | None) -> str:
        """规范化任务类型。"""
        if not quest_type:
            return "side"
        quest_type = quest_type.lower()
        if quest_type in self.VALID_QUEST_TYPES:
            return quest_type
        return "side"

    def _normalize_region_key(self, region_key: str | None) -> str | None:
        """规范化区域 key。"""
        if not region_key:
            return None
        if not region_key.startswith("region_"):
            return f"region_{region_key}"
        return region_key

    def _normalize_npc_key(self, npc_key: str | None) -> str | None:
        """规范化 NPC key。"""
        if not npc_key:
            return None
        if not npc_key.startswith("npc_"):
            return f"npc_{npc_key}"
        return npc_key

    def _normalize_prerequisites(self, prerequisites: Any) -> list[str]:
        """规范化前置条件列表。"""
        if isinstance(prerequisites, list):
            return [self._normalize_quest_key(str(p)) for p in prerequisites]
        return []

    def _normalize_objectives(self, objectives: Any) -> list[dict[str, Any]]:
        """规范化任务目标列表。"""
        if not isinstance(objectives, list):
            return []

        normalized = []
        for idx, obj in enumerate(objectives):
            if not isinstance(obj, dict):
                continue

            obj_id = obj.get("id") or f"obj_{idx + 1}"
            obj_type = obj.get("type", "story").lower()
            if obj_type not in self.VALID_OBJECTIVE_TYPES:
                obj_type = "story"

            normalized.append({
                "id": obj_id,
                "description": obj.get("description", ""),
                "type": obj_type,
                "target": obj.get("target", ""),
                "completed": bool(obj.get("completed", False)),
            })

        return normalized

    def _normalize_rewards(self, rewards: Any) -> dict[str, Any] | None:
        """规范化奖励数据。"""
        if not isinstance(rewards, dict):
            return None

        normalized = {}
        if "experience" in rewards:
            normalized["experience"] = int(rewards["experience"]) if rewards["experience"] else 0
        if "gold" in rewards:
            normalized["gold"] = int(rewards["gold"]) if rewards["gold"] else 0
        if "reputation" in rewards:
            normalized["reputation"] = rewards["reputation"]
        if "items" in rewards:
            normalized["items"] = rewards["items"]

        return normalized if normalized else None

    def _normalize_failure_condition(self, failure_condition: Any) -> dict[str, Any] | None:
        """规范化失败条件。"""
        if not isinstance(failure_condition, dict):
            return None

        fc_type = failure_condition.get("type")
        if fc_type == "time_limit":
            minutes = failure_condition.get("minutes", 0)
            if minutes > 0:
                return {"type": "time_limit", "minutes": int(minutes)}

        return None


quest_data_adapter = QuestDataAdapter()