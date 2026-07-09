extends "res://addons/gut/test.gd"
## InventoryManager 单元测试

var _inv_manager: Node

func before_each() -> void:
	_inv_manager = load("res://scripts/autoload/InventoryManager.gd").new()
	add_child_autofree(_inv_manager)

func after_each() -> void:
	_inv_manager.clear_cache()

func test_initial_state() -> void:
	assert_eq(_inv_manager.get_items().size(), 0, "初始背包应为空")
	assert_false(_inv_manager.is_loading(), "初始不应在加载中")
	assert_eq(_inv_manager.get_last_error(), "", "初始不应有错误")

func test_get_item_empty() -> void:
	var item: Dictionary = _inv_manager.get_item("item_nonexistent")
	assert_true(item.is_empty(), "查询不存在的物品应返回空字典")

func test_get_item_quantity_nonexistent() -> void:
	var qty: int = _inv_manager.get_item_quantity("item_nonexistent")
	assert_eq(qty, 0, "不存在的物品数量应为0")

func test_load_from_cache() -> void:
	var test_items: Array = [
		{"item_key": "item_health_potion_01", "item_type": "consumable", "quantity": 5},
		{"item_key": "item_iron_ore_01", "item_type": "material", "quantity": 10},
	]
	_inv_manager.load_from_cache(test_items)
	
	assert_eq(_inv_manager.get_items().size(), 2, "加载后应有2个物品")
	assert_eq(_inv_manager.get_item_quantity("item_health_potion_01"), 5, "药水数量应为5")
	assert_eq(_inv_manager.get_item_quantity("item_iron_ore_01"), 10, "铁矿石数量应为10")

func test_get_items_by_type() -> void:
	var test_items: Array = [
		{"item_key": "item_health_potion_01", "item_type": "consumable", "quantity": 5},
		{"item_key": "item_iron_ore_01", "item_type": "material", "quantity": 10},
		{"item_key": "item_mana_potion_01", "item_type": "consumable", "quantity": 3},
	]
	_inv_manager.load_from_cache(test_items)
	
	var consumables: Array[Dictionary] = _inv_manager.get_items_by_type("consumable")
	assert_eq(consumables.size(), 2, "消耗品应有2个")
	
	var materials: Array[Dictionary] = _inv_manager.get_items_by_type("material")
	assert_eq(materials.size(), 1, "材料应有1个")

func test_clear_cache() -> void:
	var test_items: Array = [
		{"item_key": "item_test", "item_type": "material", "quantity": 1},
	]
	_inv_manager.load_from_cache(test_items)
	assert_eq(_inv_manager.get_items().size(), 1, "加载后应有1个物品")
	
	_inv_manager.clear_cache()
	assert_eq(_inv_manager.get_items().size(), 0, "清空后应为空")

func test_serialize() -> void:
	var test_items: Array = [
		{"item_key": "item_health_potion_01", "item_type": "consumable", "quantity": 5},
	]
	_inv_manager.load_from_cache(test_items)
	
	var serialized: Array = _inv_manager.serialize()
	assert_eq(serialized.size(), 1, "序列化应包含1个物品")
	assert_eq(serialized[0].get("item_key", ""), "item_health_potion_01", "序列化物品key应正确")

func test_inventory_updated_signal() -> void:
	var signal_received: bool = false
	_inv_manager.inventory_updated.connect(func():
		signal_received = true
	)
	
	var test_items: Array = [
		{"item_key": "item_test", "item_type": "material", "quantity": 1},
	]
	_inv_manager.load_from_cache(test_items)
	assert_true(signal_received, "加载缓存后应发射 inventory_updated 信号")

func test_get_item_by_key() -> void:
	var test_items: Array = [
		{"item_key": "item_health_potion_01", "item_type": "consumable", "quantity": 5},
		{"item_key": "item_iron_sword_01", "item_type": "equipment", "quantity": 1},
	]
	_inv_manager.load_from_cache(test_items)
	
	var item: Dictionary = _inv_manager.get_item("item_iron_sword_01")
	assert_false(item.is_empty(), "应找到铁剑")
	assert_eq(item.get("item_type", ""), "equipment", "物品类型应为装备")
