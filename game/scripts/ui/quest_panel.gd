extends PanelContainer

signal quest_selected(quest_id: String)
signal back_to_menu()
signal open_npc_dialog(npc_id: String)

var quests: Array[Dictionary] = []
var selected_quest_id: String = ""

@onready var quest_list: VBoxContainer = $QuestList
@onready var quest_detail: Panel = $QuestDetail
@onready var detail_title: Label = $QuestDetail/Title
@onready var detail_desc: Label = $QuestDetail/Description
@onready var detail_status: Label = $QuestDetail/Status
@onready var detail_objectives: VBoxContainer = $QuestDetail/Objectives
@onready var detail_rewards: Label = $QuestDetail/Rewards
@onready var accept_button: Button = $QuestDetail/AcceptButton
@onready var back_button: Button = $BackButton

func _ready() -> void:
	back_button.pressed.connect(_on_back_button_pressed)
	accept_button.pressed.connect(_on_accept_button_pressed)
	load_quests_from_data()

func load_quests_from_data() -> void:
	var file: FileAccess = FileAccess.open("res://data/quests/quest_list.json", FileAccess.READ)
	if file:
		var content: String = file.get_as_text()
		var data: Dictionary = JSON.parse_string(content)
		quests = data.get("quests", [])
		_render_quests()
		file.close()

func load_quests(quest_list: Array[Dictionary]) -> void:
	quests = quest_list
	_render_quests()

func _render_quests() -> void:
	for child in quest_list.get_children():
		child.queue_free()
	
	for quest in quests:
		var quest_item: Button = Button.new()
		quest_item.text = quest.get("title", "") + " [" + _get_status_text(quest.get("status", "")) + "]"
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
		if quest.get("quest_id") == quest_id:
			_show_quest_detail(quest)
			break

func _show_quest_detail(quest: Dictionary) -> void:
	detail_title.text = quest.get("title", "")
	detail_desc.text = quest.get("description", "")
	
	var status_text: String = _get_status_text(quest.get("status", ""))
	detail_status.text = "状态: " + status_text
	
	for child in detail_objectives.get_children():
		child.queue_free()
	
	var objectives: Array = quest.get("objectives", [])
	for obj in objectives:
		var obj_label: Label = Label.new()
		obj_label.text = "- " + obj.get("description", "") + " (" + str(obj.get("progress", 0)) + "/" + str(obj.get("target", 1)) + ")"
		detail_objectives.add_child(obj_label)
	
	var rewards: Dictionary = quest.get("rewards", {})
	var rewards_text: String = "奖励: "
	if rewards.has("experience"):
		rewards_text += "经验 " + str(rewards.experience) + " "
	if rewards.has("gold"):
		rewards_text += "金币 " + str(rewards.gold) + " "
	if rewards.has("items"):
		rewards_text += "物品: " + str(rewards.items)
	detail_rewards.text = rewards_text
	
	var status: String = quest.get("status", "available")
	accept_button.visible = (status == "available")
	
	quest_detail.visible = true

func hide_quest_detail() -> void:
	quest_detail.visible = false
	selected_quest_id = ""

func _on_accept_button_pressed() -> void:
	for quest in quests:
		if quest.get("quest_id") == selected_quest_id:
			quest["status"] = "active"
			_render_quests()
			_show_quest_detail(quest)
			break

func _on_back_button_pressed() -> void:
	back_to_menu.emit()