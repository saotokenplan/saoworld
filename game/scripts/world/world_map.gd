extends Node2D

signal region_selected(region_id: String)
signal enter_region_requested(region_id: String)
signal back_to_menu()

var regions: Array[Dictionary] = []
var selected_region_id: String = ""
var current_status_filter: String = ""
var current_chapter_filter: String = ""

@onready var region_container: HBoxContainer = $RegionContainer
@onready var region_detail: Panel = $RegionDetail
@onready var detail_title: Label = $RegionDetail/Title
@onready var detail_desc: Label = $RegionDetail/Description
@onready var detail_status: Label = $RegionDetail/Status
@onready var detail_level: Label = $RegionDetail/LevelRange
@onready var detail_type: Label = $RegionDetail/RegionType
@onready var detail_progress: Label = $RegionDetail/Progress
@onready var detail_reputation: Label = $RegionDetail/Reputation
@onready var back_button: Button = $BackButton
@onready var enter_button: Button = $EnterRegionButton
@onready var status_filter: ButtonGroup = $StatusFilter
@onready var chapter_filter: ButtonGroup = $ChapterFilter
@onready var search_box: LineEdit = $SearchBox

func _ready() -> void:
	back_button.pressed.connect(_on_back_button_pressed)
	
	if is_instance_valid(enter_button):
		enter_button.pressed.connect(_on_enter_region_button_pressed)
		enter_button.visible = false
	
	if is_instance_valid(search_box):
		search_box.text_changed.connect(_on_search_text_changed)
	
	WorldManager.regions_loaded.connect(_on_regions_loaded)
	
	load_regions_from_data()
	
	refresh_from_server()

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
	
	var filtered_regions: Array[Dictionary] = _apply_filters(regions)
	
	for region in filtered_regions:
		var region_card: Button = Button.new()
		
		var type_icon: String = WorldManager.get_region_type_info(region.get("type", "")).get("icon", "📍")
		var status_info: Dictionary = WorldManager.get_region_status_info(region.get("status", ""))
		var status_name: String = status_info.get("name", "")
		
		region_card.text = "%s %s\n[%s]" % [type_icon, region.get("name", ""), status_name]
		region_card.custom_minimum_size = Vector2(220, 90)
		region_card.set_meta("region_id", region.get("region_id", ""))
		
		var status: String = region.get("status", "locked")
		var is_unlocked: bool = WorldManager.is_region_unlocked(region.get("region_id", ""))
		_update_region_card_style(region_card, status, is_unlocked)
		
		var region_id: String = region.get("region_id", "")
		region_card.pressed.connect(_on_region_card_pressed.bind(region_id))
		region_container.add_child(region_card)

func _update_region_card_style(card: Button, status: String, is_unlocked: bool = false) -> void:
	var style_box: StyleBoxFlat = StyleBoxFlat.new()
	match status:
		"active":
			if is_unlocked:
				style_box.bg_color = Color(0.15, 0.65, 0.15)
			else:
				style_box.bg_color = Color(0.2, 0.6, 0.2)
		"locked":
			if is_unlocked:
				style_box.bg_color = Color(0.3, 0.5, 0.3)
				card.disabled = false
			else:
				style_box.bg_color = Color(0.4, 0.4, 0.4)
				card.disabled = true
		"unstable":
			if is_unlocked:
				style_box.bg_color = Color(0.65, 0.35, 0.15)
			else:
				style_box.bg_color = Color(0.6, 0.4, 0.2)
		"archived":
			style_box.bg_color = Color(0.3, 0.3, 0.3)
			card.disabled = true
		_:
			style_box.bg_color = Color(0.3, 0.3, 0.3)
	
	card.add_theme_stylebox_override("normal", style_box)

func _on_region_card_pressed(region_id: String) -> void:
	if region_id:
		select_region(region_id)

func _on_enter_region_button_pressed() -> void:
	if selected_region_id:
		enter_region_requested.emit(selected_region_id)

func select_region(region_id: String) -> void:
	selected_region_id = region_id
	region_selected.emit(region_id)
	
	for region in regions:
		if region.get("region_id") == region_id:
			_show_region_detail(region)
			break

