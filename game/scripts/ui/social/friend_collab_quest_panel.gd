extends Control

signal close_pressed
signal quest_selected(quest_id: String)

enum QuestMode { ACTIVE = 0, PENDING = 1, HISTORY = 2 }

@onready var active_button: Button = $VBoxContainer/ModeContainer/ActiveButton
@onready var pending_button: Button = $VBoxContainer/ModeContainer/PendingButton
@onready var history_button: Button = $VBoxContainer/ModeContainer/HistoryButton
@onready var quest_list: ItemList = $VBoxContainer/QuestList
@onready var quest_title: Label = $VBoxContainer/QuestDetail/QuestTitle
@onready var quest_type: Label = $VBoxContainer/QuestDetail/QuestType
@onready var quest_status: Label = $VBoxContainer/QuestDetail/QuestStatus
@onready var quest_description: Label = $VBoxContainer/QuestDetail/QuestDescription
@onready var quest_progress: Label = $VBoxContainer/QuestDetail/QuestProgress
@onready var quest_rewards: Label = $VBoxContainer/QuestDetail/QuestRewards
@onready var accept_button: Button = $VBoxContainer/QuestDetail/ActionButtonRow/AcceptButton
@onready var reject_button: Button = $VBoxContainer/QuestDetail/ActionButtonRow/RejectButton
@onready var complete_button: Button = $VBoxContainer/QuestDetail/ActionButtonRow/CompleteButton
@onready var friend_id_input: LineEdit = $VBoxContainer/CreateSection/FriendIdInput
@onready var title_input: LineEdit = $VBoxContainer/CreateSection/TitleInput
@onready var type_input: LineEdit = $VBoxContainer/CreateSection/TypeInput
@onready var desc_input: LineEdit = $VBoxContainer/CreateSection/DescInput
@onready var create_button: Button = $VBoxContainer/CreateSection/CreateButton
@onready var refresh_button: Button = $VBoxContainer/RefreshButton

var _current_quest_id: String = ""
var _current_mode: int = QuestMode.ACTIVE

func _ready() -> void:
	active_button.pressed.connect(_on_active_mode_pressed)
	pending_button.pressed.connect(_on_pending_mode_pressed)
	history_button.pressed.connect(_on_history_mode_pressed)
	refresh_button.pressed.connect(_on_refresh_pressed)
	create_button.pressed.connect(_on_create_pressed)
	quest_list.item_selected.connect(_on_quest_item_selected)
	accept_button.pressed.connect(_on_accept_pressed)
	reject_button.pressed.connect(_on_reject_pressed)
	complete_button.pressed.connect(_on_complete_pressed)
	FriendManager.collab_quests_active_loaded.connect(_on_active_loaded)
	FriendManager.collab_quests_pending_loaded.connect(_on_pending_loaded)
	FriendManager.collab_quests_history_loaded.connect(_on_history_loaded)
	FriendManager.collab_quest_created.connect(_on_quest_state_changed)
	FriendManager.collab_quest_accepted.connect(_on_quest_state_changed)
	FriendManager.collab_quest_rejected.connect(_on_quest_state_changed)
	FriendManager.collab_quest_completed.connect(_on_quest_state_changed)

func _on_active_mode_pressed() -> void:
	_current_mode = QuestMode.ACTIVE
	active_button.button_pressed = true
	pending_button.button_pressed = false
	history_button.button_pressed = false
	_refresh_list()

func _on_pending_mode_pressed() -> void:
	_current_mode = QuestMode.PENDING
	active_button.button_pressed = false
	pending_button.button_pressed = true
	history_button.button_pressed = false
	_refresh_list()

func _on_history_mode_pressed() -> void:
	_current_mode = QuestMode.HISTORY
	active_button.button_pressed = false
	pending_button.button_pressed = false
	history_button.button_pressed = true
	_refresh_list()

func _on_refresh_pressed() -> void:
	_refresh_list()

func _refresh_list() -> void:
	match _current_mode:
		QuestMode.ACTIVE:
			FriendManager.fetch_active_collab_quests()
		QuestMode.PENDING:
			FriendManager.fetch_pending_collab_quests()
		QuestMode.HISTORY:
			FriendManager.fetch_collab_quest_history()

func _on_active_loaded() -> void:
	if _current_mode == QuestMode.ACTIVE:
		_update_quest_list(FriendManager.get_active_collab_quests())

func _on_pending_loaded() -> void:
	if _current_mode == QuestMode.PENDING:
		_update_quest_list(FriendManager.get_pending_collab_quests())

func _on_history_loaded() -> void:
	if _current_mode == QuestMode.HISTORY:
		_update_quest_list(FriendManager.get_history_collab_quests())

func _on_quest_state_changed() -> void:
	_refresh_list()

func _update_quest_list(quests: Array) -> void:
	quest_list.clear()
	for quest in quests:
		var title: String = quest.get("title", "未知任务")
		var quest_type: String = quest.get("quest_type", "")
		var status: String = quest.get("status", "")
		var type_label: String = _get_type_label(quest_type)
		var status_label: String = _get_status_label(status)
		var display_text: String = "%s [%s] %s" % [title, type_label, status_label]
		quest_list.add_item(display_text)

