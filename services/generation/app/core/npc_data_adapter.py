"""NPC 数据转换适配器模块。

将 AI 生成的 NPC 数据转换为 world-service 兼容的格式。
"""

import uuid
from typing import Any



class NPCDataAdapter:
    """NPC 数据转换适配器。"""

    REQUIRED_FIELDS = [
        "npc_key",
        "name",
        "title",
        "gender",
        "age",
        "race",
        "faction_key",
        "region_key",
        "role",
        "location_key",
        "description",
        "personality",
        "traits",
        "voice",
        "backstory",
        "motivation",
        "relationship_map",
        "dialog_style",
        "dialog_nodes",
        "quests_given",
        "quests_related",
        "shop_items",
        "services_offered",
        "location_x",
        "location_y",
        "interaction_radius",
    ]

    def __init__(self, chapter_id: str = "chapter_01"):
        self.chapter_id = chapter_id

    def adapt(self, raw_npc_data: dict[str, Any]) -> dict[str, Any]:
        """将原始 NPC 数据转换为 world-service 兼容格式。

        Args:
            raw_npc_data: AI 生成的原始 NPC 数据

        Returns:
            转换后的 NPC 数据，符合 world-service NPC 模型
        """
        adapted: dict[str, Any] = {}

        adapted["npc_key"] = self._normalize_npc_key(raw_npc_data.get("npc_key"))
        adapted["chapter_id"] = self.chapter_id
        adapted["name"] = raw_npc_data.get("name", "")
        adapted["title"] = raw_npc_data.get("title") or None
        adapted["faction_key"] = self._normalize_faction_key(raw_npc_data.get("faction_key"))
        adapted["role"] = raw_npc_data.get("role") or None
        adapted["location_key"] = raw_npc_data.get("location_key") or None
        adapted["description"] = raw_npc_data.get("description") or None
        adapted["personality"] = self._normalize_personality(raw_npc_data.get("personality")) or None
        adapted["dialogues"] = self._convert_dialog_nodes(raw_npc_data.get("dialog_nodes")) or None
        adapted["related_quests"] = self._normalize_quests(raw_npc_data.get("quests_given")) or None
        adapted["rewards"] = self._normalize_rewards(raw_npc_data.get("rewards"))

        return adapted

    def validate_completeness(self, npc_data: dict[str, Any]) -> tuple[float, list[str]]:
        """验证 NPC 数据字段完整度。

        Args:
            npc_data: NPC 数据

        Returns:
            (完整度百分比, 缺失字段列表)
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            value = npc_data.get(field)
            if value is None:
                missing.append(field)
            elif isinstance(value, str) and not value.strip():
                missing.append(field)

        total = len(self.REQUIRED_FIELDS)
        present = total - len(missing)
        completeness = present / total

        return completeness, missing

    def ensure_minimum_completeness(
        self, npc_data: dict[str, Any], min_completeness: float = 0.95
    ) -> dict[str, Any]:
        """确保 NPC 数据达到最小完整度要求。

        Args:
            npc_data: NPC 数据
            min_completeness: 最小完整度要求（默认 0.95）

        Returns:
            填充默认值后的 NPC 数据

        Raises:
            ValueError: 完整度低于最小值
        """
        completeness, missing = self.validate_completeness(npc_data)
        if completeness < min_completeness:
            raise ValueError(
                f"NPC data completeness {completeness:.2%} below required {min_completeness:.2%}. "
                f"Missing fields: {', '.join(missing)}"
            )

        return self._fill_defaults(npc_data)

    def _fill_defaults(self, npc_data: dict[str, Any]) -> dict[str, Any]:
        """填充缺失字段的默认值。"""
        defaults = {
            "npc_key": f"npc_{uuid.uuid4().hex[:8]}",
            "name": "Unknown NPC",
            "title": "",
            "gender": "unknown",
            "age": 30,
            "race": "human",
            "faction_key": "",
            "region_key": "region_unknown",
            "role": "commoner",
            "location_key": "loc_unknown",
            "description": "A mysterious figure.",
            "personality": ["mysterious"],
            "traits": [],
            "voice": "neutral",
            "backstory": "Unknown background.",
            "motivation": "Unknown motivation.",
            "relationship_map": {},
            "dialog_style": "neutral",
            "dialog_nodes": {},
            "quests_given": [],
            "quests_related": [],
            "shop_items": [],
            "services_offered": [],
            "location_x": 0,
            "location_y": 0,
            "interaction_radius": 30,
        }

        for key, default in defaults.items():
            if npc_data.get(key) is None:
                npc_data[key] = default
            elif isinstance(npc_data[key], str) and not npc_data[key].strip():
                npc_data[key] = default
            elif isinstance(npc_data[key], (list, dict)) and len(npc_data[key]) == 0:
                npc_data[key] = default

        return npc_data

    def _normalize_npc_key(self, npc_key: str | None) -> str:
        """规范化 NPC key。"""
        if not npc_key:
            return f"npc_{uuid.uuid4().hex[:8]}"
        if not npc_key.startswith("npc_"):
            return f"npc_{npc_key}"
        return npc_key

    def _normalize_faction_key(self, faction_key: str | None) -> str | None:
        """规范化阵营 key。"""
        if not faction_key:
            return None
        if not faction_key.startswith("faction_"):
            return f"faction_{faction_key}"
        return faction_key

    def _normalize_personality(self, personality: Any) -> list[str]:
        """规范化性格特征。"""
        if isinstance(personality, list):
            return [str(p) for p in personality]
        if isinstance(personality, str):
            return [personality]
        return []

    def _normalize_quests(self, quests: Any) -> list[str]:
        """规范化任务列表。"""
        if isinstance(quests, list):
            return [str(q) for q in quests]
        return []

    def _normalize_rewards(self, rewards: Any) -> dict[str, Any] | None:
        """规范化奖励数据。"""
        if isinstance(rewards, dict):
            return rewards
        return None

    def _convert_dialog_nodes(self, dialog_nodes: Any) -> list[dict[str, Any]]:
        """将对话树节点转换为 world-service 格式。"""
        if not isinstance(dialog_nodes, dict):
            return []

        dialogues = []
        for node_id, node_data in dialog_nodes.items():
            if not isinstance(node_data, dict):
                continue
            condition = self._infer_condition(node_id)
            text = node_data.get("text", "")
            if text:
                dialogues.append({
                    "id": f"dia_{node_id}",
                    "text": text,
                    "condition": condition,
                })

        return dialogues

    def _infer_condition(self, node_id: str) -> str:
        """根据节点 ID 推断对话条件。"""
        condition_map = {
            "first_meet": "first_meet",
            "about_self": "talk_about_self",
            "about_work": "talk_about_work",
            "about_trade": "talk_about_trade",
            "about_research": "talk_about_research",
            "has_quest": "has_quest",
            "quest_accepted": "quest_accepted",
            "quest_completed": "quest_completed",
            "default": "default",
            "goodbye": "goodbye",
        }
        return condition_map.get(node_id, "default")


npc_data_adapter = NPCDataAdapter()