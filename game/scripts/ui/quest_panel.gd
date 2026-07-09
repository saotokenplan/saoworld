extends PanelContainer

signal quest_selected(quest_id: String)
signal back_to_menu()
signal open_npc_dialog(npc_id: String)
signal quest_accepted(quest_id: String)
signal quest_completed(quest_id: String)

var quests: Array[Dictionary] = []
var selected_quest_id: String = ""
var is_loading: bool = false
var error_message: String = ""

@onready var quest_list: VBoxContainer = $QuestList
@onready var quest_detail: Panel = $QuestDetail
@onready var detail_title: Label = $QuestDetail/Title
@onready var detail_desc: Label = $QuestDetail/Description
@onready var detail_status: Label = $QuestDetail/Status
@onready var detail_objectives: VBoxContainer = $QuestDetail/Objectives
@onready var detail_rewards: Label = $QuestDetail/Rewards
@onready var accept_button: Button = $QuestDetail/AcceptButton
@onready var complete_button: Button = $QuestDetail/CompleteButton
@onready var back_button: Button = $BackButton
@onready var loading_label: Label = $LoadingLabel
@onready var error_label: Label = $ErrorLabel
@onready var status_filter_option: OptionButton = $StatusFilter

func _ready() -> void:
	back_button.pressed.connect(_on_back_button_pressed)
	accept_button.pressed.connect(_on_accept_button_pressed)
	complete_button.pressed.connect(_on_complete_button_pressed)
	if status_filter_option:
		status_filter_option.item_selected.connect(_on_status_filter_selected)
		_init_status_filter()
	PlayerManager.player_quests_loaded.connect(_on_player_quests_loaded)
	PlayerManager.player_error.connect(_on_player_error)
	load_quests_from_server()

func _init_status_filter() -> void:
	if not status_filter_option:
		return
	status_filter_option.clear()
	status_filter_option.add_item("全部", 0)
	status_filter_option.add_item("可接取", 1)
	status_filter_option.add_item("进行中", 2)
	status_filter_option.add_item("已完成", 3)
	status_filter_option.add_item("已失败", 4)
	status_filter_option.selected = 0

func _on_status_filter_selected(index: int) -> void:
	_render_quests()

func _get_filter_status() -> String:
	if not status_filter_option:
		return ""
	match status_filter_option.selected:
		1: return "available"
		2: return "active"
		3: return "completed"
		4: return "failed"
		_: return ""

func load_quests_from_server() -> void:
	_set_loading(true)
	error_message = ""
	PlayerManager.fetch_player_quests()

func load_quests(quest_list_arg: Array[Dictionary]) -> void:
	quests = quest_list_arg
	_render_quests()

func _on_player_quests_loaded() -> void:
	quests = PlayerManager.player_quests.duplicate()
	_set_loading(false)
	error_message = ""
	_render_quests()

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

func _render_quests() -> void:
	for child in quest_list.get_children():
		child.queue_free()
	
	var filter_status: String = _get_filter_status()
	var filtered_quests: Array[Dictionary] = []
	
	if filter_status == "":
		filtered_quests = quests
	else:
		for quest in quests:
			if quest.get("status", "") == filter_status:
				filtered_quests.append(quest)
	
	if filtered_quests.size() == 0:
		var empty_label: Label = Label.new()
		empty_label.text = "暂无任务"
		empty_label.add_theme_font_size_override("font_size", 16)
		quest_list.add_child(empty_label)
		return
	
	for quest in filtered_quests:
		var quest_item: Button = Button.new()
		quest_item.text = quest.get("title", quest.get("quest_id", "")) + " [" + _get_status_text(quest.get("status", "")) + "]"
		quest_item.custom_minimum_size = Vector2(400, 40)
		quest_item.set_meta("quest_id", quest.get("quest_id", ""))
		
		var status: String = quest.get("status", "available")
		_update_quest_item_style(quest_item, status)
		
		quest_item.pressed.connect(_on_quest_item_pressed)
		quest_list.add_child(quest_item)

func _get_status_text(status: String) -> String:
	return match status:
		"available": "可接取"
		"active": "进行中"
		"completed": "已完成"
		"failed": "已失败"
		_: "未知"