func _on_quest_item_selected(index: int) -> void:
	var quests: Array = _get_current_quests()
	if index >= 0 and index < quests.size():
		var quest: Dictionary = quests[index]
		_current_quest_id = quest.get("quest_id", "")
		_update_quest_detail(quest)
		quest_selected.emit(_current_quest_id)

func _get_current_quests() -> Array:
	match _current_mode:
		QuestMode.ACTIVE:
			return FriendManager.get_active_collab_quests()
		QuestMode.PENDING:
			return FriendManager.get_pending_collab_quests()
		QuestMode.HISTORY:
			return FriendManager.get_history_collab_quests()
	return []

func _update_quest_detail(quest: Dictionary) -> void:
	if quest.is_empty():
		_clear_detail()
		return

	var title: String = quest.get("title", "未知任务")
	var quest_type: String = quest.get("quest_type", "")
	var status: String = quest.get("status", "")
	var description: String = quest.get("description", "")
	var progress: Dictionary = quest.get("progress", {})
	var rewards: Dictionary = quest.get("rewards", {})

	quest_title.text = title
	quest_type.text = "类型: %s" % _get_type_label(quest_type)
	quest_status.text = "状态: %s" % _get_status_label(status)
	quest_description.text = description
	quest_progress.text = "进度: %s" % _format_progress(progress)
	quest_rewards.text = "奖励: %s" % _format_rewards(rewards)

	_update_action_buttons(status)

func _clear_detail() -> void:
	quest_title.text = "选择任务查看详情"
	quest_type.text = "类型: --"
	quest_status.text = "状态: --"
	quest_description.text = ""
	quest_progress.text = "进度: --"
	quest_rewards.text = "奖励: --"
	_disable_all_action_buttons()

func _update_action_buttons(status: String) -> void:
	_disable_all_action_buttons()
	match status:
		"pending_invite":
			accept_button.disabled = false
			reject_button.disabled = false
		"active":
			complete_button.disabled = false
		"completed", "failed", "expired":
			pass

func _disable_all_action_buttons() -> void:
	accept_button.disabled = true
	reject_button.disabled = true
	complete_button.disabled = true

func _on_accept_pressed() -> void:
	if _current_quest_id != "":
		FriendManager.accept_collab_quest(_current_quest_id)

func _on_reject_pressed() -> void:
	if _current_quest_id != "":
		FriendManager.reject_collab_quest(_current_quest_id)

func _on_complete_pressed() -> void:
	if _current_quest_id != "":
		FriendManager.complete_collab_quest(_current_quest_id)

func _on_create_pressed() -> void:
	var friend_id: String = friend_id_input.text.strip_edges()
	var title: String = title_input.text.strip_edges()
	var quest_type: String = type_input.text.strip_edges()
	var description: String = desc_input.text.strip_edges()

	if friend_id == "" or title == "":
		return

	if quest_type == "":
		quest_type = "hunt"

	FriendManager.create_collab_quest(friend_id, quest_type, title, description, {}, {}, "")

	friend_id_input.text = ""
	title_input.text = ""
	type_input.text = ""
	desc_input.text = ""

func _get_type_label(quest_type: String) -> String:
	var type_map: Dictionary = {
		"hunt": "狩猎",
		"explore": "探索",
		"collect": "采集",
		"escort": "护送",
		"challenge": "挑战"
	}
	return type_map.get(quest_type, "未知")

func _get_status_label(status: String) -> String:
	var status_map: Dictionary = {
		"pending_invite": "待接受",
		"active": "进行中",
		"completed": "已完成",
		"failed": "失败",
		"expired": "已过期"
	}
	return status_map.get(status, "未知")

func _format_progress(progress: Dictionary) -> String:
	if progress.is_empty():
		return "--"
	var texts: Array = []
	for key in progress.keys():
		var value = progress.get(key)
		texts.append("%s: %s" % [key, str(value)])
	return ", ".join(texts)

func _format_rewards(rewards: Dictionary) -> String:
	if rewards.is_empty():
		return "无"
	var texts: Array = []
	if rewards.has("experience_points"):
		texts.append("经验 %d" % rewards.get("experience_points", 0))
	if rewards.has("gold"):
		texts.append("金币 %d" % rewards.get("gold", 0))
	if rewards.has("contribution_points"):
		texts.append("贡献 %d" % rewards.get("contribution_points", 0))
	if rewards.has("reputation"):
		texts.append("声望 %d" % rewards.get("reputation", 0))
	if texts.size() == 0:
		return "无"
	return ", ".join(texts)

func refresh() -> void:
	_refresh_list()

func clear() -> void:
	quest_list.clear()
	_clear_detail()
	friend_id_input.text = ""
	title_input.text = ""
	type_input.text = ""
	desc_input.text = ""
	_current_quest_id = ""
	_current_mode = QuestMode.ACTIVE
