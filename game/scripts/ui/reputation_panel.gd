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

var next_unlock_label: Label = null
var unlockable_label: Label = null

func _ready() -> void:
	back_button.pressed.connect(_on_back_button_pressed)
	PlayerManager.player_reputation_loaded.connect(_on_reputation_loaded)
	PlayerManager.player_error.connect(_on_player_error)
	PlayerManager.reputation_unlocked.connect(_on_reputation_unlocked)
	_ensure_detail_extras()
	load_reputation_from_server()

func _ensure_detail_extras() -> void:
	if not is_instance_valid(rep_detail):
		return
	if not is_instance_valid(next_unlock_label):
		if rep_detail.has_node("NextUnlockLabel"):
			next_unlock_label = rep_detail.get_node("NextUnlockLabel") as Label
		else:
			var label: Label = Label.new()
			label.name = "NextUnlockLabel"
			detail_next_level.add_sibling(label)
			next_unlock_label = label
	if not is_instance_valid(unlockable_label):
		if rep_detail.has_node("UnlockableLabel"):
			unlockable_label = rep_detail.get_node("UnlockableLabel") as Label
		else:
			var label2: Label = Label.new()
			label2.name = "UnlockableLabel"
			if is_instance_valid(next_unlock_label):
				next_unlock_label.add_sibling(label2)
			else:
				detail_next_level.add_sibling(label2)
			unlockable_label = label2

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

	_ensure_detail_extras()
	if is_instance_valid(next_unlock_label):
		var next_unlock: int = PlayerManager.get_next_unlock_threshold(current_rep)
		var unlock_level: int = PlayerManager.get_reputation_level(next_unlock) if next_unlock > 0 else -1
		if next_unlock <= 0:
			next_unlock_label.text = "下一解锁阈值: 已全部解锁"
		elif current_rep < next_unlock:
			next_unlock_label.text = "下一区域解锁阈值: 声望 %d（还需 %d 点，%s）" % [
				next_unlock,
				next_unlock - current_rep,
				PlayerManager.REPUTATION_LEVELS[unlock_level].get("name", "") if unlock_level >= 0 else ""
			]
		else:
			next_unlock_label.text = "下一区域解锁阈值: 声望 %d（已达成）" % next_unlock

	if is_instance_valid(unlockable_label):
		var unlockable_regions: Array = PlayerManager.get_unlocked_regions_by_reputation(current_rep)
		var already_unlocked: Array = PlayerManager.get_unlocked_regions_by_reputation(current_rep - 1)
		var newly_unlocked: Array = []
		for rid in unlockable_regions:
			if not already_unlocked.has(rid):
				newly_unlocked.append(rid)
		if newly_unlocked.is_empty():
			unlockable_label.text = "当前声望可解锁: 0 个新区域"
		else:
			var names: Array = []
			for rid in newly_unlocked:
				names.append(_get_region_display_name(rid))
			unlockable_label.text = "当前声望可解锁: " + "、".join(names) + "（%d 个）" % newly_unlocked.size()

func _on_reputation_unlocked(_region_id: String) -> void:
	if selected_region_id != "":
		_render_detail(selected_region_id)

func _on_back_button_pressed() -> void:
	back_to_menu.emit()

func refresh() -> void:
	load_reputation_from_server()