func _update_quest_item_style(item: Button, status: String) -> void:
	var style_box: StyleBoxFlat = StyleBoxFlat.new()
	match status:
		"available":
			style_box.bg_color = Color(0.2, 0.4, 0.6)
		"active":
			style_box.bg_color = Color(0.6, 0.5, 0.2)
		"completed":
			style_box.bg_color = Color(0.2, 0.6, 0.2)
		"failed":
			style_box.bg_color = Color(0.6, 0.2, 0.2)
		_:
			style_box.bg_color = Color(0.3, 0.3, 0.3)
	
	item.add_theme_stylebox_override("normal", style_box)

func _on_quest_item_pressed() -> void:
	var item: Button = get_last_signal_receiver()
	var quest_id: String = item.get_meta("quest_id", "")
	if quest_id:
		select_quest(quest_id)

func select_quest(quest_id: String) -> void:
	selected_quest_id = quest_id
	quest_selected.emit(quest_id)
	
	for quest in quests:
		var qid: String = quest.get("quest_id", quest.get("player_quest_id", ""))
		if qid == quest_id:
			_show_quest_detail(quest)
			break

func _show_quest_detail(quest: Dictionary) -> void:
	detail_title.text = quest.get("title", quest.get("quest_id", ""))
	detail_desc.text = quest.get("description", "")
	
	var status_text: String = _get_status_text(quest.get("status", ""))
	detail_status.text = "状态: " + status_text
	
	for child in detail_objectives.get_children():
		child.queue_free()
	
	var objectives: Array = quest.get("objectives", [])
	if objectives.size() > 0:
		for obj in objectives:
			var obj_label: Label = Label.new()
			var desc: String = obj.get("description", obj.get("text", ""))
			var progress: int = obj.get("progress", 0)
			var target: int = obj.get("target", 1)
			var completed: bool = obj.get("completed", progress >= target)
			var prefix: String = "[✓] " if completed else "[ ] "
			obj_label.text = prefix + desc + " (" + str(progress) + "/" + str(target) + ")"
			obj_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			detail_objectives.add_child(obj_label)
	else:
		var obj_jsonb: Dictionary = quest.get("objectives_jsonb", {})
		if obj_jsonb.size() > 0:
			for key in obj_jsonb.keys():
				var obj_label: Label = Label.new()
				obj_label.text = "- " + key + ": " + str(obj_jsonb[key])
				obj_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				detail_objectives.add_child(obj_label)
	
	var rewards: Dictionary = quest.get("rewards", {})
	if rewards.size() == 0:
		rewards = quest.get("rewards_jsonb", {})
	var rewards_text: String = "奖励: "
	if rewards.has("experience") or rewards.has("exp"):
		rewards_text += "经验 " + str(rewards.get("experience", rewards.get("exp", 0))) + " "
	if rewards.has("gold") or rewards.has("gold_coins"):
		rewards_text += "金币 " + str(rewards.get("gold", rewards.get("gold_coins", 0))) + " "
	if rewards.has("items"):
		rewards_text += "物品: " + str(rewards.items)
	detail_rewards.text = rewards_text
	
	var status: String = quest.get("status", "available")
	accept_button.visible = (status == "available")
	complete_button.visible = (status == "active")
	
	quest_detail.visible = true

func hide_quest_detail() -> void:
	quest_detail.visible = false
	selected_quest_id = ""

func _on_accept_button_pressed() -> void:
	if selected_quest_id == "":
		return
	
	accept_button.disabled = true
	var result: Dictionary = PlayerManager.accept_quest_api(selected_quest_id)
	accept_button.disabled = false
	
	if result.get("success", false):
		quest_accepted.emit(selected_quest_id)
		accept_button.visible = false
		complete_button.visible = true
		var quest_data: Dictionary = result.get("data", {})
		if quest_data.size() > 0:
			_show_quest_detail(quest_data)
	else:
		error_message = result.get("message", "接取任务失败")
		_update_error_display()

func _on_complete_button_pressed() -> void:
	if selected_quest_id == "":
		return
	
	complete_button.disabled = true
	var result: Dictionary = PlayerManager.complete_quest_api(selected_quest_id)
	complete_button.disabled = false
	
	if result.get("success", false):
		quest_completed.emit(selected_quest_id)
		complete_button.visible = false
		var quest_data: Dictionary = result.get("data", {})
		if quest_data.size() > 0:
			_show_quest_detail(quest_data)
	else:
		error_message = result.get("message", "完成任务失败")
		_update_error_display()

func _on_back_button_pressed() -> void:
	back_to_menu.emit()

func get_selected_quest() -> Dictionary:
	for quest in quests:
		var qid: String = quest.get("quest_id", quest.get("player_quest_id", ""))
		if qid == selected_quest_id:
			return quest
	return {}
