extends Control
## 背包面板 UI
## 显示玩家背包物品，支持分类过滤和使用消耗品

signal back_pressed

var _current_filter: String = "all"

@onready var _back_button: Button = $BackButton
@onready var _type_filter: OptionButton = $TypeFilter
@onready var _item_list: VBoxContainer = $ItemList
@onready var _empty_label: Label = $EmptyLabel
@onready var _loading_label: Label = $LoadingLabel

func _ready() -> void:
	_back_button.pressed.connect(_on_back_pressed)
	_type_filter.item_selected.connect(_on_filter_changed)
	_setup_filter_options()
	
	var inv_manager: Node = get_node_or_null("/root/InventoryManager")
	if inv_manager != null:
		inv_manager.inventory_updated.connect(_on_inventory_updated)
		inv_manager.inventory_error.connect(_on_inventory_error)
		inv_manager.load_inventory()

func _setup_filter_options() -> void:
	_type_filter.add_item("全部", 0)
	_type_filter.add_item("消耗品", 1)
	_type_filter.add_item("装备", 2)
	_type_filter.add_item("材料", 3)
	_type_filter.add_item("任务物品", 4)

func _on_back_pressed() -> void:
	back_pressed.emit()

func _on_filter_changed(index: int) -> void:
	match index:
		0: _current_filter = "all"
		1: _current_filter = "consumable"
		2: _current_filter = "equipment"
		3: _current_filter = "material"
		4: _current_filter = "quest_item"
	_refresh_display()

func _on_inventory_updated() -> void:
	_refresh_display()

func _on_inventory_error(error_message: String) -> void:
	_loading_label.visible = false
	_empty_label.visible = true
	_empty_label.text = "加载失败: " + error_message

func _refresh_display() -> void:
	# 清空列表
	for child: Node in _item_list.get_children():
		child.queue_free()
	
	var inv_manager: Node = get_node_or_null("/root/InventoryManager")
	if inv_manager == null:
		return
	
	var items: Array[Dictionary] = []
	if _current_filter == "all":
		items = inv_manager.get_items()
	else:
		items = inv_manager.get_items_by_type(_current_filter)
	
	_loading_label.visible = false
	_empty_label.visible = items.is_empty()
	
	for item: Dictionary in items:
		_create_item_row(item)

func _create_item_row(item: Dictionary) -> void:
	var row: HBoxContainer = HBoxContainer.new()
	
	var name_label: Label = Label.new()
	var item_name: String = item.get("metadata_jsonb", {}).get("name", item.get("item_key", "未知"))
	name_label.text = item_name
	name_label.custom_minimum_size.x = 300.0
	row.add_child(name_label)
	
	var type_label: Label = Label.new()
	var type_map: Dictionary = {
		"consumable": "消耗品",
		"equipment": "装备",
		"material": "材料",
		"quest_item": "任务物品",
	}
	type_label.text = type_map.get(item.get("item_type", ""), item.get("item_type", ""))
	type_label.custom_minimum_size.x = 100.0
	row.add_child(type_label)
	
	var qty_label: Label = Label.new()
	qty_label.text = "x" + str(item.get("quantity", 0))
	qty_label.custom_minimum_size.x = 80.0
	row.add_child(qty_label)
	
	if item.get("item_type", "") == "consumable":
		var use_button: Button = Button.new()
		use_button.text = "使用"
		use_button.pressed.connect(_on_use_item.bind(item.get("item_key", "")))
		row.add_child(use_button)
	
	_item_list.add_child(row)

func _on_use_item(item_key: String) -> void:
	var inv_manager: Node = get_node_or_null("/root/InventoryManager")
	if inv_manager != null:
		inv_manager.use_item(item_key, 1)
