extends PanelContainer

signal dialog_closed()
signal accept_quest(quest_id: String)

var current_npc: Dictionary = {}
var current_dialog_index: int = 0
var current_quest_id: String = ""
var current_node_id: String = ""
var dialog_tree: Dictionary = {}
var dialog_nodes: Dictionary = {}
var met_npcs: Dictionary = {}

@onready var npc_name: Label = $NPCName
@onready var npc_title: Label = $NPCTitle
@onready var dialog_text: Label = $DialogText
@onready var choices_container: VBoxContainer = $ChoicesContainer
@onready var close_button: Button = $CloseButton
@onready var quest_info: Panel = $QuestInfo
@onready var quest_title: Label = $QuestInfo/QuestTitle
@onready var quest_desc: Label = $QuestInfo/QuestDescription

var reputation_notice: Label = null

func _ready() -> void:
	close_button.pressed.connect(_on_close_button_pressed)
	PlayerManager.reputation_unlocked.connect(_on_reputation_unlocked)
	_ensure_reputation_notice()

func open_dialog(npc_data: Dictionary) -> void:
	current_npc = npc_data
	current_dialog_index = 0
	current_quest_id = ""
	dialog_tree = npc_data.get("dialog_tree", {})
	dialog_nodes = dialog_tree.get("nodes", {})

	npc_name.text = npc_data.get("name", "")
	npc_title.text = npc_data.get("title", "")
	quest_info.visible = false

	_ensure_reputation_notice()
	if is_instance_valid(reputation_notice):
		var npc_id: String = npc_data.get("npc_id", "")
		var region_id: String = npc_data.get("region_id", "")
		var accessible: bool = WorldManager.is_npc_accessible(npc_id, region_id)
		if not accessible:
			var min_rep: int = WorldManager.get_npc_min_reputation(npc_id)
			var region_rep: int = PlayerManager.get_region_reputation(region_id) if region_id != "" else 0
			var level: int = PlayerManager.get_reputation_level(region_rep) if region_id != "" else 0
			var level_name: String = PlayerManager.REPUTATION_LEVELS[level].get("name", "")
			reputation_notice.text = "🔒 此 NPC 需要声望 %d（%s）才能完全互动" % [min_rep, level_name]
			reputation_notice.visible = true
		else:
			reputation_notice.text = ""
			reputation_notice.visible = false

	if dialog_nodes.size() > 0:
		var start_node: String = _determine_start_node()
		current_node_id = start_node
		_show_tree_node(start_node)
	else:
		_fallback_linear_dialog()

	visible = true

func _ensure_reputation_notice() -> void:
	if is_instance_valid(reputation_notice):
		return
	if not is_node_ready():
		return
	if has_node("ReputationNotice"):
		reputation_notice = $ReputationNotice as Label
		return
	var label: Label = Label.new()
	label.name = "ReputationNotice"
	dialog_text.add_sibling(label)
	reputation_notice = label

func _on_reputation_unlocked(_region_id: String) -> void:
	if not visible:
		return
	if current_npc.size() == 0:
		return
	var npc_id: String = current_npc.get("npc_id", "")
	var region_id: String = current_npc.get("region_id", "")
	var accessible: bool = WorldManager.is_npc_accessible(npc_id, region_id)
	if is_instance_valid(reputation_notice):
		reputation_notice.visible = not accessible

func _determine_start_node() -> String:
	var npc_id: String = current_npc.get("npc_id", "")
	var related_quests: Array = current_npc.get("related_quests", [])
	
	for quest_id in related_quests:
		if PlayerManager.is_quest_completed(quest_id):
			if dialog_nodes.has("quest_completed"):
				return "quest_completed"
	
	for quest_id in related_quests:
		if PlayerManager.is_quest_active(quest_id):
			if dialog_nodes.has("default"):
				return "default"
	
	if not _has_met_npc(npc_id):
		_mark_npc_met(npc_id)
		if dialog_nodes.has("first_meet"):
			return "first_meet"
	
	if dialog_nodes.has("default"):
		return "default"
	
	return dialog_tree.get("start", "first_meet")

func _has_met_npc(npc_id: String) -> bool:
	return met_npcs.get(npc_id, false)

func _mark_npc_met(npc_id: String) -> void:
	met_npcs[npc_id] = true

func _show_tree_node(node_id: String) -> void:
	_clear_choices()
	quest_info.visible = false
	
	if not dialog_nodes.has(node_id):
		_dialog_complete()
		return
	
	var node: Dictionary = dialog_nodes[node_id]
	var text: String = node.get("text", "")
	dialog_text.text = text
	
	var quest_trigger: String = node.get("quest_trigger", "")
	if quest_trigger != "":
		current_quest_id = quest_trigger
	
	var choices: Array = node.get("choices", [])
	var is_end: bool = node.get("is_end", false)
	
	if is_end or (choices.size() == 0 and text == ""):
		_dialog_complete()
		return
	
	for i in range(choices.size()):
		var choice: Dictionary = choices[i]
		var choice_button: Button = Button.new()
		choice_button.text = choice.get("text", "继续")
		choice_button.custom_minimum_size = Vector2(500, 40)

		var npc_id: String = current_npc.get("npc_id", "")
		var region_id: String = current_npc.get("region_id", "")
		var accessible: bool = WorldManager.is_npc_accessible(npc_id, region_id)

		var style_box: StyleBoxFlat = StyleBoxFlat.new()
		if accessible:
			style_box.bg_color = Color(0.2, 0.4, 0.6)
			choice_button.disabled = false
		else:
			style_box.bg_color = Color(0.4, 0.4, 0.4)
			choice_button.disabled = true
		choice_button.add_theme_stylebox_override("normal", style_box)

		var hover_style: StyleBoxFlat = StyleBoxFlat.new()
		hover_style.bg_color = Color(0.3, 0.5, 0.7) if accessible else Color(0.45, 0.45, 0.45)
		choice_button.add_theme_stylebox_override("hover", hover_style)

		choice_button.set_meta("choice_index", i)
		choice_button.pressed.connect(_on_choice_selected.bind(i))
		choices_container.add_child(choice_button)

	close_button.visible = true

