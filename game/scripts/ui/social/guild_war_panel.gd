extends Control

signal close_pressed
signal war_selected(war_id: String)

enum WarMode { ACTIVE = 0, HISTORY = 1 }

@onready var active_button: Button = $VBoxContainer/ModeContainer/ActiveButton
@onready var history_button: Button = $VBoxContainer/ModeContainer/HistoryButton
@onready var war_list: ItemList = $VBoxContainer/WarList
@onready var war_title: Label = $VBoxContainer/WarDetail/WarTitle
@onready var war_status: Label = $VBoxContainer/WarDetail/WarStatus
@onready var war_type: Label = $VBoxContainer/WarDetail/WarType
@onready var war_score: Label = $VBoxContainer/WarDetail/WarScore
@onready var war_reward: Label = $VBoxContainer/WarDetail/WarReward
@onready var accept_button: Button = $VBoxContainer/WarDetail/ActionButtonRow/AcceptButton
@onready var cancel_button: Button = $VBoxContainer/WarDetail/ActionButtonRow/CancelButton
@onready var join_button: Button = $VBoxContainer/WarDetail/ActionButtonRow/JoinButton
@onready var complete_button: Button = $VBoxContainer/WarDetail/ActionButtonRow/CompleteButton
@onready var scoreboard_list: ItemList = $VBoxContainer/ScoreboardList
@onready var refresh_button: Button = $VBoxContainer/RefreshButton

var _current_war_id: String = ""
var _current_guild_id: String = ""
var _current_mode: int = WarMode.ACTIVE

func _ready() -> void:
	active_button.pressed.connect(_on_active_mode_pressed)
	history_button.pressed.connect(_on_history_mode_pressed)
	refresh_button.pressed.connect(_on_refresh_pressed)
	war_list.item_selected.connect(_on_war_item_selected)
	accept_button.pressed.connect(_on_accept_pressed)
	cancel_button.pressed.connect(_on_cancel_pressed)
	join_button.pressed.connect(_on_join_pressed)
	complete_button.pressed.connect(_on_complete_pressed)
	GuildManager.guild_wars_loaded.connect(_on_wars_loaded)
	GuildManager.guild_war_history_loaded.connect(_on_history_loaded)
	GuildManager.guild_war_detail_loaded.connect(_on_detail_loaded)
	GuildManager.guild_war_scoreboard_loaded.connect(_on_scoreboard_loaded)
	GuildManager.guild_war_accepted.connect(_on_war_state_changed)
	GuildManager.guild_war_cancelled.connect(_on_war_state_changed)
	GuildManager.guild_war_joined.connect(_on_war_state_changed)
	GuildManager.guild_war_completed.connect(_on_war_state_changed)
	GuildManager.guild_war_declared.connect(_on_war_state_changed)

func set_guild_id(guild_id: String) -> void:
	_current_guild_id = guild_id

func _on_active_mode_pressed() -> void:
	_current_mode = WarMode.ACTIVE
	active_button.button_pressed = true
	history_button.button_pressed = false
	_refresh_list()

func _on_history_mode_pressed() -> void:
	_current_mode = WarMode.HISTORY
	active_button.button_pressed = false
	history_button.button_pressed = true
	_refresh_list()

func _on_refresh_pressed() -> void:
	_refresh_list()

func _refresh_list() -> void:
	if _current_mode == WarMode.ACTIVE:
		GuildManager.fetch_active_wars()
	else:
		GuildManager.fetch_war_history()

func _on_wars_loaded() -> void:
	_update_war_list(GuildManager.get_active_wars())

func _on_history_loaded() -> void:
	_update_war_list(GuildManager.get_war_history())

func _on_detail_loaded() -> void:
	_update_war_detail(GuildManager.get_war_detail())

func _on_scoreboard_loaded() -> void:
	_update_scoreboard(GuildManager.get_war_scoreboard())

func _on_war_state_changed() -> void:
	_refresh_list()

func _update_war_list(wars: Array) -> void:
	war_list.clear()
	for war in wars:
		var challenger: String = war.get("challenger_guild_id", "未知")
		var defender: String = war.get("defender_guild_id", "未知")
		var status: String = war.get("status", "")
		var war_type: String = war.get("war_type", "")
		var status_label: String = _get_status_label(status)
		var type_label: String = _get_type_label(war_type)
		var display_text: String = "%s vs %s [%s] %s" % [challenger, defender, type_label, status_label]
		war_list.add_item(display_text)

func _on_war_item_selected(index: int) -> void:
	var wars: Array = []
	if _current_mode == WarMode.ACTIVE:
		wars = GuildManager.get_active_wars()
	else:
		wars = GuildManager.get_war_history()

	if index >= 0 and index < wars.size():
		var war: Dictionary = wars[index]
		_current_war_id = war.get("war_id", "")
		_update_war_detail(war)
		war_selected.emit(_current_war_id)
		if _current_war_id != "":
			GuildManager.fetch_war_scoreboard(_current_war_id)

