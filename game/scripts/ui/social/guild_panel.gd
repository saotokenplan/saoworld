extends Control

signal close_pressed

@onready var tab_container: TabContainer = $TabContainer
@onready var guild_name_label: Label = $TabContainer/GuildInfoTab/VBoxContainer/GuildNameLabel
@onready var guild_description: Label = $TabContainer/GuildInfoTab/VBoxContainer/GuildDescription
@onready var guild_stats: Label = $TabContainer/GuildInfoTab/VBoxContainer/GuildStats
@onready var guild_announcement: Label = $TabContainer/GuildInfoTab/VBoxContainer/GuildAnnouncement
@onready var close_button: Button = $TabContainer/GuildInfoTab/VBoxContainer/CloseButton
@onready var member_list: ItemList = $TabContainer/MembersTab/VBoxContainer/MemberList
@onready var refresh_button: Button = $TabContainer/MembersTab/VBoxContainer/RefreshButton
@onready var guild_quest_panel: Control = $TabContainer/QuestTab/GuildQuestPanel
@onready var guild_war_panel: Control = $TabContainer/WarTab/GuildWarPanel

var _current_guild_id: String = ""

func _ready() -> void:
	close_button.pressed.connect(_on_close_pressed)
	refresh_button.pressed.connect(_on_refresh_members_pressed)
	GuildManager.guild_info_loaded.connect(_on_guild_info_loaded)
	GuildManager.guild_members_loaded.connect(_on_members_loaded)
	GuildManager.guild_quests_loaded.connect(_on_quests_loaded)

func set_guild_id(guild_id: String) -> void:
	_current_guild_id = guild_id
	if guild_war_panel:
		guild_war_panel.set_guild_id(guild_id)

func refresh() -> void:
	if _current_guild_id != "":
		GuildManager.fetch_guild_info(_current_guild_id)
		GuildManager.fetch_guild_members(_current_guild_id)
		GuildManager.fetch_guild_quests(_current_guild_id)
		guild_war_panel.refresh()

func _on_close_pressed() -> void:
	close_pressed.emit()

func _on_refresh_members_pressed() -> void:
	if _current_guild_id != "":
		GuildManager.fetch_guild_members(_current_guild_id)

func _on_guild_info_loaded() -> void:
	var info: Dictionary = GuildManager._guild_info
	guild_name_label.text = info.get("name", "未知公会")
	guild_description.text = info.get("description", "暂无描述")
	var level: int = info.get("level", 1)
	var member_count: int = info.get("member_count", 0)
	var max_members: int = info.get("max_members", 50)
	guild_stats.text = "等级: %d | 成员: %d/%d" % [level, member_count, max_members]
	guild_announcement.text = info.get("announcement", "暂无公告")

func _on_members_loaded() -> void:
	member_list.clear()
	var members: Array = GuildManager._guild_members
	for member in members:
		var display_name: String = member.get("display_name", member.get("player_id", ""))
		var role: String = member.get("role", "member")
		var role_label: String = _get_role_label(role)
		var label: String = "%s [%s]" % [display_name, role_label]
		member_list.add_item(label)

func _on_quests_loaded() -> void:
	guild_quest_panel.refresh()

func _get_role_label(role: String) -> String:
	var role_map: Dictionary = {
		"leader": "会长",
		"officer": "官员",
		"member": "成员"
	}
	return role_map.get(role, "成员")