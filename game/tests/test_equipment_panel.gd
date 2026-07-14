extends "res://addons/gut/test.gd"

var _equipment_panel: Control

func before_each() -> void:
	_equipment_panel = load("res://scripts/ui/inventory/equipment_panel.gd").new()
	add_child_autofree(_equipment_panel)

func after_each() -> void:
	pass

func test_signal_declarations() -> void:
	assert_true(_equipment_panel.has_signal("back_pressed"), "应声明 back_pressed 信号")
	assert_true(_equipment_panel.has_signal("equip_item"), "应声明 equip_item 信号")
	assert_true(_equipment_panel.has_signal("unequip_item"), "应声明 unequip_item 信号")

func test_initial_state() -> void:
	assert_eq(_equipment_panel.get_equipment().size(), 0, "初始装备列表应为空")
	assert_true(_equipment_panel.get_stats().is_empty(), "初始属性应为空")

func test_get_equipment() -> void:
	var test_equipment: Array[Dictionary] = [
		{"slot": "weapon", "item_key": "item_iron_sword_01", "item_name": "铁剑"},
		{"slot": "armor", "item_key": "item_leather_armor_01", "item_name": "皮甲"},
	]
	
	var test_stats: Dictionary = {"attack": 15, "defense": 8}
	
	_equipment_panel._on_equipment_updated(test_equipment, test_stats)
	
	var equipment: Array[Dictionary] = _equipment_panel.get_equipment()
	assert_eq(equipment.size(), 2, "装备列表应有2个装备")
	assert_eq(equipment[0].get("slot", ""), "weapon", "第一个装备槽位应为weapon")
	assert_eq(equipment[1].get("slot", ""), "armor", "第二个装备槽位应为armor")

func test_get_stats() -> void:
	var test_stats: Dictionary = {"attack": 15, "defense": 8, "health": 50}
	
	_equipment_panel._on_equipment_updated([], test_stats)
	
	var stats: Dictionary = _equipment_panel.get_stats()
	assert_eq(stats.get("attack", 0), 15, "攻击力应为15")
	assert_eq(stats.get("defense", 0), 8, "防御力应为8")
	assert_eq(stats.get("health", 0), 50, "生命值应为50")

func test_empty_equipment_display() -> void:
	var test_equipment: Array[Dictionary] = []
	var test_stats: Dictionary = {}
	
	_equipment_panel._on_equipment_updated(test_equipment, test_stats)
	
	var empty_label: Label = _equipment_panel.get_node_or_null("EmptyLabel")
	assert_true(empty_label.visible, "空状态时空标签应可见")

func test_slot_names_constant() -> void:
	assert_true(_equipment_panel.has("SLOT_NAMES"), "应定义 SLOT_NAMES 常量")
	var slot_names: Dictionary = _equipment_panel.SLOT_NAMES
	assert_eq(slot_names.get("helmet", ""), "头盔", "头盔名称映射正确")
	assert_eq(slot_names.get("armor", ""), "护甲", "护甲名称映射正确")
	assert_eq(slot_names.get("weapon", ""), "武器", "武器名称映射正确")
	assert_eq(slot_names.get("accessory", ""), "饰品", "饰品名称映射正确")