extends PanelContainer

signal back_to_menu()
signal reputation_selected(region_id: String)

var reputation_list: Array[Dictionary] = []
var selected_region_id: String = ""
var is_loading: bool = false
var error_message: String = ""

@onready var rep_list: VBoxContainer = $ReputationList
@onready var rep_detail: Panel = $ReputationDetail
@onready var detail_region_name: Label = $ReputationDetail/RegionName
@onready var detail_level: Label = $ReputationDetail/Level
@onready var detail_reputation: Label = $ReputationDetail/ReputationValue
@onready var detail_progress_bar: ProgressBar = $ReputationDetail/ProgressBar
@onready var detail_next_level: Label = $ReputationDetail/NextLevel
@onready var back_button: Button = $BackButton
@onready var loading_label: Label = $LoadingLabel
@onready var error_label: Label = $ErrorLabel
@onready var title_label: Label = $TitleLabel

func _ready() -> void:
	back_button.pressed.connect(_on_back_button_pressed)
	PlayerManager.player_reputation_loaded.connect(_on_reputation_loaded)
	PlayerManager.player_error.connect(_on_player_error)
	load_reputation_from_server()

func load_reputation_from_server() -> void:
	_set_loading(true)
	error_message = ""
	PlayerManager.fetch_all_reputation()

func _on_reputation_loaded() -> void:
	reputation_list = PlayerManager.reputation_list.duplicate()
	_set_loading(false)
	error_message = ""
	_render_reputation_list()

func _on_player_error(error_code: String, message: String) -> void:
	_set_loading(false)
	error_message = message
	_update_error_display()

func _set_loading(loading: bool) -> void:
	is_loading = loading
	if is_instance_valid(loading_label):
		loading_label.visible = loading

func _update_error_display() -> void:
	if is_instance_valid(error_label):
		error_label.visible = error_message != ""
		error_label.text = error_message

func _render_reputation_list() -> void:
	for child in rep_list.get_children():
		child.queue_free()
	
	if reputation_list.is_empty():
		var empty_label: Label = Label.new()
		empty_label.text = "暂无声望记录"
		empty_label.add_theme_color_override("font_color", Color(0.6, 0.6, 0.6))
		rep_list.add_child(empty_label)
		return
	
	for rep in reputation_list:
		var item: HBoxContainer = HBoxContainer.new()
		item.custom_minimum_size = Vector2(0, 50)
		item.add_theme_constant_override("separation", 10)
		
		var region_id: String = rep.get("region_id", "unknown")
		var reputation: int = rep.get("reputation", 0)
		var level_key: String = rep.get("reputation_level", "neutral")
		var level_info: Dictionary = PlayerManager.get_reputation_level_info(level_key)
		
		var icon_label: Label = Label.new()
		icon_label.text = level_info.get("icon", "❓")
		icon_label.add_theme_font_size_override("font_size", 24)
		icon_label.custom_minimum_size = Vector2(40, 0)
		item.add_child(icon_label)
		
		var info_vbox: VBoxContainer = VBoxContainer.new()
		info_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		
		var name_label: Label = Label.new()
		name_label.text = _get_region_display_name(region_id)
		name_label.add_theme_font_size_override("font_size", 16)
		name_label.add_theme_color_override("font_color", Color.WHITE)
		info_vbox.add_child(name_label)
		
		var level_label: Label = Label.new()
		level_label.text = level_info.get("name", level_key)
		level_label.add_theme_color_override("font_color", Color(level_info.get("color", "#FFFFFF")))
		info_vbox.add_child(level_label)
		
		item.add_child(info_vbox)
		
		var rep_value_label: Label = Label.new()
		rep_value_label.text = str(reputation)
		rep_value_label.add_theme_color_override("font_color", Color(0.8, 0.8, 0.8))
		rep_value_label.custom_minimum_size = Vector2(80, 0)
		rep_value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		item.add_child(rep_value_label)
		
		var item_button: Button = Button.new()
		item_button.flat = true
		item_button.custom_minimum_size = Vector2(0, 50)
		item_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		item_button.add_child(item)
		item_button.pressed.connect(_on_reputation_item_pressed.bind(region_id))
		rep_list.add_child(item_button)

func _get_region_display_name(region_id: String) -> String:
	var region: Dictionary = WorldManager.get_region_by_id(region_id)
	if region.has("name"):
		return region["name"]
	return region_id

func _on_reputation_item_pressed(region_id: String) -> void:
	selected_region_id = region_id
	_render_detail(region_id)
	reputation_selected.emit(region_id)

func _render_detail(region_id: String) -> void:
	var rep_data: Dictionary = {}
	for rep in reputation_list:
		if rep.get("region_id", "") == region_id:
			rep_data = rep
			break
	
	if rep_data.is_empty():
		rep_data = PlayerManager.fetch_region_reputation(region_id)
	
	if rep_data.is_empty():
		return
	
	var level_key: String = rep_data.get("reputation_level", "neutral")
	var level_info: Dictionary = PlayerManager.get_reputation_level_info(level_key)
	var progress_info: Dictionary = PlayerManager.get_reputation_progress(region_id)
	
	detail_region_name.text = _get_region_display_name(region_id)
	detail_level.text = "%s %s" % [level_info.get("icon", "❓"), level_info.get("name", level_key)]
	detail_level.add_theme_color_override("font_color", Color(level_info.get("color", "#FFFFFF")))
	detail_reputation.text = "声望值: %d" % rep_data.get("reputation", 0)
	detail_progress_bar.value = progress_info.get("progress", 0.0) * 100
	
	var next_threshold: int = progress_info.get("next_level_threshold", 0)
	var current_rep: int = rep_data.get("reputation", 0)
	if level_key == "exalted":
		detail_next_level.text = "已达最高等级"
	else:
		detail_next_level.text = "距离下一等级: %d / %d" % [current_rep, next_threshold]

func _on_back_button_pressed() -> void:
	back_to_menu.emit()

func refresh() -> void:
	load_reputation_from_server()
