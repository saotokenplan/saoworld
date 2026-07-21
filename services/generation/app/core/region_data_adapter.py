import uuid
from typing import Any


class RegionDataAdapter:
    """区域场景描述数据转换适配器。

    将 AI 生成的区域场景描述数据转换为 world-service 兼容的格式。
    """

    REQUIRED_FIELDS = [
        "region_key",
        "name",
        "chapter_id",
        "region_type",
        "description",
        "danger_level",
        "recommended_level",
    ]

    VALID_REGION_TYPES = ["core", "expansion", "anomaly", "hidden"]

    VALID_TERRAIN_TYPES = [
        "plains",
        "forest",
        "mountain",
        "desert",
        "swamp",
        "cave",
        "city",
        "wasteland",
        "volcanic",
        "ocean",
        "lake",
        "river",
        "glacier",
        "jungle",
    ]

    VALID_LANDMARK_TYPES = ["natural", "manmade", "ruin", "mystical"]

    VALID_DANGER_LEVELS = ["peaceful", "low", "medium", "high", "extreme"]

    VALID_LIGHTING_TYPES = ["day", "night", "dark", "foggy", "sunny"]

    VALID_ARCHITECTURAL_STYLES = ["medieval", "futuristic", "ruined", "natural", "organic"]

    def __init__(self, chapter_id: str = "chapter_01"):
        self.chapter_id = chapter_id

    def adapt(self, raw_region_data: dict[str, Any]) -> dict[str, Any]:
        """将原始区域场景描述数据转换为 world-service 兼容格式。

        Args:
            raw_region_data: AI 生成的原始区域数据

        Returns:
            转换后的区域数据，符合 world-service RegionDefinition 模型
        """
        adapted: dict[str, Any] = {}

        adapted["region_key"] = self._normalize_region_key(raw_region_data.get("region_key"))
        adapted["name"] = raw_region_data.get("name", "")
        adapted["chapter_id"] = raw_region_data.get("chapter_id", self.chapter_id)
        adapted["region_type"] = self._normalize_region_type(raw_region_data.get("region_type"))
        adapted["parent_region"] = self._normalize_parent_region(raw_region_data.get("parent_region"))
        adapted["description"] = raw_region_data.get("description") or None
        adapted["lore"] = raw_region_data.get("lore") or None
        adapted["atmosphere"] = raw_region_data.get("atmosphere") or None
        adapted["visual_style"] = self._normalize_visual_style(raw_region_data.get("visual_style"))
        adapted["landmarks"] = self._normalize_landmarks(raw_region_data.get("landmarks"))
        adapted["danger_level"] = self._normalize_danger_level(raw_region_data.get("danger_level"))
        adapted["recommended_level"] = self._normalize_recommended_level(
            raw_region_data.get("recommended_level")
        )
        adapted["accessibility"] = raw_region_data.get("accessibility") or None
        adapted["climate"] = raw_region_data.get("climate") or None
        adapted["notable_locations"] = self._normalize_notable_locations(
            raw_region_data.get("notable_locations")
        )

        return adapted

    def validate_completeness(self, region_data: dict[str, Any]) -> tuple[float, list[str]]:
        """验证区域数据字段完整度。

        Args:
            region_data: 区域数据

        Returns:
            (完整度百分比, 缺失字段列表)
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            value = region_data.get(field)
            if value is None:
                missing.append(field)
            elif isinstance(value, str) and not value.strip():
                missing.append(field)

        total = len(self.REQUIRED_FIELDS)
        present = total - len(missing)
        completeness = present / total

        return completeness, missing

    def ensure_minimum_completeness(
        self, region_data: dict[str, Any], min_completeness: float = 0.90
    ) -> dict[str, Any]:
        """确保区域数据达到最小完整度要求。

        Args:
            region_data: 区域数据
            min_completeness: 最小完整度要求（默认 0.90）

        Returns:
            填充默认值后的区域数据

        Raises:
            ValueError: 完整度低于最小值
        """
        completeness, missing = self.validate_completeness(region_data)
        if completeness < min_completeness:
            raise ValueError(
                f"Region data completeness {completeness:.2%} below required {min_completeness:.2%}. "
                f"Missing fields: {', '.join(missing)}"
            )

        return self._fill_defaults(region_data)

    def _fill_defaults(self, region_data: dict[str, Any]) -> dict[str, Any]:
        """填充缺失字段的默认值。"""
        defaults: dict[str, Any] = {
            "region_key": f"region_{uuid.uuid4().hex[:8]}",
            "name": "Unknown Region",
            "chapter_id": self.chapter_id,
            "region_type": "expansion",
            "parent_region": None,
            "description": "A mysterious region.",
            "lore": "Little is known about this place.",
            "atmosphere": "Unknown atmosphere.",
            "visual_style": {
                "terrain_type": "plains",
                "color_palette": ["gray", "brown", "green"],
                "lighting": "day",
                "architectural_style": "natural",
            },
            "landmarks": [],
            "danger_level": "medium",
            "recommended_level": "1-10",
            "accessibility": "Accessible from adjacent regions.",
            "climate": "Temperate climate.",
            "notable_locations": [],
        }

        for key, default in defaults.items():
            value = region_data.get(key)
            if value is None:
                region_data[key] = default
            elif isinstance(value, str) and not value.strip():
                region_data[key] = default

        return region_data

    def _normalize_region_key(self, region_key: str | None) -> str:
        """规范化区域 key。"""
        if not region_key:
            return f"region_{uuid.uuid4().hex[:8]}"
        if not region_key.startswith("region_"):
            return f"region_{region_key}"
        return region_key

    def _normalize_region_type(self, region_type: str | None) -> str:
        """规范化区域类型。"""
        if not region_type:
            return "expansion"
        if region_type.lower() in self.VALID_REGION_TYPES:
            return region_type.lower()
        return "expansion"

    def _normalize_parent_region(self, parent_region: str | None) -> str | None:
        """规范化父区域。"""
        if parent_region is None:
            return None
        if not parent_region.startswith("region_"):
            return f"region_{parent_region}"
        return parent_region

    def _normalize_danger_level(self, danger_level: str | None) -> str:
        """规范化危险等级。"""
        if not danger_level:
            return "medium"
        if danger_level.lower() in self.VALID_DANGER_LEVELS:
            return danger_level.lower()
        return "medium"

    def _normalize_recommended_level(self, recommended_level: str | None) -> str:
        """规范化推荐等级范围。"""
        if not recommended_level:
            return "1-10"
        return str(recommended_level).strip()

    def _normalize_visual_style(self, visual_style: Any) -> dict[str, Any] | None:
        """规范化视觉风格数据。"""
        if not isinstance(visual_style, dict):
            return {
                "terrain_type": "plains",
                "color_palette": ["gray", "brown", "green"],
                "lighting": "day",
                "architectural_style": "natural",
            }

        result: dict[str, Any] = {}
        result["terrain_type"] = self._normalize_terrain_type(visual_style.get("terrain_type"))
        result["color_palette"] = self._normalize_color_palette(visual_style.get("color_palette"))
        result["lighting"] = self._normalize_lighting(visual_style.get("lighting"))
        result["architectural_style"] = self._normalize_architectural_style(
            visual_style.get("architectural_style")
        )

        return result

    def _normalize_terrain_type(self, terrain_type: str | None) -> str:
        """规范化地形类型。"""
        if not terrain_type:
            return "plains"
        if terrain_type.lower() in self.VALID_TERRAIN_TYPES:
            return terrain_type.lower()
        return "plains"

    def _normalize_color_palette(self, color_palette: Any) -> list[str]:
        """规范化主色调数组。"""
        if isinstance(color_palette, list):
            return [str(c).strip() for c in color_palette if c]
        return ["gray", "brown", "green"]

    def _normalize_lighting(self, lighting: str | None) -> str:
        """规范化光照描述。"""
        if not lighting:
            return "day"
        if lighting.lower() in self.VALID_LIGHTING_TYPES:
            return lighting.lower()
        return "day"

    def _normalize_architectural_style(self, architectural_style: str | None) -> str:
        """规范化建筑风格。"""
        if not architectural_style:
            return "natural"
        if architectural_style.lower() in self.VALID_ARCHITECTURAL_STYLES:
            return architectural_style.lower()
        return "natural"

    def _normalize_landmarks(self, landmarks: Any) -> list[dict[str, Any]]:
        """规范化地标数组。"""
        if not isinstance(landmarks, list):
            return []

        result = []
        for landmark in landmarks:
            if not isinstance(landmark, dict):
                continue

            normalized = {}
            normalized["landmark_key"] = self._normalize_landmark_key(landmark.get("landmark_key"))
            normalized["name"] = landmark.get("name", "")
            normalized["description"] = landmark.get("description") or ""
            normalized["type"] = self._normalize_landmark_type(landmark.get("type"))
            normalized["significance"] = landmark.get("significance") or ""

            result.append(normalized)

        return result

    def _normalize_landmark_key(self, landmark_key: str | None) -> str:
        """规范化地标 key。"""
        if not landmark_key:
            return f"landmark_{uuid.uuid4().hex[:8]}"
        if not landmark_key.startswith("landmark_"):
            return f"landmark_{landmark_key}"
        return landmark_key

    def _normalize_landmark_type(self, landmark_type: str | None) -> str:
        """规范化地标类型。"""
        if not landmark_type:
            return "natural"
        if landmark_type.lower() in self.VALID_LANDMARK_TYPES:
            return landmark_type.lower()
        return "natural"

    def _normalize_notable_locations(self, notable_locations: Any) -> list[str]:
        """规范化著名地点数组。"""
        if isinstance(notable_locations, list):
            return [str(loc).strip() for loc in notable_locations if loc]
        return []


region_data_adapter = RegionDataAdapter()