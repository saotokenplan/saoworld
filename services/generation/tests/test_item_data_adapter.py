"""装备数据适配器测试。"""

import pytest

from app.core.item_data_adapter import ItemDataAdapter


@pytest.fixture
def adapter() -> ItemDataAdapter:
    return ItemDataAdapter(chapter_id="chapter_01")


class TestItemDataAdapter:
    """ItemDataAdapter 测试类。"""

    def test_adapt_complete_data(self, adapter: ItemDataAdapter) -> None:
        """测试完整数据的适配。"""
        raw_data = {
            "item_key": "sword_steel",
            "item_type": "weapon",
            "item_slot": "weapon",
            "name": "钢铁长剑",
            "description": "一把普通的钢铁长剑，适合新手使用。",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "stats": {"attack": 10, "speed": 5},
            "effects": {"effect_type": "passive", "description": "普通攻击"},
            "sell_price": 50,
            "stackable": False,
        }

        result = adapter.adapt(raw_data)

        assert result["item_key"] == "item_sword_steel"
        assert result["item_type"] == "weapon"
        assert result["item_slot"] == "weapon"
        assert result["name"] == "钢铁长剑"
        assert result["description"] == "一把普通的钢铁长剑，适合新手使用。"
        assert result["rarity"] == "common"
        assert result["chapter_id"] == "chapter_01"
        assert result["level_requirement"] == 1
        assert result["stats_jsonb"] == {"attack": 10, "speed": 5}
        assert result["effects_jsonb"] == {"effect_type": "passive", "description": "普通攻击"}
        assert result["sell_price"] == 50
        assert result["stackable"] is False

    def test_adapt_missing_fields(self, adapter: ItemDataAdapter) -> None:
        """测试缺失字段时使用默认值。"""
        raw_data = {
            "name": "神秘物品",
        }

        result = adapter.adapt(raw_data)

        assert result["item_key"].startswith("item_")
        assert result["name"] == "神秘物品"
        assert result["item_type"] == "weapon"
        assert result["chapter_id"] == "chapter_01"
        assert result["level_requirement"] == 1
        assert result["sell_price"] == 0
        assert result["stackable"] is False

    def test_adapt_normalizes_item_key(self, adapter: ItemDataAdapter) -> None:
        """测试装备 key 规范化（添加 item_ 前缀）。"""
        result = adapter.adapt({"item_key": "armor_leather", "name": "Leather Armor"})
        assert result["item_key"] == "item_armor_leather"

    def test_adapt_valid_item_types(self, adapter: ItemDataAdapter) -> None:
        """测试所有合法装备类型。"""
        for item_type in ["weapon", "armor", "accessory", "consumable", "material"]:
            result = adapter.adapt({"item_type": item_type, "name": "Test"})
            assert result["item_type"] == item_type

    def test_adapt_invalid_item_type_defaults_to_weapon(self, adapter: ItemDataAdapter) -> None:
        """测试无效装备类型默认为 weapon。"""
        result = adapter.adapt({"item_type": "invalid_type", "name": "Test"})
        assert result["item_type"] == "weapon"

    def test_adapt_valid_item_slots(self, adapter: ItemDataAdapter) -> None:
        """测试所有合法装备槽位。"""
        valid_slots = ["head", "chest", "legs", "feet", "weapon", "off_hand", "ring", "necklace"]
        for slot in valid_slots:
            result = adapter.adapt({"item_type": "armor", "item_slot": slot, "name": "Test"})
            assert result["item_slot"] == slot

    def test_adapt_slot_based_on_type(self, adapter: ItemDataAdapter) -> None:
        """测试根据装备类型自动选择槽位。"""
        result = adapter.adapt({"item_type": "weapon", "name": "Test"})
        assert result["item_slot"] == "weapon"

        result = adapter.adapt({"item_type": "armor", "name": "Test"})
        assert result["item_slot"] == "head"

        result = adapter.adapt({"item_type": "consumable", "name": "Test"})
        assert result["item_slot"] is None

        result = adapter.adapt({"item_type": "material", "name": "Test"})
        assert result["item_slot"] is None

    def test_adapt_valid_rarities(self, adapter: ItemDataAdapter) -> None:
        """测试所有合法稀有度。"""
        for rarity in ["common", "uncommon", "rare", "epic", "legendary"]:
            result = adapter.adapt({"rarity": rarity, "name": "Test"})
            assert result["rarity"] == rarity

    def test_adapt_invalid_rarity_defaults_to_common(self, adapter: ItemDataAdapter) -> None:
        """测试无效稀有度默认为 common。"""
        result = adapter.adapt({"rarity": "invalid", "name": "Test"})
        assert result["rarity"] == "common"

    def test_adapt_normalizes_level_requirement(self, adapter: ItemDataAdapter) -> None:
        """测试等级要求规范化（范围限制 1-60）。"""
        result = adapter.adapt({"level_requirement": -1, "name": "Test"})
        assert result["level_requirement"] == 1

        result = adapter.adapt({"level_requirement": 100, "name": "Test"})
        assert result["level_requirement"] == 60

    def test_adapt_normalizes_sell_price(self, adapter: ItemDataAdapter) -> None:
        """测试售卖价格规范化（非负）。"""
        result = adapter.adapt({"sell_price": -10, "name": "Test"})
        assert result["sell_price"] == 0

    def test_adapt_stackable_consumable_material(self, adapter: ItemDataAdapter) -> None:
        """测试消耗品和材料默认可堆叠。"""
        result = adapter.adapt({"item_type": "consumable", "name": "Potion", "stackable": False})
        assert result["stackable"] is True

        result = adapter.adapt({"item_type": "material", "name": "Iron Ore", "stackable": False})
        assert result["stackable"] is True

    def test_adapt_stackable_weapon_armor_accessory(self, adapter: ItemDataAdapter) -> None:
        """测试武器、护甲、饰品默认不可堆叠。"""
        result = adapter.adapt({"item_type": "weapon", "name": "Sword", "stackable": True})
        assert result["stackable"] is False

        result = adapter.adapt({"item_type": "armor", "name": "Armor", "stackable": True})
        assert result["stackable"] is False

        result = adapter.adapt({"item_type": "accessory", "name": "Ring", "stackable": True})
        assert result["stackable"] is False

    def test_adapt_normalizes_stats(self, adapter: ItemDataAdapter) -> None:
        """测试属性数据规范化。"""
        result = adapter.adapt({"stats": {"attack": 10}, "name": "Test"})
        assert result["stats_jsonb"] == {"attack": 10}

        result = adapter.adapt({"stats": "invalid", "name": "Test"})
        assert result["stats_jsonb"] is None

    def test_adapt_normalizes_effects(self, adapter: ItemDataAdapter) -> None:
        """测试效果数据规范化。"""
        result = adapter.adapt({"effects": {"effect_type": "buff"}, "name": "Test"})
        assert result["effects_jsonb"] == {"effect_type": "buff"}

        result = adapter.adapt({"effects": "invalid", "name": "Test"})
        assert result["effects_jsonb"] is None

    def test_validate_completeness_full_data(self, adapter: ItemDataAdapter) -> None:
        """测试完整数据的完整度验证。"""
        raw_data = {
            "item_key": "item_test",
            "item_type": "weapon",
            "name": "Test Item",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "sell_price": 10,
            "stackable": False,
        }

        completeness, missing = adapter.validate_completeness(raw_data)

        assert completeness == 1.0
        assert len(missing) == 0

    def test_validate_completeness_missing_fields(self, adapter: ItemDataAdapter) -> None:
        """测试缺失字段的完整度验证。"""
        raw_data = {"name": "Test"}

        completeness, missing = adapter.validate_completeness(raw_data)

        assert completeness < 1.0
        assert len(missing) > 0
        assert "item_key" in missing
        assert "item_type" in missing

    def test_ensure_minimum_completeness_passes(self, adapter: ItemDataAdapter) -> None:
        """测试达到最小完整度要求时通过。"""
        raw_data = {
            "item_key": "item_test",
            "item_type": "weapon",
            "name": "Test Item",
            "rarity": "common",
            "chapter_id": "chapter_01",
            "level_requirement": 1,
            "sell_price": 10,
            "stackable": False,
        }

        result = adapter.ensure_minimum_completeness(raw_data)

        assert result["item_key"] == "item_test"

    def test_ensure_minimum_completeness_fails(self, adapter: ItemDataAdapter) -> None:
        """测试低于最小完整度要求时抛出异常。"""
        raw_data = {"name": "Test"}

        with pytest.raises(ValueError, match="completeness"):
            adapter.ensure_minimum_completeness(raw_data)