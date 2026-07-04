extends Node2D

signal region_selected(region_id: String)
signal back_to_menu()

var regions: Array[Dictionary] = []
var selected_region_id: String = ""

@onready var region_container: HBoxContainer = $RegionContainer
@onready var region_detail: Panel = $RegionDetail
@onready var detail_title: Label = $RegionDetail/Title
@onready var detail_desc: Label = $RegionDetail/Description
@onready var detail_status: Label = $RegionDetail/Status
@onready var detail_level: Label = $RegionDetail/LevelRange
@onready var back_button: Button = $BackButton

func _ready() -> void:
	back_button.pressed.connect(_on_back_button_pressed)
	load_regions_from_data()

func load_regions_from_data() -> void:
	var file: FileAccess = FileAccess.open("res://data/regions/region_list.json", FileAccess.READ)
	if file:
		var content: String = file.get_as_text()
		var data: Dictionary = JSON.parse_string(content)
		regions = data.get("regions", [])
		_render_regions()
		file.close()

func load_regions(region_list: Array[Dictionary]) -> void:
	regions = region_list
	_render_regions()

func _render_regions() -> void:
	for child in region_container.get_children():
		child.queue_free()
	
	for region in regions:
		var region_card: Button = Button.new()
		region_card.text = region.get("name", "")
		region_card.custom_minimum_size = Vector2(200, 80)
		region_card.set_meta("region_id", region.get("region_id", ""))
		
		var status: String = region.get("status", "locked")
		_update_region_card_style(region_card, status)
		
		region_card.pressed.connect(_on_region_card_pressed)
		region_container.add_child(region_card)

func _update_region_card_style(card: Button, status: String) -> void:
	var style_box: StyleBoxFlat = StyleBoxFlat.new()
	match status:
		"active":
			style_box.bg_color = Color(0.2, 0.6, 0.2)
		"locked":
			style_box.bg_color = Color(0.4, 0.4, 0.4)
			card.disabled = true
		"unstable":
			style_box.bg_color = Color(0.6, 0.4, 0.2)
		"archived":
			style_box.bg_color = Color(0.3, 0.3, 0.3)
			card.disabled = true
		_:
			style_box.bg_color = Color(0.3, 0.3, 0.3)
	
	card.add_theme_stylebox_override("normal", style_box)

func _on_region_card_pressed() -> void:
	var card: Button = get_parent().get_parent() if not is_instance_valid(self) else get_last_signal_receiver()
	var region_id: String = card.get_meta("region_id", "")
	if region_id:
		select_region(region_id)

func select_region(region_id: String) -> void:
	selected_region_id = region_id
	region_selected.emit(region_id)
	
	for region in regions:
		if region.get("region_id") == region_id:
			_show_region_detail(region)
			break

func _show_region_detail(region: Dictionary) -> void:
	detail_title.text = region.get("name", "")
	detail_desc.text = region.get("description", "")
	
	var status_text: String = match region.get("status", ""):
		"active": "活跃"
		"locked": "锁定"
		"unstable": "不稳定"
		"archived": "已归档"
		_: "未知"
	detail_status.text = "状态: " + status_text
	
	var level_range: Array = region.get("level_range", [0, 0])
	detail_level.text = "等级范围: " + str(level_range[0]) + " - " + str(level_range[1])
	
	region_detail.visible = true

func hide_region_detail() -> void:
	region_detail.visible = false
	selected_region_id = ""

func _on_back_button_pressed() -> void:
	back_to_menu.emit()