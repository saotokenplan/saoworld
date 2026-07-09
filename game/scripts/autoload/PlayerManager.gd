extends Node

signal player_info_loaded
signal player_quests_loaded
signal player_regions_loaded
signal player_error(error_code: String, message: String)
signal auth_error(message: String)
signal loading_changed(is_loading: bool)
signal quest_accepted(quest_id: String)
signal quest_completed(quest_id: String)
signal quest_progress_updated(quest_id: String)
signal quest_failed(quest_id: String)
signal quest_detail_loaded(quest_id: String)

var player_info: Dictionary = {}
var player_quests: Array[Dictionary] = []
var player_regions: Array[Dictionary] = []
var is_loading: bool = false
var last_error: Dictionary = {}
var schema_version: int = 1

const QUEST_STATUS: Dictionary = {
	"available": {"name": "可接取", "color": "#2196F3"},
	"active": {"name": "进行中", "color": "#FF9800"},
	"completed": {"name": "已完成", "color": "#4CAF50"},
	"failed": {"name": "失败", "color": "#F44336"}
}

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)

func _on_auth_error(request_id: String, message: String) -> void:
	auth_error.emit(message)

func fetch_player_info() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/player/info")
	
	if result.get("success", false):
		_handle_player_info_success(result)
	else:
		_handle_player_error(result)
	
	_set_loading(false)

func _handle_player_info_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	player_info = data
	last_error.clear()
	
	if player_info.has("player_id"):
		GameState.player_id = player_info["player_id"]
	if player_info.has("player_name"):
		GameState.player_name = player_info["player_name"]
	
	player_info_loaded.emit()

func _handle_player_error(result: Dictionary) -> void:
	var err_code: String = result.get("code", "UNKNOWN_ERROR")
	var err_message: String = result.get("message", "玩家数据获取失败")
	
	last_error = {
		"code": err_code,
		"message": err_message,
		"is_auth_error": result.get("is_auth_error", false),
		"is_server_error": result.get("is_server_error", false)
	}
	
	player_error.emit(err_code, err_message)

func fetch_player_quests(limit: int = 20, offset: int = 0, status_filter: String = "") -> void:
	_set_loading(true)
	var params: Array[String] = []
	params.append("limit=%d" % limit)
	params.append("offset=%d" % offset)
	if status_filter != "":
		params.append("status=%s" % status_filter)
	
	var endpoint: String = "/player/quests?%s" % "&".join(params)
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		_handle_player_quests_success(result)
	else:
		_handle_player_error(result)
	
	_set_loading(false)

func _handle_player_quests_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	player_quests = data.get("items", [])
	last_error.clear()
	player_quests_loaded.emit()