func _on_choice_selected(index: int) -> void:
	var node: Dictionary = dialog_nodes.get(current_node_id, {})
	var choices: Array = node.get("choices", [])
	
	if index >= choices.size():
		return
	
	var choice: Dictionary = choices[index]
	var action: String = choice.get("action", "")
	
	if action == "accept_quest" and current_quest_id != "":
		var result: Dictionary = PlayerManager.accept_quest_api(current_quest_id)
		if result.get("success", false):
			accept_quest.emit(current_quest_id)
			_show_quest_accepted_info(current_quest_id)
		else:
			_show_quest_error(result.get("message", "接取任务失败"))
	
	var next_id: String = choice.get("next", "")
	if next_id == "" or next_id == "goodbye":
		var goodbye_node: Dictionary = dialog_nodes.get("goodbye", {})
		if goodbye_node.get("is_end", false):
			_dialog_complete()
		else:
			_dialog_complete()
		return
	
	current_node_id = next_id
	_show_tree_node(next_id)

func _show_quest_accepted_info(quest_id: String) -> void:
	var quest: Dictionary = PlayerManager.get_player_quest_by_id(quest_id)
	if quest.size() > 0:
		quest_title.text = "已接取: " + quest.get("title", "")
		quest_desc.text = quest.get("description", "")
	else:
		var quests: Array = _load_quests()
		for q in quests:
			if q.get("quest_id") == quest_id:
				quest_title.text = "已接取: " + q.get("title", "")
				quest_desc.text = q.get("description", "")
				break
	quest_info.visible = true

func _show_quest_error(message: String) -> void:
	quest_title.text = "接取失败"
	quest_desc.text = message
	var style_box: StyleBoxFlat = StyleBoxFlat.new()
	style_box.bg_color = Color(0.6, 0.2, 0.2, 0.8)
	quest_info.add_theme_stylebox_override("panel", style_box)
	quest_info.visible = true

func _clear_choices() -> void:
	for child in choices_container.get_children():
		child.queue_free()

func _fallback_linear_dialog() -> void:
	var dialogs: Array = current_npc.get("dialogs", [])
	if dialogs.size() == 0:
		_dialog_complete()
		return
	
	dialog_text.text = dialogs[0].get("text", "")
	
	var next_button: Button = Button.new()
	next_button.text = "继续" if dialogs.size() > 1 else "关闭"
	next_button.custom_minimum_size = Vector2(500, 40)
	next_button.pressed.connect(_on_linear_next)
	choices_container.add_child(next_button)

func _on_linear_next() -> void:
	var dialogs: Array = current_npc.get("dialogs", [])
	current_dialog_index += 1
	
	if current_dialog_index >= dialogs.size():
		_dialog_complete()
		return
	
	_clear_choices()
	dialog_text.text = dialogs[current_dialog_index].get("text", "")
	
	var has_quest: bool = dialogs[current_dialog_index].has("quest_id")
	if has_quest:
		current_quest_id = dialogs[current_dialog_index].get("quest_id", "")
		_show_quest_offer(current_quest_id)
	
	var is_last: bool = (current_dialog_index == dialogs.size() - 1)
	var next_button: Button = Button.new()
	next_button.text = "关闭" if is_last else "继续"
	next_button.custom_minimum_size = Vector2(500, 40)
	next_button.pressed.connect(_on_linear_next)
	choices_container.add_child(next_button)

func _show_quest_offer(quest_id: String) -> void:
	current_quest_id = quest_id
	var quests: Array = _load_quests()
	for quest in quests:
		if quest.get("quest_id") == quest_id:
			quest_title.text = quest.get("title", "")
			quest_desc.text = quest.get("description", "")
			quest_info.visible = true
			
			var accept_button: Button = Button.new()
			accept_button.text = "接受任务"
			accept_button.custom_minimum_size = Vector2(500, 40)
			var style_box: StyleBoxFlat = StyleBoxFlat.new()
			style_box.bg_color = Color(0.2, 0.6, 0.3)
			accept_button.add_theme_stylebox_override("normal", style_box)
			accept_button.pressed.connect(_on_accept_quest_button_pressed)
			choices_container.add_child(accept_button)
			break

func _on_accept_quest_button_pressed() -> void:
	if current_quest_id:
		accept_quest.emit(current_quest_id)
		_dialog_complete()

func _load_quests() -> Array:
	var file: FileAccess = FileAccess.open("res://data/quests/quest_list.json", FileAccess.READ)
	if file:
		var content: String = file.get_as_text()
		var data: Dictionary = JSON.parse_string(content)
		file.close()
		return data.get("quests", [])
	return []

func _dialog_complete() -> void:
	_clear_choices()
	visible = false
	dialog_closed.emit()

func _on_close_button_pressed() -> void:
	_dialog_complete()

func get_current_node_id() -> String:
	return current_node_id

func get_current_quest_trigger() -> String:
	var node: Dictionary = dialog_nodes.get(current_node_id, {})
	return node.get("quest_trigger", "")

func set_met_npcs(data: Dictionary) -> void:
	met_npcs = data

func get_met_npcs() -> Dictionary:
	return met_npcs