func _update_war_detail(war: Dictionary) -> void:
	if war.is_empty():
		war_title.text = "选择战争查看详情"
		war_status.text = "状态: --"
		war_type.text = "类型: --"
		war_score.text = "比分: 0 : 0"
		war_reward.text = "奖励: --"
		_disable_all_action_buttons()
		return

	var challenger: String = war.get("challenger_guild_id", "未知")
	var defender: String = war.get("defender_guild_id", "未知")
	var status: String = war.get("status", "")
	var war_type: String = war.get("war_type", "")
	var challenger_score: int = war.get("challenger_score", 0)
	var defender_score: int = war.get("defender_score", 0)
	var reward: Dictionary = war.get("reward", {})

	war_title.text = "%s vs %s" % [challenger, defender]
	war_status.text = "状态: %s" % _get_status_label(status)
	war_type.text = "类型: %s" % _get_type_label(war_type)
	war_score.text = "比分: %d : %d" % [challenger_score, defender_score]
	war_reward.text = "奖励: %s" % _format_reward(reward)

	_update_action_buttons(status)

func _update_action_buttons(status: String) -> void:
	_disable_all_action_buttons()
	match status:
		"declared":
			accept_button.disabled = false
			cancel_button.disabled = false
		"accepted":
			join_button.disabled = false
			cancel_button.disabled = false
		"in_progress":
			join_button.disabled = false
			complete_button.disabled = false
		"completed", "cancelled":
			pass

func _disable_all_action_buttons() -> void:
	accept_button.disabled = true
	cancel_button.disabled = true
	join_button.disabled = true
	complete_button.disabled = true

func _update_scoreboard(scoreboard: Dictionary) -> void:
	scoreboard_list.clear()
	var challenger_participants: Array = scoreboard.get("challenger_participants", [])
	var defender_participants: Array = scoreboard.get("defender_participants", [])

	scoreboard_list.add_item("=== 宣战方 ===")
	for participant in challenger_participants:
		var player_id: String = participant.get("player_id", "未知")
		var kills: int = participant.get("kills", 0)
		var deaths: int = participant.get("deaths", 0)
		var contribution: int = participant.get("contribution_score", 0)
		scoreboard_list.add_item("%s | 击杀 %d | 死亡 %d | 贡献 %d" % [player_id, kills, deaths, contribution])

	scoreboard_list.add_item("=== 防守方 ===")
	for participant in defender_participants:
		var player_id: String = participant.get("player_id", "未知")
		var kills: int = participant.get("kills", 0)
		var deaths: int = participant.get("deaths", 0)
		var contribution: int = participant.get("contribution_score", 0)
		scoreboard_list.add_item("%s | 击杀 %d | 死亡 %d | 贡献 %d" % [player_id, kills, deaths, contribution])

func _on_accept_pressed() -> void:
	if _current_war_id != "":
		GuildManager.accept_war(_current_war_id)

func _on_cancel_pressed() -> void:
	if _current_war_id != "":
		GuildManager.cancel_war(_current_war_id)

func _on_join_pressed() -> void:
	if _current_war_id != "" and _current_guild_id != "":
		GuildManager.join_war(_current_war_id, _current_guild_id)

func _on_complete_pressed() -> void:
	if _current_war_id != "":
		GuildManager.complete_war(_current_war_id)

func _get_status_label(status: String) -> String:
	var status_map: Dictionary = {
		"declared": "已宣战",
		"accepted": "已接受",
		"in_progress": "进行中",
		"completed": "已完成",
		"cancelled": "已取消"
	}
	return status_map.get(status, "未知")

func _get_type_label(war_type: String) -> String:
	var type_map: Dictionary = {
		"territory": "领土战",
		"resource": "资源战",
		"honor": "荣誉战"
	}
	return type_map.get(war_type, "未知")

func _format_reward(reward: Dictionary) -> String:
	if reward.is_empty():
		return "无"
	var texts: Array = []
	if reward.has("experience_points"):
		texts.append("经验 %d" % reward.get("experience_points", 0))
	if reward.has("gold"):
		texts.append("金币 %d" % reward.get("gold", 0))
	if reward.has("contribution_points"):
		texts.append("贡献 %d" % reward.get("contribution_points", 0))
	if reward.has("reputation"):
		texts.append("声望 %d" % reward.get("reputation", 0))
	if texts.size() == 0:
		return "无"
	return ", ".join(texts)

func refresh() -> void:
	_refresh_list()

func clear() -> void:
	war_list.clear()
	scoreboard_list.clear()
	war_title.text = "选择战争查看详情"
	war_status.text = "状态: --"
	war_type.text = "类型: --"
	war_score.text = "比分: 0 : 0"
	war_reward.text = "奖励: --"
	_disable_all_action_buttons()
	_current_war_id = ""
	_current_mode = WarMode.ACTIVE
