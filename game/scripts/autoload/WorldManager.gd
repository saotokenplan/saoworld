extends Node

signal regions_loaded
signal region_detail_loaded(region_id: String)
signal world_error(error_code: String, message: String)
signal auth_error(message: String)
signal loading_changed(is_loading: bool)

var regions: Array[Dictionary] = []
var region_cache: Dictionary = {}
var is_loading: bool = false
var last_error: Dictionary = {}
var schema_version: int = 1

const REGION_STATUS: Dictionary = {
	"locked": {"name": "锁定", "color": "#666666"},
	"active": {"name": "活跃", "color": "#4CAF50"},
	"unstable": {"name": "不稳定", "color": "#FF9800"},
	"archived": {"name": "已归档", "color": "#9E9E9E"}
}

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)

func _on_auth_error(request_id: String, message: String) -> void:
	auth_error.emit(message)

func fetch_regions(limit: int = 20, offset: int = 0, status_filter: String = "") -> void:
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
	
	last_error.clear()
	regions_loaded.emit()

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
	is_loading = false
	last_error.clear()