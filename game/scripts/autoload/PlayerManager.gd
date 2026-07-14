extends Node

signal player_info_loaded
signal player_quests_loaded
signal player_regions_loaded
signal player_reputation_loaded
signal player_error(error_code: String, message: String)
signal auth_error(message: String)
signal loading_changed(is_loading: bool)
signal quest_accepted(quest_id: String)
signal quest_completed(quest_id: String)
signal quest_progress_updated(quest_id: String)
signal quest_failed(quest_id: String)
signal quest_detail_loaded(quest_id: String)
signal reputation_updated(region_id: String, new_reputation: int)
signal reputation_unlocked(region_id: String, unlock_type: String)

# 个人中心信号
signal profile_loaded
signal contribution_loaded
signal achievements_loaded

var player_info: Dictionary = {}
var player_quests: Array[Dictionary] = []
var player_regions: Array[Dictionary] = []
var reputation_cache: Dictionary = {}
var reputation_list: Array[Dictionary] = []
var is_loading: bool = false
var last_error: Dictionary = {}
var schema_version: int = 1

# 索引字典（O(1) 查询）
var quest_index: Dictionary = {}
var region_index: Dictionary = {}

# 预排序声望级别列表
var sorted_reputation_levels: Array[Dictionary] = []

# 个人中心数据
var profile_data: Dictionary = {}
var contribution_data: Dictionary = {}
var achievements_data: Array[Dictionary] = []

# 并行请求追踪
var pending_requests: int = 0
var refresh_all_completed: bool = false

const REPUTATION_LEVELS: Dictionary = {
	"hostile": {"name": "敌对", "color": "#F44336", "threshold": -3000, "icon": "💀"},
	"neutral": {"name": "中立", "color": "#9E9E9E", "threshold": 0, "icon": "😐"},
	"friendly": {"name": "友好", "color": "#4CAF50", "threshold": 3000, "icon": "😊"},
	"honored": {"name": "尊敬", "color": "#2196F3", "threshold": 9000, "icon": "🙂"},
	"revered": {"name": "崇敬", "color": "#9C27B0", "threshold": 21000, "icon": "😍"},
	"exalted": {"name": "崇拜", "color": "#FFD700", "threshold": 42000, "icon": "✨"}
}

const REGION_UNLOCK_THRESHOLD: int = 3000

const QUEST_STATUS: Dictionary = {
	"available": {"name": "可接取", "color": "#2196F3"},
	"active": {"name": "进行中", "color": "#FF9800"},
	"completed": {"name": "已完成", "color": "#4CAF50"},
	"failed": {"name": "失败", "color": "#F44336"}
}

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)
	_prepare_reputation_levels()

func _prepare_reputation_levels() -> void:
	sorted_reputation_levels = []
	for level_name in REPUTATION_LEVELS:
		var level_data: Dictionary = REPUTATION_LEVELS[level_name].duplicate()
		level_data["level_name"] = level_name
		sorted_reputation_levels.append(level_data)
	
	sorted_reputation_levels.sort_custom(_sort_reputation_by_threshold)

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
	_update_quest_index()
	last_error.clear()
	player_quests_loaded.emit()

func _update_quest_index() -> void:
	quest_index.clear()
	for quest in player_quests:
		var quest_id: String = quest.get("quest_id", "")
		if quest_id != "":
			quest_index[quest_id] = quest

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
	_update_region_index()
	last_error.clear()
	player_regions_loaded.emit()

func _update_region_index() -> void:
	region_index.clear()
	for region in player_regions:
		var region_id: String = region.get("region_id", "")
		if region_id != "":
			region_index[region_id] = region

func get_player_quest_by_id(quest_id: String) -> Dictionary:
	return quest_index.get(quest_id, {})

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
	return region_index.get(region_id, {})

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
	pending_requests = 4
	refresh_all_completed = false
	
	fetch_player_info_async()
	fetch_player_quests_async()
	fetch_player_regions_async()
	fetch_all_reputation_async()

func fetch_player_info_async() -> void:
	var result: Dictionary = APIManager.get("/player/info")
	if result.get("success", false):
		_handle_player_info_success(result)
	else:
		_handle_player_error(result)
	_decrement_pending_requests()

func fetch_player_quests_async(limit: int = 20, offset: int = 0, status_filter: String = "") -> void:
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
	_decrement_pending_requests()

