extends Node

signal regions_loaded
signal region_detail_loaded(region_id: String)
signal world_error(error_code: String, message: String)
signal auth_error(message: String)
signal loading_changed(is_loading: bool)
signal npcs_loaded
signal npc_detail_loaded(npc_id: String)
signal quests_loaded
signal quest_detail_loaded(quest_id: String)

var regions: Array[Dictionary] = []
var region_cache: Dictionary = {}
var npc_cache: Dictionary = {}
var npc_list: Array[Dictionary] = []
var quest_list: Array[Dictionary] = []
var quest_cache: Dictionary = {}
var is_loading: bool = false
var last_error: Dictionary = {}
var schema_version: int = 1
var _cache_timestamps: Dictionary = {}
const CACHE_TTL_SECONDS: int = 300

const REGION_STATUS: Dictionary = {
	"locked": {"name": "锁定", "color": "#666666"},
	"active": {"name": "活跃", "color": "#4CAF50"},
	"unstable": {"name": "不稳定", "color": "#FF9800"},
	"archived": {"name": "已归档", "color": "#9E9E9E"}
}

const REGION_TYPE: Dictionary = {
	"core": {"name": "核心区域", "icon": "🏰"},
	"expansion": {"name": "扩展区域", "icon": "🌍"}
}

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)

func _on_auth_error(request_id: String, message: String) -> void:
	auth_error.emit(message)

func fetch_regions(limit: int = 20, offset: int = 0, status_filter: String = "", force_refresh: bool = false) -> void:
	if not force_refresh and _is_cache_valid("regions") and regions.size() > 0:
		regions_loaded.emit()
		return
	
	_set_loading(true)
	var params: Array[String] = []
	params.append("limit=%d" % limit)
	params.append("offset=%d" % offset)
	if status_filter != "":
		params.append("status=%s" % status_filter)
	
	var endpoint: String = "/world/regions?%s" % "&".join(params)
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		_handle_regions_success(result)
	else:
		_handle_world_error(result)
	
	_set_loading(false)

func _handle_regions_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	regions = data.get("items", [])
	
	for region in regions:
		var region_id: String = region.get("region_id", "")
		if region_id != "":
			region_cache[region_id] = region
	
	_cache_timestamps["regions"] = Time.get_unix_time_from_system()
	last_error.clear()
	regions_loaded.emit()

func _is_cache_valid(cache_key: String) -> bool:
	if not _cache_timestamps.has(cache_key):
		return false
	var last_time: int = _cache_timestamps[cache_key]
	var now: int = Time.get_unix_time_from_system()
	return now - last_time < CACHE_TTL_SECONDS

func _update_cache_timestamp(cache_key: String) -> void:
	_cache_timestamps[cache_key] = Time.get_unix_time_from_system()

func invalidate_cache(cache_key: String = "") -> void:
	if cache_key == "":
		_cache_timestamps.clear()
	else:
		_cache_timestamps.erase(cache_key)

func _handle_world_error(result: Dictionary) -> void:
	var err_code: String = result.get("code", "UNKNOWN_ERROR")
	var err_message: String = result.get("message", "世界数据获取失败")
	
	last_error = {
		"code": err_code,
		"message": err_message,
		"is_auth_error": result.get("is_auth_error", false),
		"is_server_error": result.get("is_server_error", false)
	}
	
	world_error.emit(err_code, err_message)

func fetch_region_detail(region_id: String) -> Dictionary:
	if region_cache.has(region_id):
		return region_cache[region_id]
	
	_set_loading(true)
	var result: Dictionary = APIManager.get("/world/regions/%s" % region_id)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		region_cache[region_id] = data
		last_error.clear()
		region_detail_loaded.emit(region_id)
		_set_loading(false)
		return data
	else:
		_handle_world_error(result)
		_set_loading(false)
		return {}

func get_region_by_id(region_id: String) -> Dictionary:
	if region_cache.has(region_id):
		return region_cache[region_id]
	for region in regions:
		if region.get("region_id", "") == region_id:
			return region
	return {}

func get_regions_by_status(status: String) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	for region in regions:
		if region.get("status", "") == status:
			filtered.append(region)
	return filtered

