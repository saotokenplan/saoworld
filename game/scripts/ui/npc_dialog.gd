extends PanelContainer

signal dialog_closed()
signal accept_quest(quest_id: String)

var current_npc: Dictionary = {}
var current_dialog_index: int = 0
var current_quest_id: String = ""

@onready var npc_name: Label = $NPCName
@onready var dialog_text: Label = $DialogText
@onready var next_button: Button = $NextButton
@onready var accept_quest_button: Button = $AcceptQuestButton
@onready var close_button: Button = $CloseButton
@onready var quest_info: Panel = $QuestInfo
@onready var quest_title: Label = $QuestInfo/QuestTitle
@onready var quest_desc: Label = $QuestInfo/QuestDescription

func _ready() -> void:
	next_button.pressed.connect(_on_next_button_pressed)
	accept_quest_button.pressed.connect(_on_accept_quest_button_pressed)
	close_button.pressed.connect(_on_close_button_pressed)

func open_dialog(npc_data: Dictionary) -> void:
	current_npc = npc_data
	current_dialog_index = 0
	current_quest_id = ""
	
	npc_name.text = npc_data.get("name", "")
	quest_info.visible = false
	accept_quest_button.visible = false
	
	_show_current_dialog()
	visible = true

func _show_current_dialog() -> void:
	var dialogs: Array = current_npc.get("dialogs", [])
	if current_dialog_index < dialogs.size():
		var dialog: Dictionary = dialogs[current_dialog_index]
		dialog_text.text = dialog.get("text", "")
		
		var has_quest: bool = dialog.has("quest_id")
		var is_last: bool = (current_dialog_index == dialogs.size() - 1)
		
		next_button.visible = not has_quest and not is_last
		
		if has_quest:
			_show_quest_offer(dialog.get("quest_id", ""))
		elif is_last:
			next_button.text = "关闭"
		else:
			next_button.text = "继续"
	else:
		_dialog_complete()

func _show_quest_offer(quest_id: String) -> void:
	current_quest_id = quest_id
	
	var quests: Array = _load_quests()
	for quest in quests:
		if quest.get("quest_id") == quest_id:
			quest_title.text = quest.get("title", "")
			quest_desc.text = quest.get("description", "")
			quest_info.visible = true
			accept_quest_button.visible = true
			next_button.visible = false
			break

func _load_quests() -> Array:
	var file: FileAccess = FileAccess.open("res://data/quests/quest_list.json", FileAccess.READ)
	if file:
		var content: String = file.get_as_text()
		var data: Dictionary = JSON.parse_string(content)
		file.close()
		return data.get("quests", [])
	return []

func _on_next_button_pressed() -> void:
	var dialogs: Array = current_npc.get("dialogs", [])
	if current_dialog_index < dialogs.size() - 1:
		current_dialog_index += 1
		_show_current_dialog()
	else:
		_dialog_complete()

func _on_accept_quest_button_pressed() -> void:
	if current_quest_id:
		accept_quest.emit(current_quest_id)
		_dialog_complete()

func _dialog_complete() -> void:
	visible = false
	dialog_closed.emit()

func _on_close_button_pressed() -> void:
	_dialog_complete()