func fetch_player_regions_async(limit: int = 20, offset: int = 0) -> void:
	var endpoint: String = "/player/regions?limit=%d&offset=%d" % [limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	if result.get("success", false):
		_handle_player_regions_success(result)
	else:
		_handle_player_error(result)
	_decrement_pending_requests()

func fetch_all_reputation_async(limit: int = 20, offset: int = 0) -> void:
	var endpoint: String = "/player/reputation?limit=%d&offset=%d" % [limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	if result.get("success", false):
		_handle_reputation_list_success(result)
	else:
		_handle_player_error(result)
	_decrement_pending_requests()

func _decrement_pending_requests() -> void:
	pending_requests -= 1
	if pending_requests <= 0:
		refresh_all_completed = true
		_set_loading(false)

func fetch_all_reputation(limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var endpoint: String = "/player/reputation?limit=%d&offset=%d" % [limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		_handle_reputation_list_success(result)
	else:
		_handle_player_error(result)
	
	_set_loading(false)

func fetch_region_reputation(region_id: String) -> Dictionary:
	if reputation_cache.has(region_id):
		return reputation_cache[region_id]
	
	_set_loading(true)
	var endpoint: String = "/player/reputation/%s" % region_id
	var result: Dictionary = APIManager.get(endpoint)
	
	_set_loading(false)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_upsert_reputation(data)
		last_error.clear()
		return data
	else:
		_handle_player_error(result)
		return {}

func _handle_reputation_list_success(result: Dictionary) -> void:
	var data: Array[Dictionary] = result.get("data", [])
	reputation_list = data
	for rep in data:
		var region_id: String = rep.get("region_id", "")
		if region_id != "":
			reputation_cache[region_id] = rep
	last_error.clear()
	player_reputation_loaded.emit()

func _upsert_reputation(rep_data: Dictionary) -> void:
	var region_id: String = rep_data.get("region_id", "")
	if region_id == "":
		return
	
	reputation_cache[region_id] = rep_data
	
	for i in range(reputation_list.size()):
		if reputation_list[i].get("region_id", "") == region_id:
			reputation_list[i] = rep_data
			return
	
	reputation_list.append(rep_data)

func get_region_reputation(region_id: String) -> int:
	if reputation_cache.has(region_id):
		return reputation_cache[region_id].get("reputation", 0)
	var player_region: Dictionary = get_player_region_by_id(region_id)
	return player_region.get("reputation", 0)

func get_reputation_level(region_id: String) -> String:
	var rep: int = get_region_reputation(region_id)
	return calculate_reputation_level(rep)

func calculate_reputation_level(reputation: int) -> String:
	for level_info in sorted_reputation_levels:
		if reputation >= level_info["threshold"]:
			return level_info["level_name"]
	
	return "hostile"

func _sort_reputation_by_threshold(a: Dictionary, b: Dictionary) -> bool:
	return a["threshold"] > b["threshold"]

func get_reputation_level_info(level_key: String) -> Dictionary:
	if REPUTATION_LEVELS.has(level_key):
		return REPUTATION_LEVELS[level_key]
	return {"name": level_key, "color": "#FFFFFF", "threshold": 0, "icon": "❓"}

func get_reputation_progress(region_id: String) -> Dictionary:
	var rep: Dictionary = {}
	if reputation_cache.has(region_id):
		rep = reputation_cache[region_id]
	else:
		var reputation: int = get_region_reputation(region_id)
		rep = {"region_id": region_id, "reputation": reputation, "reputation_level": calculate_reputation_level(reputation)}
	
	var current_level: String = rep.get("reputation_level", "neutral")
	var current_rep: int = rep.get("reputation", 0)
	var next_threshold: int = rep.get("next_level_threshold", 0)
	var progress: float = rep.get("current_level_progress", 0.0)
	
	if next_threshold == 0 and progress == 0.0:
		var levels: Array = ["hostile", "neutral", "friendly", "honored", "revered", "exalted"]
		var current_idx: int = levels.find(current_level)
		
		if current_idx < levels.size() - 1:
			var next_level_key: String = levels[current_idx + 1]
			next_threshold = REPUTATION_LEVELS[next_level_key]["threshold"]
			var current_threshold: int = REPUTATION_LEVELS[current_level]["threshold"]
			var range_val: int = next_threshold - current_threshold
			var current_progress: int = current_rep - current_threshold
			if range_val > 0:
				progress = float(current_progress) / float(range_val)
				progress = clamp(progress, 0.0, 1.0)
			else:
				progress = 1.0
		else:
			next_threshold = REPUTATION_LEVELS["exalted"]["threshold"]
			progress = 1.0
	
	return {
		"current_level": current_level,
		"current_reputation": current_rep,
		"next_level_threshold": next_threshold,
		"progress": progress,
		"level_info": get_reputation_level_info(current_level)
	}

func get_reputation_count() -> int:
	return reputation_list.size()

func check_reputation_unlock(current_reputation: int, required_level: String = "", min_reputation: int = 0) -> bool:
	if min_reputation > 0:
		return current_reputation >= min_reputation
	if required_level != "" and REPUTATION_LEVELS.has(required_level):
		var threshold: int = REPUTATION_LEVELS[required_level].threshold
		return current_reputation >= threshold
	return true

func get_next_unlock_threshold(current_reputation: int) -> Dictionary:
	var levels: Array = ["hostile", "neutral", "friendly", "honored", "revered", "exalted"]
	var next_level: String = ""
	var next_threshold: int = 0
	var progress: float = 0.0
	var current_level: String = calculate_reputation_level(current_reputation)
	var current_idx: int = levels.find(current_level)
	
	if current_idx < levels.size() - 1:
		next_level = levels[current_idx + 1]
		next_threshold = REPUTATION_LEVELS[next_level].threshold
		var current_threshold: int = REPUTATION_LEVELS[current_level].threshold
		var range_val: int = next_threshold - current_threshold
		var current_progress: int = current_reputation - current_threshold
		if range_val > 0:
			progress = float(current_progress) / float(range_val)
			progress = clamp(progress, 0.0, 1.0)
	else:
		next_level = "exalted"
		next_threshold = REPUTATION_LEVELS["exalted"].threshold
		progress = 1.0
	
	return {
		"current_level": current_level,
		"current_reputation": current_reputation,
		"next_level": next_level,
		"next_threshold": next_threshold,
		"progress": progress
	}

func check_and_unlock_by_reputation(region_id: String) -> bool:
	var rep: int = get_region_reputation(region_id)
	if rep < REGION_UNLOCK_THRESHOLD:
		return false
	
	var player_region: Dictionary = get_player_region_by_id(region_id)
	if player_region.get("unlocked", false):
		return false
	
	player_region["unlocked"] = true
	player_region["unlocked_at"] = Time.get_datetime_string_from_system()
	_upsert_player_region(player_region)
	reputation_unlocked.emit(region_id, "region_unlock")
	return true

func _upsert_player_region(region_data: Dictionary) -> void:
	var region_id: String = region_data.get("region_id", "")
	if region_id == "":
		return
	
	for i in range(player_regions.size()):
		if player_regions[i].get("region_id", "") == region_id:
			player_regions[i] = region_data
			return
	
	player_regions.append(region_data)

func get_unlocked_regions_by_reputation() -> Array[Dictionary]:
	var unlocked: Array[Dictionary] = []
	for region in player_regions:
		var rep: int = region.get("reputation", 0)
		if rep >= REGION_UNLOCK_THRESHOLD:
			unlocked.append(region)
	return unlocked

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
	quest_index.clear()
	region_index.clear()
	reputation_cache.clear()
	reputation_list.clear()
	profile_data.clear()
	contribution_data.clear()
	achievements_data.clear()
	is_loading = false
	last_error.clear()
	pending_requests = 0
	refresh_all_completed = false

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

# --- 个人中心相关方法 ---

func fetch_player_profile() -> void:
	"""获取玩家完整信息聚合（基本信息+贡献度+声望+成就统计）"""
	_set_loading(true)
	var result: Dictionary = APIManager.get("/player/profile")
	
	if result.get("success", false):
		_handle_profile_success(result)
	else:
		_handle_player_error(result)
	
	_set_loading(false)

func _handle_profile_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	profile_data = data
	last_error.clear()
	
	# 同步更新 player_info 基础信息
	player_info["player_id"] = data.get("player_id", "")
	player_info["display_name"] = data.get("display_name", "")
	player_info["chapter_id"] = data.get("chapter_id", "")
	player_info["contribution_points"] = data.get("contribution_points", 0)
	
	profile_loaded.emit()

func fetch_player_contribution(limit: int = 20, offset: int = 0) -> void:
	"""获取贡献度详情"""
	_set_loading(true)
	var endpoint: String = "/player/contribution?limit=%d&offset=%d" % [limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		_handle_contribution_success(result)
	else:
		_handle_player_error(result)
	
	_set_loading(false)

func _handle_contribution_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	contribution_data = data
	last_error.clear()
	contribution_loaded.emit()

func fetch_player_achievements(limit: int = 20, offset: int = 0) -> void:
	"""获取玩家成就列表"""
	_set_loading(true)
	var endpoint: String = "/player/achievements?limit=%d&offset=%d" % [limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		_handle_achievements_success(result)
	else:
		_handle_player_error(result)
	
	_set_loading(false)

func _handle_achievements_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	var items: Array[Dictionary] = data.get("items", [])
	achievements_data = items
	last_error.clear()
	achievements_loaded.emit()

func get_contribution_points() -> int:
	"""获取贡献度积分"""
	if profile_data.has("contribution_points"):
		return profile_data["contribution_points"]
	return player_info.get("contribution_points", 0)

func get_achievements_unlocked() -> int:
	"""获取已解锁成就数量"""
	if profile_data.has("achievements_unlocked"):
		return profile_data["achievements_unlocked"]
	return achievements_data.size()

func get_achievements_total() -> int:
	"""获取总成就数量"""
	if profile_data.has("achievements_total"):
		return profile_data["achievements_total"]
	return 0

func get_reputation_summary() -> Array[Dictionary]:
	"""获取声望汇总列表"""
	if profile_data.has("reputation_summary"):
		return profile_data["reputation_summary"]
	return reputation_list

func refresh_profile() -> void:
	"""刷新个人中心全部数据"""
	fetch_player_profile()
	fetch_all_reputation()
	fetch_player_achievements()