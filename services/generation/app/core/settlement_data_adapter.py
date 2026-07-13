"""聚落数据转换适配器模块。

将 AI 生成的聚落数据转换为 world-service 兼容的格式。
"""

import uuid
from typing import Any


class SettlementDataAdapter:
    """聚落数据转换适配器。"""

    REQUIRED_FIELDS = [
        "settlement_key",
        "name",
        "settlement_type",
        "region_key",
        "chapter_id",
        "description",
        "population",
        "main_resources",
        "economy_type",
        "status",
    ]

    VALID_SETTLEMENT_TYPES = {"village", "town", "city", "camp", "fortress", "market", "outpost"}

    VALID_ECONOMY_TYPES = {"agriculture", "commerce", "mining", "hunting", "fishing", "trade"}

    VALID_STATUSES = {"peaceful", "troubled", "warring", "thriving"}

    def __init__(self, chapter_id: str = "chapter_01"):
        self.chapter_id = chapter_id

    def adapt(self, raw_settlement_data: dict[str, Any]) -> dict[str, Any]:
        """将原始聚落数据转换为 world-service 兼容格式。

        Args:
            raw_settlement_data: AI 生成的原始聚落数据

        Returns:
            转换后的聚落数据，符合 world-service 聚落模型
        """
        adapted: dict[str, Any] = {}

        adapted["settlement_key"] = self._normalize_settlement_key(raw_settlement_data.get("settlement_key"))
        adapted["name"] = raw_settlement_data.get("name", "")
        adapted["settlement_type"] = self._normalize_settlement_type(raw_settlement_data.get("settlement_type"))
        adapted["region_key"] = self._normalize_region_key(raw_settlement_data.get("region_key"))
        adapted["chapter_id"] = raw_settlement_data.get("chapter_id") or self.chapter_id
        adapted["faction_key"] = self._normalize_faction_key(raw_settlement_data.get("faction_key"))
        adapted["description"] = raw_settlement_data.get("description") or None
        adapted["population"] = self._normalize_population(raw_settlement_data.get("population"))
        adapted["main_resources"] = self._normalize_resources(raw_settlement_data.get("main_resources"))
        adapted["economy_type"] = self._normalize_economy_type(raw_settlement_data.get("economy_type"))
        adapted["status"] = self._normalize_status(raw_settlement_data.get("status"))
        adapted["notable_locations"] = self._normalize_locations(raw_settlement_data.get("notable_locations"))
        adapted["key_npcs"] = self._normalize_npc_keys(raw_settlement_data.get("key_npcs"))
        adapted["faction_influence"] = self._normalize_faction_influence(raw_settlement_data.get("faction_influence"))
        adapted["relationships"] = self._normalize_relationships(raw_settlement_data.get("relationships"))
        adapted["history"] = raw_settlement_data.get("history") or None
        adapted["culture"] = raw_settlement_data.get("culture") or None
        adapted["defenses"] = self._normalize_defenses(raw_settlement_data.get("defenses"))
        adapted["services"] = self._normalize_services(raw_settlement_data.get("services"))
        adapted["special_features"] = self._normalize_features(raw_settlement_data.get("special_features"))
        adapted["location_x"] = self._normalize_location(raw_settlement_data.get("location_x"))
        adapted["location_y"] = self._normalize_location(raw_settlement_data.get("location_y"))

        return adapted

    def validate_completeness(self, settlement_data: dict[str, Any]) -> tuple[float, list[str]]:
        """验证聚落数据字段完整度。

        Args:
            settlement_data: 聚落数据

        Returns:
            (完整度百分比, 缺失字段列表)
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            value = settlement_data.get(field)
            if value is None:
                missing.append(field)
            elif isinstance(value, str) and not value.strip():
                missing.append(field)
            elif isinstance(value, list) and len(value) == 0:
                missing.append(field)
            elif isinstance(value, int) and value <= 0:
                missing.append(field)

        total = len(self.REQUIRED_FIELDS)
        present = total - len(missing)
        completeness = present / total

        return completeness, missing

    def ensure_minimum_completeness(
        self, settlement_data: dict[str, Any], min_completeness: float = 0.90
    ) -> dict[str, Any]:
        """确保聚落数据达到最小完整度要求。

        Args:
            settlement_data: 聚落数据
            min_completeness: 最小完整度要求（默认 0.90）

        Returns:
            填充默认值后的聚落数据

        Raises:
            ValueError: 完整度低于最小值
        """
        completeness, missing = self.validate_completeness(settlement_data)
        if completeness < min_completeness:
            raise ValueError(
                f"Settlement data completeness {completeness:.2%} below required {min_completeness:.2%}. "
                f"Missing fields: {', '.join(missing)}"
            )

        return self._fill_defaults(settlement_data)

    def _fill_defaults(self, settlement_data: dict[str, Any]) -> dict[str, Any]:
        """填充缺失字段的默认值。"""
        defaults = {
            "settlement_key": f"settlement_{uuid.uuid4().hex[:8]}",
            "name": "Unknown Settlement",
            "settlement_type": "village",
            "region_key": "region_unknown",
            "chapter_id": self.chapter_id,
            "faction_key": "",
            "description": "A mysterious settlement.",
            "population": 50,
            "main_resources": ["basic"],
            "economy_type": "agriculture",
            "status": "peaceful",
            "notable_locations": [],
            "key_npcs": [],
            "faction_influence": {},
            "relationships": {},
            "history": "Unknown history.",
            "culture": "Unknown culture.",
            "defenses": [],
            "services": [],
            "special_features": [],
            "location_x": 0,
            "location_y": 0,
        }

        for key, default in defaults.items():
            if settlement_data.get(key) is None:
                settlement_data[key] = default
            elif isinstance(settlement_data[key], str) and not settlement_data[key].strip():
                settlement_data[key] = default
            elif isinstance(settlement_data[key], (list, dict)) and len(settlement_data[key]) == 0:
                settlement_data[key] = default
            elif isinstance(settlement_data[key], int) and settlement_data[key] <= 0:
                settlement_data[key] = default

        return settlement_data

    def _normalize_settlement_key(self, settlement_key: str | None) -> str:
        """规范化聚落 key。"""
        if not settlement_key:
            return f"settlement_{uuid.uuid4().hex[:8]}"
        if not settlement_key.startswith("settlement_"):
            return f"settlement_{settlement_key}"
        return settlement_key

    def _normalize_settlement_type(self, settlement_type: str | None) -> str:
        """规范化聚落类型。"""
        if not settlement_type:
            return "village"
        settlement_type = settlement_type.lower()
        if settlement_type in self.VALID_SETTLEMENT_TYPES:
            return settlement_type
        return "village"

    def _normalize_region_key(self, region_key: str | None) -> str | None:
        """规范化区域 key。"""
        if not region_key:
            return None
        if not region_key.startswith("region_"):
            return f"region_{region_key}"
        return region_key

    def _normalize_faction_key(self, faction_key: str | None) -> str | None:
        """规范化阵营 key。"""
        if not faction_key:
            return None
        if not faction_key.startswith("faction_"):
            return f"faction_{faction_key}"
        return faction_key

    def _normalize_population(self, population: Any) -> int:
        """规范化人口数量。"""
        if isinstance(population, int):
            return max(1, population)
        if isinstance(population, str):
            try:
                return max(1, int(population))
            except ValueError:
                pass
        return 50

    def _normalize_resources(self, resources: Any) -> list[str]:
        """规范化资源列表。"""
        if isinstance(resources, list):
            return [str(r) for r in resources]
        if isinstance(resources, str):
            return [resources]
        return ["basic"]

    def _normalize_economy_type(self, economy_type: str | None) -> str:
        """规范化经济类型。"""
        if not economy_type:
            return "agriculture"
        economy_type = economy_type.lower()
        if economy_type in self.VALID_ECONOMY_TYPES:
            return economy_type
        return "agriculture"

    def _normalize_status(self, status: str | None) -> str:
        """规范化状态。"""
        if not status:
            return "peaceful"
        status = status.lower()
        if status in self.VALID_STATUSES:
            return status
        return "peaceful"

    def _normalize_locations(self, locations: Any) -> list[dict[str, Any]]:
        """规范化地点列表。"""
        if not isinstance(locations, list):
            return []

        normalized = []
        for idx, loc in enumerate(locations):
            if not isinstance(loc, dict):
                continue

            location_key = loc.get("location_key") or f"loc_settlement_{idx + 1}"
            if not location_key.startswith("loc_"):
                location_key = f"loc_{location_key}"

            normalized.append({
                "location_key": location_key,
                "name": loc.get("name", ""),
                "description": loc.get("description", ""),
            })

        return normalized

    def _normalize_npc_keys(self, npc_keys: Any) -> list[str]:
        """规范化 NPC key 列表。"""
        if isinstance(npc_keys, list):
            normalized = []
            for key in npc_keys:
                key_str = str(key)
                if not key_str.startswith("npc_"):
                    key_str = f"npc_{key_str}"
                normalized.append(key_str)
            return normalized
        return []

    def _normalize_faction_influence(self, faction_influence: Any) -> dict[str, str]:
        """规范化阵营影响力。"""
        if isinstance(faction_influence, dict):
            normalized = {}
            for faction_key, influence in faction_influence.items():
                key_str = str(faction_key)
                if not key_str.startswith("faction_"):
                    key_str = f"faction_{key_str}"
                normalized[key_str] = str(influence)
            return normalized
        return {}

    def _normalize_relationships(self, relationships: Any) -> dict[str, str]:
        """规范化关系描述。"""
        if isinstance(relationships, dict):
            normalized = {}
            for settlement_key, relation in relationships.items():
                key_str = str(settlement_key)
                if not key_str.startswith("settlement_"):
                    key_str = f"settlement_{key_str}"
                normalized[key_str] = str(relation)
            return normalized
        return {}

    def _normalize_defenses(self, defenses: Any) -> list[str]:
        """规范化防御设施列表。"""
        if isinstance(defenses, list):
            return [str(d) for d in defenses]
        return []

    def _normalize_services(self, services: Any) -> list[str]:
        """规范化服务列表。"""
        if isinstance(services, list):
            return [str(s) for s in services]
        return []

    def _normalize_features(self, features: Any) -> list[str]:
        """规范化特色列表。"""
        if isinstance(features, list):
            return [str(f) for f in features]
        return []

    def _normalize_location(self, location: Any) -> float:
        """规范化坐标值。"""
        if isinstance(location, (int, float)):
            return float(location)
        if isinstance(location, str):
            try:
                return float(location)
            except ValueError:
                pass
        return 0.0


settlement_data_adapter = SettlementDataAdapter()
