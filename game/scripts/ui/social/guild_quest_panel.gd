extends Control

signal close_pressed
signal quest_selected(quest_key: String)

@onready var quest_list: ItemList = $VBoxContainer/QuestList
@onready var quest_name_label: Label = $VBoxContainer/QuestDetail/QuestName
@onready var quest_description_label: Label = $VBoxContainer/QuestDetail/QuestDescription
@onready var progress_bar: ProgressBar = $VBoxContainer/QuestDetail/ProgressBar
@onready var progress_label: Label = $VBoxContainer/QuestDetail/ProgressLabel
@onready var reward_label: Label = $VBoxContainer/QuestDetail/RewardLabel
@onready var action_button: Button = $VBoxContainer/QuestDetail/ActionButton
@onready var refresh_button: Button = $VBoxContainer/RefreshButton

var _current_quest_key: String = ""
var _current_guild_id: String = ""

func _ready() -> void:
	refresh_button.pressed.connect(_on_refresh_pressed)
	quest_list.item_selected.connect(_on_quest_item_selected)
	action_button.pressed.connect(_on_action_pressed)
	GuildManager.guild_quests_loaded.connect(_on_quests_loaded)
	GuildManager.guild_quest_progress_updated.connect(_on_progress_updated)
	GuildManager.guild_quest_reward_claimed.connect(_on_reward_claimed)

func set_guild_id(guild_id: String) -> void:
	_current_guild_id = guild_id
	if guild_id != "":
		GuildManager.fetch_guild_quests(guild_id)

func _on_refresh_pressed() -> void:
	if _current_guild_id != "":
		GuildManager.fetch_guild_quests(_current_guild_id)

func _on_quest_item_selected(index: int) -> void:
	var quests: Array = GuildManager.get_guild_quests()
	if index >= 0 and index < quests.size():
		var quest: Dictionary = quests[index]
		_current_quest_key = quest.get("quest_key", "")
		_update_quest_detail(quest)
		quest_selected.emit(_current_quest_key)

func _update_quest_detail(quest: Dictionary) -> void:
	var quest_name: String = quest.get("name", "未知任务")
	var quest_desc: String = quest.get("description", "")
	var quest_type: String = quest.get("quest_type", "")
	var status: String = quest.get("status", "")

	quest_name_label.text = "%s (%s)" % [quest_name, _get_type_label(quest_type)]
	quest_description_label.text = quest_desc

	var progress: Dictionary = GuildManager.get_guild_quest_progress(_current_quest_key)
	_update_progress_display(progress, quest)

	var rewards: Dictionary = quest.get("rewards", {})
	_update_reward_display(rewards)

	_update_action_button(status, progress)

func _update_progress_display(progress: Dictionary, quest: Dictionary) -> void:
	var current: int = progress.get("current", 0)
	var total: int = quest.get("target_count", 100)

	if total > 0:
		var percentage: int = int((current / total) * 100)
		progress_bar.value = percentage
		progress_label.text = "进度: %d/%d" % [current, total]
	else:
		progress_bar.value = 0
		progress_label.text = "进度: --"

func _update_reward_display(rewards: Dictionary) -> void:
	var reward_texts: Array = []

	if rewards.has("experience_points"):
		reward_texts.append("经验 %d" % rewards.get("experience_points", 0))
	if rewards.has("gold"):
		reward_texts.append("金币 %d" % rewards.get("gold", 0))
	if rewards.has("contribution_points"):
		reward_texts.append("贡献 %d" % rewards.get("contribution_points", 0))
	if rewards.has("reputation"):
		reward_texts.append("声望 %d" % rewards.get("reputation", 0))

	if reward_texts.size() > 0:
		reward_label.text = "奖励: %s" % ", ".join(reward_texts)
	else:
		reward_label.text = "奖励: 无"

func _update_action_button(status: String, progress: Dictionary) -> void:
	if status == "completed":
		action_button.text = "领取奖励"
		action_button.disabled = false
	elif status == "active":
		var current: int = progress.get("current", 0)
		var total: int = progress.get("target_count", 100)
		if current >= total:
			action_button.text = "完成任务"
			action_button.disabled = false
		else:
			action_button.text = "进行中..."
			action_button.disabled = true
	else:
		action_button.text = "未开始"
		action_button.disabled = true

func _on_action_pressed() -> void:
	if _current_guild_id == "" or _current_quest_key == "":
		return

	var progress: Dictionary = GuildManager.get_guild_quest_progress(_current_quest_key)
	var current: int = progress.get("current", 0)
	var total: int = progress.get("target_count", 100)

	if current >= total:
		GuildManager.claim_guild_quest_reward(_current_guild_id, _current_quest_key)

func _on_quests_loaded() -> void:
	_update_quest_list()

func _on_progress_updated(quest_key: String, progress_data: Dictionary) -> void:
	if quest_key == _current_quest_key:
		var quests: Array = GuildManager.get_guild_quests()
		for quest in quests:
			if quest.get("quest_key", "") == quest_key:
				_update_quest_detail(quest)
				break

func _on_reward_claimed(quest_key: String) -> void:
	if quest_key == _current_quest_key:
		action_button.text = "已领取"
		action_button.disabled = true
		GuildManager.fetch_guild_quests(_current_guild_id)

func _update_quest_list() -> void:
	quest_list.clear()
	var quests: Array = GuildManager.get_guild_quests()

	for quest in quests:
		var name: String = quest.get("name", "未知任务")
		var status: String = quest.get("status", "unknown")
		var type_label: String = _get_type_label(quest.get("quest_type", ""))
		var status_label: String = _get_status_label(status)

		var display_text: String = "%s [%s] %s" % [name, type_label, status_label]
		quest_list.add_item(display_text)

func _get_type_label(quest_type: String) -> String:
	var type_map: Dictionary = {
		"collect": "采集",
		"kill": "击杀",
		"deliver": "运送",
		"explore": "探索",
		"defend": "防御",
		"craft": "制作"
	}
	return type_map.get(quest_type, "未知")

func _get_status_label(status: String) -> String:
	var status_map: Dictionary = {
		"active": "进行中",
		"completed": "已完成",
		"failed": "失败",
		"expired": "已过期"
	}
	return status_map.get(status, "未知")

func refresh() -> void:
	if _current_guild_id != "":
		GuildManager.fetch_guild_quests(_current_guild_id)

func clear() -> void:
	quest_list.clear()
	quest_name_label.text = "选择任务查看详情"
	quest_description_label.text = ""
	progress_bar.value = 0
	progress_label.text = "进度: 0/100"
	reward_label.text = "奖励: "
	action_button.text = "领取奖励"
	action_button.disabled = true
	_current_quest_key = ""