func _show_region_detail(region: Dictionary) -> void:
	var region_id: String = region.get("region_id", "")
	
	detail_title.text = region.get("name", "")
	detail_desc.text = region.get("description", "")
	
	var status_text: String = match region.get("status", ""):
		"active": "活跃"
		"locked": "锁定"
		"unstable": "不稳定"
		"archived": "已归档"
		_: "未知"
	
	var is_unlocked: bool = WorldManager.is_region_unlocked(region_id)
	var unlocked_text: String = "（已解锁）" if is_unlocked else "（未解锁）"
	detail_status.text = "状态: " + status_text + unlocked_text
	
	var level_range: Array = region.get("level_range", [0, 0])
	detail_level.text = "等级范围: " + str(level_range[0]) + " - " + str(level_range[1])
	
	var type_info: Dictionary = WorldManager.get_region_type_info(region.get("type", ""))
	detail_type.text = "区域类型: " + type_info.get("icon", "📍") + " " + type_info.get("name", "")
	
	var progression: Dictionary = WorldManager.get_region_progression(region_id)
	detail_progress.text = "任务进度: %d/%d (%.0f%%)" % [
		progression.get("completed_quests", 0),
		progression.get("total_quests", 0),
		progression.get("progress", 0) * 100
	]
	
	var reputation: int = WorldManager.get_region_reputation(region_id)
	detail_reputation.text = "声望值: %d" % reputation
	
	region_detail.visible = true
	
	if is_instance_valid(enter_button):
		var can_enter: bool = is_unlocked and region.get("status", "locked") != "archived"
		enter_button.visible = can_enter
		enter_button.disabled = not can_enter

func hide_region_detail() -> void:
	region_detail.visible = false
	selected_region_id = ""
	
	if is_instance_valid(enter_button):
		enter_button.visible = false

func _on_back_button_pressed() -> void:
	back_to_menu.emit()

func _apply_filters(region_list: Array[Dictionary]) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = region_list.duplicate()
	
	if current_status_filter != "":
		filtered = [region for region in filtered if region.get("status", "") == current_status_filter]
	
	if current_chapter_filter != "":
		filtered = [region for region in filtered if region.get("chapter_id", "") == current_chapter_filter]
	
	return filtered

func set_status_filter(status: String) -> void:
	current_status_filter = status
	_render_regions()

func set_chapter_filter(chapter_id: String) -> void:
	current_chapter_filter = chapter_id
	_render_regions()

func clear_filters() -> void:
	current_status_filter = ""
	current_chapter_filter = ""
	if is_instance_valid(search_box):
		search_box.text = ""
	_render_regions()

func _on_search_text_changed(text: String) -> void:
	if text == "":
		_render_regions()
	else:
		var search_results: Array[Dictionary] = WorldManager.search_regions(text)
		_render_search_results(search_results)

func _render_search_results(results: Array[Dictionary]) -> void:
	for child in region_container.get_children():
		child.queue_free()
	
	for region in results:
		var region_card: Button = Button.new()
		
		var type_icon: String = WorldManager.get_region_type_info(region.get("type", "")).get("icon", "📍")
		var status_info: Dictionary = WorldManager.get_region_status_info(region.get("status", ""))
		var status_name: String = status_info.get("name", "")
		
		region_card.text = "%s %s\n[%s]" % [type_icon, region.get("name", ""), status_name]
		region_card.custom_minimum_size = Vector2(220, 90)
		region_card.set_meta("region_id", region.get("region_id", ""))
		
		var status: String = region.get("status", "locked")
		var is_unlocked: bool = WorldManager.is_region_unlocked(region.get("region_id", ""))
		_update_region_card_style(region_card, status, is_unlocked)
		
		var region_id: String = region.get("region_id", "")
		region_card.pressed.connect(_on_region_card_pressed.bind(region_id))
		region_container.add_child(region_card)

func refresh_from_server() -> void:
	WorldManager.fetch_regions()

func _on_regions_loaded() -> void:
	regions = WorldManager.regions
	_render_regions()

func get_selected_region() -> Dictionary:
	for region in regions:
		if region.get("region_id", "") == selected_region_id:
			return region
	return {}

func get_region_count() -> int:
	return regions.size()

func get_unlocked_region_count() -> int:
	return WorldManager.get_unlocked_region_count()
