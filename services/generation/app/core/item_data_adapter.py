import uuid
from typing import Any


class ItemDataAdapter:
    """装备数据转换适配器。

    将 AI 生成的装备数据转换为 world-service 兼容的格式。
    """

    REQUIRED_FIELDS = [
        "item_key",
        "item_type",
        "name",
        "rarity",
        "chapter_id",
        "level_requirement",
        "sell_price",
        "stackable",
    ]

    VALID_ITEM_TYPES = ["weapon", "armor", "accessory", "consumable", "material"]

    VALID_ITEM_SLOTS = ["head", "chest", "legs", "feet", "weapon", "off_hand", "ring", "necklace"]

    VALID_RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]

    TYPE_TO_SLOT_MAP = {
        "weapon": ["weapon"],
        "armor": ["head", "chest", "legs", "feet"],
        "accessory": ["ring", "necklace", "off_hand"],
        "consumable": [],
        "material": [],
    }

    def __init__(self, chapter_id: str = "chapter_01"):
        self.chapter_id = chapter_id

    def adapt(self, raw_item_data: dict[str, Any]) -> dict[str, Any]:
        """将原始装备数据转换为 world-service 兼容格式。

        Args:
            raw_item_data: AI 生成的原始装备数据

        Returns:
            转换后的装备数据，符合 world-service ItemDefinition 模型
        """
        adapted: dict[str, Any] = {}

        adapted["item_key"] = self._normalize_item_key(raw_item_data.get("item_key"))
        adapted["item_type"] = self._normalize_item_type(raw_item_data.get("item_type"))
        adapted["item_slot"] = self._normalize_item_slot(raw_item_data.get("item_slot"), adapted["item_type"])
        adapted["name"] = raw_item_data.get("name", "")
        adapted["description"] = raw_item_data.get("description") or None
        adapted["rarity"] = self._normalize_rarity(raw_item_data.get("rarity"))
        adapted["chapter_id"] = raw_item_data.get("chapter_id", self.chapter_id)
        adapted["level_requirement"] = self._normalize_int(raw_item_data.get("level_requirement"), min_val=1, max_val=60, default=1)
        adapted["stats_jsonb"] = self._normalize_stats(raw_item_data.get("stats"))
        adapted["effects_jsonb"] = self._normalize_effects(raw_item_data.get("effects"))
        adapted["sell_price"] = self._normalize_int(raw_item_data.get("sell_price"), min_val=0, default=0)
        adapted["stackable"] = self._normalize_stackable(raw_item_data.get("stackable"), adapted["item_type"])

        return adapted

    def validate_completeness(self, item_data: dict[str, Any]) -> tuple[float, list[str]]:
        """验证装备数据字段完整度。

        Args:
            item_data: 装备数据

        Returns:
            (完整度百分比, 缺失字段列表)
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            value = item_data.get(field)
            if value is None:
                missing.append(field)
            elif isinstance(value, str) and not value.strip():
                missing.append(field)

        total = len(self.REQUIRED_FIELDS)
        present = total - len(missing)
        completeness = present / total

        return completeness, missing

    def ensure_minimum_completeness(
        self, item_data: dict[str, Any], min_completeness: float = 0.95
    ) -> dict[str, Any]:
        """确保装备数据达到最小完整度要求。

        Args:
            item_data: 装备数据
            min_completeness: 最小完整度要求（默认 0.95）

        Returns:
            填充默认值后的装备数据

        Raises:
            ValueError: 完整度低于最小值
        """
        completeness, missing = self.validate_completeness(item_data)
        if completeness < min_completeness:
            raise ValueError(
                f"Item data completeness {completeness:.2%} below required {min_completeness:.2%}. "
                f"Missing fields: {', '.join(missing)}"
            )

        return self._fill_defaults(item_data)

    def _fill_defaults(self, item_data: dict[str, Any]) -> dict[str, Any]:
        """填充缺失字段的默认值。"""
        defaults = {
            "item_key": f"item_{uuid.uuid4().hex[:8]}",
            "item_type": "weapon",
            "item_slot": None,
            "name": "Unknown Item",
            "description": "A mysterious item.",
            "rarity": "common",
            "chapter_id": self.chapter_id,
            "level_requirement": 1,
            "stats": {},
            "effects": {},
            "sell_price": 0,
            "stackable": False,
        }

        for key, default in defaults.items():
            value = item_data.get(key)
            if value is None:
                item_data[key] = default
            elif isinstance(value, str) and not value.strip():
                item_data[key] = default

        return item_data

    def _normalize_item_key(self, item_key: str | None) -> str:
        """规范化装备 key。"""
        if not item_key:
            return f"item_{uuid.uuid4().hex[:8]}"
        if not item_key.startswith("item_"):
            return f"item_{item_key}"
        return item_key

    def _normalize_item_type(self, item_type: str | None) -> str:
        """规范化装备类型。"""
        if not item_type:
            return "weapon"
        if item_type.lower() in self.VALID_ITEM_TYPES:
            return item_type.lower()
        return "weapon"

    def _normalize_item_slot(self, item_slot: str | None, item_type: str) -> str | None:
        """规范化装备槽位。"""
        if item_slot is None:
            valid_slots = self.TYPE_TO_SLOT_MAP.get(item_type, [])
            return valid_slots[0] if valid_slots else None
        if item_slot.lower() in self.VALID_ITEM_SLOTS:
            return item_slot.lower()
        valid_slots = self.TYPE_TO_SLOT_MAP.get(item_type, [])
        return valid_slots[0] if valid_slots else None

    def _normalize_rarity(self, rarity: str | None) -> str:
        """规范化稀有度。"""
        if not rarity:
            return "common"
        if rarity.lower() in self.VALID_RARITIES:
            return rarity.lower()
        return "common"

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

    def _normalize_stats(self, stats: Any) -> dict[str, Any] | None:
        """规范化属性数据。"""
        if isinstance(stats, dict):
            return stats
        return None

    def _normalize_effects(self, effects: Any) -> dict[str, Any] | None:
        """规范化效果数据。"""
        if isinstance(effects, dict):
            return effects
        return None

    def _normalize_stackable(self, stackable: Any, item_type: str) -> bool:
        """规范化可堆叠属性。"""
        if item_type in ["consumable", "material"]:
            return True
        if item_type in ["weapon", "armor", "accessory"]:
            return False
        if isinstance(stackable, bool):
            return stackable
        if isinstance(stackable, str):
            return stackable.lower() in ["true", "yes", "1"]
        return False


item_data_adapter = ItemDataAdapter()