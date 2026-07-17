extends Node

signal guild_info_loaded
signal guild_members_loaded
signal guild_created
signal guild_joined
signal guild_left
signal guild_quests_loaded
signal guild_quest_progress_updated
signal guild_quest_reward_claimed
signal guild_error(error_code: String, message: String)

# 公会战相关信号
signal guild_wars_loaded
signal guild_war_history_loaded
signal guild_war_detail_loaded
signal guild_war_scoreboard_loaded
signal guild_war_declared
signal guild_war_accepted
signal guild_war_cancelled
signal guild_war_joined
signal guild_war_completed

var _guild_info: Dictionary = {}
var _guild_members: Array = []
var _guild_quests: Array = []
var _guild_quest_progress: Dictionary = {}
var _is_loading: bool = false

# 公会战相关状态
var _active_wars: Array = []
var _war_history: Array = []
var _current_war_detail: Dictionary = {}
var _war_scoreboard: Dictionary = {}

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)

func _on_auth_error(request_id: String, message: String) -> void:
	guild_error.emit("AUTH_ERROR", message)

func fetch_my_guild() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/guild")

	if result.get("success", false):
		_guild_info = result.get("data", {})
		guild_info_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_guild_info(guild_id: String) -> void:
	if guild_id == "":
		guild_error.emit("INVALID_GUILD_ID", "公会ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.get("/guild/%s" % guild_id)

	if result.get("success", false):
		_guild_info = result.get("data", {})
		guild_info_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_guild_members(guild_id: String) -> void:
	if guild_id == "":
		guild_error.emit("INVALID_GUILD_ID", "公会ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.get("/guild/%s/members" % guild_id)

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_guild_members = data.get("items", [])
		guild_members_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func create_guild(name: String) -> void:
	if name == "":
		guild_error.emit("INVALID_GUILD_NAME", "公会名称不能为空")
		return

	_set_loading(true)
	var body: Dictionary = {"name": name}
	var result: Dictionary = APIManager.post("/guild", body)

	if result.get("success", false):
		_guild_info = result.get("data", {})
		guild_created.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func join_guild(guild_id: String) -> void:
	if guild_id == "":
		guild_error.emit("INVALID_GUILD_ID", "公会ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/guild/%s/join" % guild_id)

	if result.get("success", false):
		guild_joined.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func leave_guild() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.post("/guild/leave")

	if result.get("success", false):
		_guild_info.clear()
		_guild_members.clear()
		guild_left.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_guild_quests(guild_id: String) -> void:
	if guild_id == "":
		guild_error.emit("INVALID_GUILD_ID", "公会ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.get("/guild/%s/quests" % guild_id)

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_guild_quests = data.get("items", [])
		guild_quests_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_guild_quest_detail(guild_id: String, quest_key: String) -> Dictionary:
	if guild_id == "" or quest_key == "":
		guild_error.emit("INVALID_PARAMS", "参数不能为空")
		return {}

	var result: Dictionary = APIManager.get("/guild/%s/quests/%s" % [guild_id, quest_key])

	if result.get("success", false):
		return result.get("data", {})
	else:
		_handle_error(result)
		return {}

func fetch_guild_quest_progress(guild_id: String, quest_key: String) -> Dictionary:
	if guild_id == "" or quest_key == "":
		guild_error.emit("INVALID_PARAMS", "参数不能为空")
		return {}

	var result: Dictionary = APIManager.get("/guild/%s/quests/%s/progress" % [guild_id, quest_key])

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_guild_quest_progress[quest_key] = data
		return data
	else:
		_handle_error(result)
		return {}

func update_guild_quest_progress(guild_id: String, quest_key: String, progress_data: Dictionary) -> void:
	if guild_id == "" or quest_key == "":
		guild_error.emit("INVALID_PARAMS", "参数不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.put("/guild/%s/quests/%s/progress" % [guild_id, quest_key], progress_data)

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_guild_quest_progress[quest_key] = data
		guild_quest_progress_updated.emit(quest_key, data)
	else:
		_handle_error(result)

	_set_loading(false)

func claim_guild_quest_reward(guild_id: String, quest_key: String) -> void:
	if guild_id == "" or quest_key == "":
		guild_error.emit("INVALID_PARAMS", "参数不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/guild/%s/quests/%s/reward" % [guild_id, quest_key])

	if result.get("success", false):
		guild_quest_reward_claimed.emit(quest_key)
	else:
		_handle_error(result)

	_set_loading(false)

func get_guild_quests() -> Array:
	return _guild_quests.duplicate()

func get_guild_quest_progress(quest_key: String) -> Dictionary:
	return _guild_quest_progress.get(quest_key, {})

func get_guild_info() -> Dictionary:
	return _guild_info.duplicate()

func get_guild_member_count() -> int:
	return _guild_members.size()

# === 公会战相关 API ===

func declare_war(defender_guild_id: String, war_type: String, reward_config: Dictionary) -> void:
	if defender_guild_id == "":
		guild_error.emit("INVALID_GUILD_ID", "目标公会ID不能为空")
		return
	if war_type == "":
		war_type = "territory"

	_set_loading(true)
	var body: Dictionary = {
		"defender_guild_id": defender_guild_id,
		"war_type": war_type,
		"reward_config": reward_config
	}
	var result: Dictionary = APIManager.post("/guild/wars", body)

	if result.get("success", false):
		_current_war_detail = result.get("data", {})
		guild_war_declared.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func accept_war(war_id: String) -> void:
	if war_id == "":
		guild_error.emit("INVALID_WAR_ID", "战争ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/guild/wars/%s/accept" % war_id)

	if result.get("success", false):
		_current_war_detail = result.get("data", {})
		guild_war_accepted.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func cancel_war(war_id: String) -> void:
	if war_id == "":
		guild_error.emit("INVALID_WAR_ID", "战争ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/guild/wars/%s/cancel" % war_id)

	if result.get("success", false):
		_current_war_detail = result.get("data", {})
		guild_war_cancelled.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_active_wars() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/guild/wars/active")

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_active_wars = data.get("wars", data.get("items", []))
		guild_wars_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_war_history(limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/guild/wars/history?limit=%d&offset=%d" % [limit, offset])

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_war_history = data.get("wars", data.get("items", []))
		guild_war_history_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_war_detail(war_id: String) -> void:
	if war_id == "":
		guild_error.emit("INVALID_WAR_ID", "战争ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.get("/guild/wars/%s" % war_id)

	if result.get("success", false):
		_current_war_detail = result.get("data", {})
		guild_war_detail_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func join_war(war_id: String, guild_id: String) -> void:
	if war_id == "" or guild_id == "":
		guild_error.emit("INVALID_PARAMS", "战争ID和公会ID不能为空")
		return

	_set_loading(true)
	var body: Dictionary = {"guild_id": guild_id}
	var result: Dictionary = APIManager.post("/guild/wars/%s/join" % war_id, body)

	if result.get("success", false):
		guild_war_joined.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_war_scoreboard(war_id: String) -> void:
	if war_id == "":
		guild_error.emit("INVALID_WAR_ID", "战争ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.get("/guild/wars/%s/scoreboard" % war_id)

	if result.get("success", false):
		_war_scoreboard = result.get("data", {})
		guild_war_scoreboard_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func complete_war(war_id: String) -> void:
	if war_id == "":
		guild_error.emit("INVALID_WAR_ID", "战争ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/guild/wars/%s/complete" % war_id)

	if result.get("success", false):
		_current_war_detail = result.get("data", {})
		guild_war_completed.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func get_active_wars() -> Array:
	return _active_wars.duplicate()

func get_war_history() -> Array:
	return _war_history.duplicate()

func get_war_detail() -> Dictionary:
	return _current_war_detail.duplicate()

func get_war_scoreboard() -> Dictionary:
	return _war_scoreboard.duplicate()

func is_loading() -> bool:
	return _is_loading

func _handle_error(result: Dictionary) -> void:
	var err_code: String = result.get("code", "UNKNOWN_ERROR")
	var err_message: String = result.get("message", "操作失败")
	guild_error.emit(err_code, err_message)

func _set_loading(loading: bool) -> void:
	_is_loading = loading

func reset() -> void:
	_guild_info.clear()
	_guild_members.clear()
	_guild_quests.clear()
	_guild_quest_progress.clear()
	_active_wars.clear()
	_war_history.clear()
	_current_war_detail.clear()
	_war_scoreboard.clear()
	_is_loading = false