func fetch_player_regions(limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var endpoint: String = "/player/regions?limit=%d&offset=%d" % [limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		_handle_player_regions_success(result)
	else:
		_handle_player_error(result)
	
	_set_loading(false)

func _handle_player_regions_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	player_regions = data.get("items", [])
	last_error.clear()
	player_regions_loaded.emit()

func get_player_quest_by_id(quest_id: String) -> Dictionary:
	for quest in player_quests:
		if quest.get("quest_id", "") == quest_id:
			return quest
	return {}

func get_player_quests_by_status(status: String) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	for quest in player_quests:
		if quest.get("status", "") == status:
			filtered.append(quest)
	return filtered

func get_active_quests() -> Array[Dictionary]:
	return get_player_quests_by_status("active")

func get_available_quests() -> Array[Dictionary]:
	return get_player_quests_by_status("available")

func get_completed_quests() -> Array[Dictionary]:
	return get_player_quests_by_status("completed")

func get_quest_count() -> int:
	return player_quests.size()

func get_quest_status_info(status: String) -> Dictionary:
	if QUEST_STATUS.has(status):
		return QUEST_STATUS[status]
	return {"name": status, "color": "#FFFFFF"}

func is_quest_active(quest_id: String) -> bool:
	var quest: Dictionary = get_player_quest_by_id(quest_id)
	return quest.get("status", "") == "active"

func is_quest_completed(quest_id: String) -> bool:
	var quest: Dictionary = get_player_quest_by_id(quest_id)
	return quest.get("status", "") == "completed"

func get_player_region_by_id(region_id: String) -> Dictionary:
	for region in player_regions:
		if region.get("region_id", "") == region_id:
			return region
	return {}

func is_region_unlocked(region_id: String) -> bool:
	var region: Dictionary = get_player_region_by_id(region_id)
	return region.get("unlocked", false)

func get_unlocked_regions() -> Array[Dictionary]:
	var unlocked: Array[Dictionary] = []
	for region in player_regions:
		if region.get("unlocked", false):
			unlocked.append(region)
	return unlocked

func get_player_level() -> int:
	return player_info.get("level", 1)

func get_player_name() -> String:
	return player_info.get("player_name", "")

func get_player_reputation() -> int:
	return player_info.get("reputation", 0)

func get_player_id() -> String:
	return player_info.get("player_id", "")

func refresh_all() -> void:
	fetch_player_info()
	fetch_player_quests()
	fetch_player_regions()

func _set_loading(loading: bool) -> void:
	if is_loading != loading:
		is_loading = loading
		loading_changed.emit(is_loading)

func is_auth_error() -> bool:
	return last_error.get("is_auth_error", false)

func is_server_error() -> bool:
	return last_error.get("is_server_error", false)

func reset() -> void:
	player_info.clear()
	player_quests.clear()
	player_regions.clear()
	is_loading = false
	last_error.clear()

func accept_quest(quest_id: String) -> void:
	var existing: Dictionary = get_player_quest_by_id(quest_id)
	if existing.size() > 0:
		return
	
	_set_loading(true)
	var result: Dictionary = APIManager.post("/player/quests", {"quest_id": quest_id})
	
	if result.get("success", false):
		var new_quest: Dictionary = {
			"quest_id": quest_id,
			"status": "active",
			"progress": 0
		}
		player_quests.append(new_quest)
		last_error.clear()
		player_quests_loaded.emit()
	else:
		_handle_player_error(result)
	
	_set_loading(false)

func accept_quest_api(quest_id: String) -> Dictionary:
	var existing: Dictionary = get_player_quest_by_id(quest_id)
	if existing.size() > 0 and existing.get("status", "") == "active":
		return _build_quest_result(false, "QUEST_ALREADY_ACCEPTED", "任务已接取", {})
	
	_set_loading(true)
	var endpoint: String = "/player/quests/%s/accept" % quest_id
	var result: Dictionary = APIManager.post(endpoint, {})
	
	_set_loading(false)
	
	if result.get("success", false):
		var quest_data: Dictionary = result.get("data", {})
		_upsert_player_quest(quest_data)
		last_error.clear()
		quest_accepted.emit(quest_id)
		player_quests_loaded.emit()
		return _build_quest_result(true, "", "", quest_data)
	else:
		_handle_player_error(result)
		return _build_quest_result(false, result.get("code", "UNKNOWN_ERROR"), result.get("message", "接取任务失败"), {})

func update_quest_progress(quest_id: String, objectives: Array[Dictionary]) -> Dictionary:
	var quest: Dictionary = get_player_quest_by_id(quest_id)
	if quest.size() == 0 or quest.get("status", "") != "active":
		return _build_quest_result(false, "QUEST_NOT_ACTIVE", "任务未处于活跃状态", {})
	
	_set_loading(true)
	var endpoint: String = "/player/quests/%s/progress" % quest_id
	var result: Dictionary = APIManager.post(endpoint, {"objectives": objectives})
	
	_set_loading(false)
	
	if result.get("success", false):
		var quest_data: Dictionary = result.get("data", {})
		_upsert_player_quest(quest_data)
		last_error.clear()
		quest_progress_updated.emit(quest_id)
		player_quests_loaded.emit()
		return _build_quest_result(true, "", "", quest_data)
	else:
		_handle_player_error(result)
		return _build_quest_result(false, result.get("code", "UNKNOWN_ERROR"), result.get("message", "更新任务进度失败"), {})

func complete_quest_api(quest_id: String) -> Dictionary:
	var quest: Dictionary = get_player_quest_by_id(quest_id)
	if quest.size() == 0:
		return _build_quest_result(false, "QUEST_NOT_FOUND", "任务不存在", {})
	if quest.get("status", "") == "completed":
		return _build_quest_result(false, "QUEST_ALREADY_COMPLETED", "任务已完成", {})
	if quest.get("status", "") != "active":
		return _build_quest_result(false, "QUEST_INVALID_STATE", "任务状态不允许完成", {})
	
	_set_loading(true)
	var endpoint: String = "/player/quests/%s/complete" % quest_id
	var result: Dictionary = APIManager.post(endpoint, {})
	
	_set_loading(false)
	
	if result.get("success", false):
		var quest_data: Dictionary = result.get("data", {})
		_upsert_player_quest(quest_data)
		last_error.clear()
		quest_completed.emit(quest_id)
		player_quests_loaded.emit()
		return _build_quest_result(true, "", "", quest_data)
	else:
		_handle_player_error(result)
		return _build_quest_result(false, result.get("code", "UNKNOWN_ERROR"), result.get("message", "完成任务失败"), {})

func fail_quest_api(quest_id: String) -> Dictionary:
	var quest: Dictionary = get_player_quest_by_id(quest_id)
	if quest.size() == 0 or quest.get("status", "") != "active":
		return _build_quest_result(false, "QUEST_NOT_ACTIVE", "任务未处于活跃状态", {})
	
	_set_loading(true)
	var endpoint: String = "/player/quests/%s/fail" % quest_id
	var result: Dictionary = APIManager.post(endpoint, {})
	
	_set_loading(false)
	
	if result.get("success", false):
		var quest_data: Dictionary = result.get("data", {})
		_upsert_player_quest(quest_data)
		last_error.clear()
		quest_failed.emit(quest_id)
		player_quests_loaded.emit()
		return _build_quest_result(true, "", "", quest_data)
	else:
		_handle_player_error(result)
		return _build_quest_result(false, result.get("code", "UNKNOWN_ERROR"), result.get("message", "标记任务失败失败"), {})

func fetch_quest_detail(quest_id: String) -> Dictionary:
	_set_loading(true)
	var endpoint: String = "/player/quests/%s" % quest_id
	var result: Dictionary = APIManager.get(endpoint)
	
	_set_loading(false)
	
	if result.get("success", false):
		var quest_data: Dictionary = result.get("data", {})
		_upsert_player_quest(quest_data)
		last_error.clear()
		quest_detail_loaded.emit(quest_id)
		return _build_quest_result(true, "", "", quest_data)
	else:
		_handle_player_error(result)
		return _build_quest_result(false, result.get("code", "UNKNOWN_ERROR"), result.get("message", "获取任务详情失败"), {})

func _upsert_player_quest(quest_data: Dictionary) -> void:
	var quest_id: String = quest_data.get("quest_id", "")
	if quest_id == "":
		quest_id = quest_data.get("player_quest_id", "")
	
	if quest_id == "":
		return
	
	for i in range(player_quests.size()):
		if player_quests[i].get("quest_id", "") == quest_id or player_quests[i].get("player_quest_id", "") == quest_id:
			player_quests[i] = quest_data
			return
	
	player_quests.append(quest_data)

func _build_quest_result(success: bool, code: String, message: String, data: Dictionary) -> Dictionary:
	return {
		"success": success,
		"code": code,
		"message": message,
		"data": data
	}

# 存档系统支持方法
func get_quest_save_data() -> Dictionary:
	var active_quests: Array[Dictionary] = get_active_quests()
	var completed_quests: Array[Dictionary] = get_completed_quests()
	
	var active_list: Array = []
	for quest in active_quests:
		active_list.append({
			"quest_id": quest.get("quest_id", ""),
			"progress": quest.get("progress", 0)
		})
	
	var completed_list: Array = []
	for quest in completed_quests:
		completed_list.append(quest.get("quest_id", ""))
	
	return {
		"quests_active": active_list,
		"quests_completed": completed_list
	}

func restore_quest_from_save_data(data: Dictionary) -> void:
	player_quests.clear()
	
	var active_quests: Array = data.get("quests_active", [])
	for quest in active_quests:
		if quest is Dictionary:
			player_quests.append({
				"quest_id": quest.get("quest_id", ""),
				"status": "active",
				"progress": quest.get("progress", 0)
			})
	
	var completed_quests: Array = data.get("quests_completed", [])
	for quest_id in completed_quests:
		if quest_id is String:
			player_quests.append({
				"quest_id": quest_id,
				"status": "completed",
				"progress": 100
			})
	
	player_quests_loaded.emit()