func get_active_regions() -> Array[Dictionary]:
	return get_regions_by_status("active")

func get_region_count() -> int:
	return regions.size()

func get_region_status_info(status: String) -> Dictionary:
	if REGION_STATUS.has(status):
		return REGION_STATUS[status]
	return {"name": status, "color": "#FFFFFF"}

func is_region_active(region_id: String) -> bool:
	var region: Dictionary = get_region_by_id(region_id)
	return region.get("status", "") == "active"

func is_region_locked(region_id: String) -> bool:
	var region: Dictionary = get_region_by_id(region_id)
	return region.get("status", "") == "locked"

func clear_cache() -> void:
	region_cache.clear()

func refresh() -> void:
	regions.clear()
	region_cache.clear()
	fetch_regions()

func _set_loading(loading: bool) -> void:
	if is_loading != loading:
		is_loading = loading
		loading_changed.emit(is_loading)

func is_auth_error() -> bool:
	return last_error.get("is_auth_error", false)

func is_server_error() -> bool:
	return last_error.get("is_server_error", false)

func reset() -> void:
	regions.clear()
	region_cache.clear()
	_cache_timestamps.clear()
	is_loading = false
	last_error.clear()

func fetch_regions_with_chapter(chapter_id: String = "", limit: int = 20, offset: int = 0, force_refresh: bool = false) -> void:
	if not force_refresh and _is_cache_valid("regions") and regions.size() > 0:
		regions_loaded.emit()
		return
	
	_set_loading(true)
	var params: Array[String] = []
	params.append("limit=%d" % limit)
	params.append("offset=%d" % offset)
	if chapter_id != "":
		params.append("chapter_id=%s" % chapter_id)
	
	var endpoint: String = "/world/regions?%s" % "&".join(params)
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		_handle_regions_success(result)
	else:
		_handle_world_error(result)
	
	_set_loading(false)

func get_regions_by_chapter(chapter_id: String) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	for region in regions:
		if region.get("chapter_id", "") == chapter_id:
			filtered.append(region)
	return filtered

func get_regions_by_type(region_type: String) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	for region in regions:
		if region.get("type", "") == region_type:
			filtered.append(region)
	return filtered

func get_region_type_info(region_type: String) -> Dictionary:
	if REGION_TYPE.has(region_type):
		return REGION_TYPE[region_type]
	return {"name": region_type, "icon": "📍"}

func is_region_unlocked(region_id: String) -> bool:
	var region: Dictionary = get_region_by_id(region_id)
	if region == {}:
		return false
	
	if region.get("status", "") == "active":
		return true
	
	var player_region: Dictionary = PlayerManager.get_player_region_by_id(region_id)
	return player_region.get("unlocked", false)

func get_unlocked_region_count() -> int:
	var count: int = 0
	for region in regions:
		if is_region_unlocked(region.get("region_id", "")):
			count += 1
	return count

func get_region_progression(region_id: String) -> Dictionary:
	var region: Dictionary = get_region_by_id(region_id)
	if region == {}:
		return {"completed_quests": 0, "total_quests": 0, "progress": 0}
	
	var player_region: Dictionary = PlayerManager.get_player_region_by_id(region_id)
	var completed: int = player_region.get("completed_quests", 0)
	var total: int = region.get("quest_count", 0)
	
	if total == 0:
		return {"completed_quests": completed, "total_quests": total, "progress": 0}
	
	return {
		"completed_quests": completed,
		"total_quests": total,
		"progress": float(completed) / float(total)
	}

func get_region_reputation(region_id: String) -> int:
	var player_region: Dictionary = PlayerManager.get_player_region_by_id(region_id)
	return player_region.get("reputation", 0)

func search_regions(query: String) -> Array[Dictionary]:
	var results: Array[Dictionary] = []
	var lower_query: String = query.to_lower()
	
	for region in regions:
		var name: String = region.get("name", "").to_lower()
		var desc: String = region.get("description", "").to_lower()
		
		if lower_query in name or lower_query in desc:
			results.append(region)
	
	return results

