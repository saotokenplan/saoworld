extends Node

func test_signals_declared() -> void:
	assert(GuildManager.has_signal("guild_info_loaded"))
	assert(GuildManager.has_signal("guild_members_loaded"))
	assert(GuildManager.has_signal("guild_created"))
	assert(GuildManager.has_signal("guild_joined"))
	assert(GuildManager.has_signal("guild_left"))
	assert(GuildManager.has_signal("guild_quests_loaded"))
	assert(GuildManager.has_signal("guild_quest_progress_updated"))
	assert(GuildManager.has_signal("guild_quest_reward_claimed"))
	assert(GuildManager.has_signal("guild_error"))

func test_initial_state() -> void:
	assert(GuildManager._guild_info == {})
	assert(GuildManager._guild_members == [])
	assert(GuildManager._guild_quests == [])
	assert(GuildManager._guild_quest_progress == {})
	assert(GuildManager._is_loading == false)

func test_is_loading() -> void:
	assert(GuildManager.is_loading() == false)

func test_get_guild_info() -> void:
	var result: Dictionary = GuildManager.get_guild_info()
	assert(typeof(result) == TYPE_DICTIONARY)

func test_get_guild_member_count() -> void:
	assert(GuildManager.get_guild_member_count() == 0)

func test_get_guild_quests() -> void:
	var result: Array = GuildManager.get_guild_quests()
	assert(typeof(result) == TYPE_ARRAY)

func test_get_guild_quest_progress() -> void:
	var result: Dictionary = GuildManager.get_guild_quest_progress("test_key")
	assert(typeof(result) == TYPE_DICTIONARY)
	assert(result == {})

func test_reset() -> void:
	GuildManager._guild_info = {"name": "Test Guild"}
	GuildManager._guild_members = [{"player_id": "1"}]
	GuildManager._guild_quests = [{"quest_key": "q1"}]
	GuildManager._guild_quest_progress = {"q1": {"current": 50}}
	GuildManager._is_loading = true

	GuildManager.reset()

	assert(GuildManager._guild_info == {})
	assert(GuildManager._guild_members == [])
	assert(GuildManager._guild_quests == [])
	assert(GuildManager._guild_quest_progress == {})
	assert(GuildManager._is_loading == false)

func test_fetch_guild_quests_empty_guild_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	GuildManager.fetch_guild_quests("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_GUILD_ID")

func test_update_quest_progress_empty_params() -> void:
	var error_emitted: bool = false

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
	)

	GuildManager.update_guild_quest_progress("", "q1", {})

	conn.disconnect()

	assert(error_emitted == true)