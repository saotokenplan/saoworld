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

# === 公会战相关测试 ===

func test_war_signals_declared() -> void:
	assert(GuildManager.has_signal("guild_wars_loaded"))
	assert(GuildManager.has_signal("guild_war_history_loaded"))
	assert(GuildManager.has_signal("guild_war_detail_loaded"))
	assert(GuildManager.has_signal("guild_war_scoreboard_loaded"))
	assert(GuildManager.has_signal("guild_war_declared"))
	assert(GuildManager.has_signal("guild_war_accepted"))
	assert(GuildManager.has_signal("guild_war_cancelled"))
	assert(GuildManager.has_signal("guild_war_joined"))
	assert(GuildManager.has_signal("guild_war_completed"))

func test_war_initial_state() -> void:
	GuildManager.reset()
	assert(GuildManager._active_wars == [])
	assert(GuildManager._war_history == [])
	assert(GuildManager._current_war_detail == {})
	assert(GuildManager._war_scoreboard == {})
	GuildManager.reset()

func test_get_active_wars_returns_empty_initially() -> void:
	GuildManager.reset()
	var result: Array = GuildManager.get_active_wars()
	assert(typeof(result) == TYPE_ARRAY)
	assert(result == [])
	GuildManager.reset()

func test_get_war_history_returns_empty_initially() -> void:
	GuildManager.reset()
	var result: Array = GuildManager.get_war_history()
	assert(typeof(result) == TYPE_ARRAY)
	assert(result == [])
	GuildManager.reset()

func test_get_war_detail_returns_empty_initially() -> void:
	GuildManager.reset()
	var result: Dictionary = GuildManager.get_war_detail()
	assert(typeof(result) == TYPE_DICTIONARY)
	assert(result == {})
	GuildManager.reset()

func test_get_war_scoreboard_returns_empty_initially() -> void:
	GuildManager.reset()
	var result: Dictionary = GuildManager.get_war_scoreboard()
	assert(typeof(result) == TYPE_DICTIONARY)
	assert(result == {})
	GuildManager.reset()

func test_getters_return_duplicates() -> void:
	GuildManager.reset()
	GuildManager._active_wars = [{"war_id": "w1"}]
	GuildManager._war_history = [{"war_id": "w2"}]
	GuildManager._current_war_detail = {"war_id": "w3"}
	GuildManager._war_scoreboard = {"challenger_participants": []}

	var active: Array = GuildManager.get_active_wars()
	var history: Array = GuildManager.get_war_history()
	var detail: Dictionary = GuildManager.get_war_detail()
	var scoreboard: Dictionary = GuildManager.get_war_scoreboard()

	active[0]["war_id"] = "modified"
	history[0]["war_id"] = "modified"
	detail["war_id"] = "modified"
	scoreboard["challenger_participants"] = "modified"

	assert(GuildManager._active_wars[0].get("war_id", "") == "w1", "get_active_wars 应返回副本")
	assert(GuildManager._war_history[0].get("war_id", "") == "w2", "get_war_history 应返回副本")
	assert(GuildManager._current_war_detail.get("war_id", "") == "w3", "get_war_detail 应返回副本")
	assert(GuildManager._war_scoreboard.get("challenger_participants", []) == [], "get_war_scoreboard 应返回副本")
	GuildManager.reset()

func test_war_reset_clears_new_fields() -> void:
	GuildManager._active_wars = [{"war_id": "w1"}]
	GuildManager._war_history = [{"war_id": "w2"}]
	GuildManager._current_war_detail = {"war_id": "w3"}
	GuildManager._war_scoreboard = {"challenger_participants": []}
	GuildManager._is_loading = true

	GuildManager.reset()

	assert(GuildManager._active_wars == [])
	assert(GuildManager._war_history == [])
	assert(GuildManager._current_war_detail == {})
	assert(GuildManager._war_scoreboard == {})
	assert(GuildManager._is_loading == false)

func test_declare_war_empty_defender_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	GuildManager.declare_war("", "territory", {})

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_GUILD_ID")

func test_accept_war_empty_war_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	GuildManager.accept_war("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_WAR_ID")

func test_cancel_war_empty_war_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	GuildManager.cancel_war("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_WAR_ID")

func test_fetch_war_detail_empty_war_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	GuildManager.fetch_war_detail("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_WAR_ID")

func test_join_war_empty_war_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	GuildManager.join_war("", "guild_001")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_PARAMS")

func test_join_war_empty_guild_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	GuildManager.join_war("war_001", "")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_PARAMS")

func test_fetch_war_scoreboard_empty_war_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	GuildManager.fetch_war_scoreboard("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_WAR_ID")

func test_complete_war_empty_war_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = GuildManager.guild_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	GuildManager.complete_war("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_WAR_ID")