func sort_regions(sort_by: String = "name", ascending: bool = true) -> Array[Dictionary]:
	var sorted_regions: Array[Dictionary] = regions.duplicate()
	
	sorted_regions.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var value_a: Variant = a.get(sort_by, "")
		var value_b: Variant = b.get(sort_by, "")
		
		if typeof(value_a) == TYPE_STRING:
			value_a = value_a.to_lower()
			value_b = value_b.to_lower()
		
		if ascending:
			return value_a < value_b
		else:
			return value_a > value_b
	)
	
	return sorted_regions

func fetch_npcs(region_id: String = "", limit: int = 50, offset: int = 0, player_reputation: int = -1) -> void:
	_set_loading(true)
	var params: Array[String] = []
	params.append("limit=%d" % limit)
	params.append("offset=%d" % offset)
	if region_id != "":
		params.append("region_id=%s" % region_id)
	if player_reputation >= 0:
		params.append("player_reputation=%d" % player_reputation)
	
	var endpoint: String = "/world/npcs?%s" % "&".join(params)
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		npc_list = data.get("items", [])
		for npc in npc_list:
			var npc_id: String = npc.get("npc_id", "")
			if npc_id != "":
				npc_cache[npc_id] = npc
		last_error.clear()
		npcs_loaded.emit()
	else:
		_handle_world_error(result)
	
	_set_loading(false)

func fetch_npc_detail(npc_id: String) -> Dictionary:
	if npc_cache.has(npc_id):
		return npc_cache[npc_id]
	
	_set_loading(true)
	var result: Dictionary = APIManager.get("/world/npcs/%s" % npc_id)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		npc_cache[npc_id] = data
		last_error.clear()
		npc_detail_loaded.emit(npc_id)
		_set_loading(false)
		return data
	else:
		_handle_world_error(result)
		_set_loading(false)
		return {}

func get_npc_by_id(npc_id: String) -> Dictionary:
	if npc_cache.has(npc_id):
		return npc_cache[npc_id]
	return {}

func get_npcs_by_region(region_id: String) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	for npc in npc_list:
		if npc.get("location", "") == region_id:
			filtered.append(npc)
	return filtered

func get_npcs_by_faction(faction: String) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	for npc in npc_list:
		if npc.get("faction", "") == faction:
			filtered.append(npc)
	return filtered

func get_npc_count() -> int:
	return npc_list.size()

func load_npcs_from_local() -> void:
	var file: FileAccess = FileAccess.open("res://data/npcs/npc_list.json", FileAccess.READ)
	if not file:
		return
	
	var content: String = file.get_as_text()
	file.close()
	
	var data: Dictionary = JSON.parse_string(content)
	if not data is Dictionary:
		return
	
	npc_list = data.get("npcs", [])
	for npc in npc_list:
		var npc_id: String = npc.get("npc_id", "")
		if npc_id != "":
			npc_cache[npc_id] = npc

func clear_npc_cache() -> void:
	npc_cache.clear()
	npc_list.clear()

func is_npc_accessible(npc_id: String, region_id: String = "") -> bool:
	var npc: Dictionary = get_npc_by_id(npc_id)
	if npc == {}:
		return false
	
	var min_reputation: int = npc.get("min_reputation", 0)
	if min_reputation <= 0:
		return true
	
	var rep: int = 0
	if region_id != "":
		rep = PlayerManager.get_region_reputation(region_id)
	else:
		var npc_region: String = npc.get("location", "")
		if npc_region != "":
			rep = PlayerManager.get_region_reputation(npc_region)
	
	return rep >= min_reputation

func get_npc_min_reputation(npc_id: String) -> int:
	var npc: Dictionary = get_npc_by_id(npc_id)
	return npc.get("min_reputation", 0)

func get_accessible_npcs(region_id: String = "") -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	var npcs_to_check: Array[Dictionary] = []
	
	if region_id != "":
		npcs_to_check = get_npcs_by_region(region_id)
	else:
		npcs_to_check = npc_list
	
	for npc in npcs_to_check:
		var npc_id: String = npc.get("npc_id", "")
		if is_npc_accessible(npc_id, region_id):
			filtered.append(npc)
	
	return filtered

