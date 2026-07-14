extends Control

signal back_pressed
signal equip_item(slot: String, item_key: String)
signal unequip_item(slot: String)

var _equipment: Array[Dictionary] = []
var _stats: Dictionary = {}

@onready var _back_button: Button = $BackButton
@onready var _equipment_grid: GridContainer = $EquipmentGrid
@onready var _stats_list: VBoxContainer = $StatsPanel/StatsList
@onready var _empty_label: Label = $EmptyLabel
@onready var _loading_label: Label = $LoadingLabel

const SLOT_NAMES: Dictionary = {
	"helmet": "头盔",
	"armor": "护甲",
	"weapon": "武器",
	"accessory": "饰品"
}

func _ready() -> void:
	_back_button.pressed.connect(_on_back_pressed)
	
	var inv_manager: Node = get_node_or_null("/root/InventoryManager")
	if inv_manager != null:
		inv_manager.equipment_updated.connect(_on_equipment_updated)
		inv_manager.equipment_error.connect(_on_equipment_error)
		inv_manager.load_equipment()

func get_equipment() -> Array[Dictionary]:
	return _equipment

func get_stats() -> Dictionary:
	return _stats

func _on_back_pressed() -> void:
	back_pressed.emit()

func _on_equipment_updated(equipment: Array[Dictionary], stats: Dictionary) -> void:
	_equipment = equipment
	_stats = stats
	_refresh_display()

func _on_equipment_error(error_message: String) -> void:
	_loading_label.visible = false
	_empty_label.visible = true
	_empty_label.text = "加载失败: " + error_message

func _refresh_display() -> void:
	for child: Node in _equipment_grid.get_children():
		child.queue_free()
	
	for child: Node in _stats_list.get_children():
		child.queue_free()
	
	_loading_label.visible = false
	
	if _equipment.is_empty():
		_empty_label.visible = true
		return
	
	_empty_label.visible = false
	
	for equipment_item: Dictionary in _equipment:
		_create_equipment_row(equipment_item)
	
	_create_stats_display()

func _create_equipment_row(equipment_item: Dictionary) -> void:
	var row: HBoxContainer = HBoxContainer.new()
	
	var slot_label: Label = Label.new()
	var slot: String = equipment_item.get("slot", "")
	slot_label.text = SLOT_NAMES.get(slot, slot)
	slot_label.custom_minimum_size.x = 120.0
	row.add_child(slot_label)
	
	var item_name_label: Label = Label.new()
	var item_name: String = equipment_item.get("item_name", "")
	if item_name == "" and equipment_item.has("item_key"):
		item_name = equipment_item.get("item_key", "")
	item_name_label.text = item_name if item_name != "" else "空"
	item_name_label.custom_minimum_size.x = 200.0
	row.add_child(item_name_label)
	
	if equipment_item.has("item_key") and equipment_item.get("item_key", "") != "":
		var unequip_button: Button = Button.new()
		unequip_button.text = "卸下"
		unequip_button.pressed.connect(_on_unequip_pressed.bind(slot))
		row.add_child(unequip_button)
	
	_equipment_grid.add_child(row)

func _create_stats_display() -> void:
	var stat_map: Dictionary = {
		"attack": "攻击力",
		"defense": "防御力",
		"health": "生命值",
		"speed": "速度",
		"crit_rate": "暴击率",
		"crit_damage": "暴击伤害"
	}
	
	for stat_key in stat_map:
		if _stats.has(stat_key):
			var stat_row: HBoxContainer = HBoxContainer.new()
			
			var stat_name_label: Label = Label.new()
			stat_name_label.text = stat_map[stat_key] + ":"
			stat_name_label.custom_minimum_size.x = 100.0
			stat_row.add_child(stat_name_label)
			
			var stat_value_label: Label = Label.new()
			stat_value_label.text = str(_stats[stat_key])
			stat_row.add_child(stat_value_label)
			
			_stats_list.add_child(stat_row)
	
	if _stats_list.get_children().is_empty():
		var no_stats_label: Label = Label.new()
		no_stats_label.text = "暂无装备属性加成"
		no_stats_label.horizontal_alignment = 1
		_stats_list.add_child(no_stats_label)

func _on_unequip_pressed(slot: String) -> void:
	var inv_manager: Node = get_node_or_null("/root/InventoryManager")
	if inv_manager != null:
		inv_manager.unequip_item(slot)