func fetch_quests(region_id: String = "", limit: int = 50, offset: int = 0, player_reputation: int = -1) -> void:
	_set_loading(true)
	var params: Array[String] = []
	params.append("limit=%d" % limit)
	params.append("offset=%d" % offset)
	if region_id != "":
		params.append("region_id=%s" % region_id)
	if player_reputation >= 0:
		params.append("player_reputation=%d" % player_reputation)
	
	var endpoint: String = "/world/quests?%s" % "&".join(params)
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		quest_list = data.get("items", [])
		for quest in quest_list:
			var quest_id: String = quest.get("quest_id", "")
			if quest_id != "":
				quest_cache[quest_id] = quest
		last_error.clear()
		quests_loaded.emit()
	else:
		_handle_world_error(result)
	
	_set_loading(false)

func fetch_quest_detail(quest_id: String) -> Dictionary:
	if quest_cache.has(quest_id):
		return quest_cache[quest_id]
	
	_set_loading(true)
	var result: Dictionary = APIManager.get("/world/quests/%s" % quest_id)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		quest_cache[quest_id] = data
		last_error.clear()
		quest_detail_loaded.emit(quest_id)
		_set_loading(false)
		return data
	else:
		_handle_world_error(result)
		_set_loading(false)
		return {}

func get_quest_by_id(quest_id: String) -> Dictionary:
	if quest_cache.has(quest_id):
		return quest_cache[quest_id]
	for quest in quest_list:
		if quest.get("quest_id", "") == quest_id:
			return quest
	return {}

func get_quests_by_region(region_id: String) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	for quest in quest_list:
		if quest.get("region_id", "") == region_id:
			filtered.append(quest)
	return filtered

func get_quest_count() -> int:
	return quest_list.size()

func is_quest_accessible(quest_id: String, region_id: String = "") -> bool:
	var quest: Dictionary = get_quest_by_id(quest_id)
	if quest == {}:
		return false
	
	var min_reputation: int = quest.get("min_reputation", 0)
	if min_reputation <= 0:
		return true
	
	var rep: int = 0
	if region_id != "":
		rep = PlayerManager.get_region_reputation(region_id)
	else:
		var quest_region: String = quest.get("region_id", "")
		if quest_region != "":
			rep = PlayerManager.get_region_reputation(quest_region)
	
	return rep >= min_reputation

func get_quest_min_reputation(quest_id: String) -> int:
	var quest: Dictionary = get_quest_by_id(quest_id)
	return quest.get("min_reputation", 0)

func get_accessible_quests(region_id: String = "") -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	var quests_to_check: Array[Dictionary] = []
	
	if region_id != "":
		quests_to_check = get_quests_by_region(region_id)
	else:
		quests_to_check = quest_list
	
	for quest in quests_to_check:
		var quest_id: String = quest.get("quest_id", "")
		if is_quest_accessible(quest_id, region_id):
			filtered.append(quest)
	
	return filtered

func clear_quest_cache() -> void:
	quest_cache.clear()
	quest_list.clear()

# ====== S1-08 客户端 UI 优化：区域解锁条件格式化（auto-20260711-0200） ======

func get_region_unlock_requirement_text(region_id: String) -> String:
	var threshold: int = PlayerManager.REGION_UNLOCK_THRESHOLD
	if is_region_unlocked(region_id):
		return "已解锁（声望 %d 即可）" % threshold
	var current_rep: int = get_region_reputation(region_id)
	return "需要声望 %d（当前 %d）" % [threshold, current_rep]

func get_region_reputation_progress(region_id: String) -> Dictionary:
	var threshold: int = PlayerManager.REGION_UNLOCK_THRESHOLD
	var current_rep: int = get_region_reputation(region_id)
	var unlocked: bool = is_region_unlocked(region_id)
	var progress: float = 0.0
	if threshold > 0:
		progress = float(current_rep) / float(threshold)
		progress = clamp(progress, 0.0, 1.0)
	return {
		"current": current_rep,
		"required": threshold,
		"progress": progress,
		"unlocked": unlocked
	}

func is_region_locked_by_reputation(region_id: String) -> bool:
	var region: Dictionary = get_region_by_id(region_id)
	if region == {}:
		return false
	if region.get("status", "") != "locked":
		return false
	var current_rep: int = get_region_reputation(region_id)
	var threshold: int = PlayerManager.REGION_UNLOCK_THRESHOLD
	return current_rep < threshold