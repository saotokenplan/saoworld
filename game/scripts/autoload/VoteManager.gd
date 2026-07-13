extends Node

signal current_vote_loaded
signal vote_submitted
signal vote_history_loaded
signal vote_error(error_code: String, message: String)
signal loading_changed(is_loading: bool)
signal auth_error(message: String)
signal vote_landing_updated(cycle_id: String, landed: bool)
signal discussions_loaded(discussions: Array, meta: Dictionary)
signal discussion_created(discussion: Dictionary)
signal replies_loaded(discussion_id: String, replies: Array, meta: Dictionary)
signal reply_created(reply: Dictionary)
signal discussion_like_changed(discussion_id: String, liked: bool, like_count: int)
signal vote_progress_updated(progress: Dictionary)
signal chart_data_loaded(chart_data: Dictionary)

var current_cycle: Dictionary = {}
var candidates: Array[Dictionary] = []
var vote_history: Array[Dictionary] = []
var has_voted: bool = false
var is_loading: bool = false
var last_error: Dictionary = {}
var schema_version: int = 1
var discussions: Array[Dictionary] = []
var current_discussion_id: String = ""
var replies: Array[Dictionary] = []
var discussions_meta: Dictionary = {}
var replies_meta: Dictionary = {}
var current_progress: Dictionary = {}
var progress_poll_timer: Timer = null
var progress_poll_interval: int = 10
var is_polling_progress: bool = false
var _chart_data_cache: Dictionary = {}

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)
	_setup_progress_poll_timer()

func _setup_progress_poll_timer() -> void:
	progress_poll_timer = Timer.new()
	progress_poll_timer.wait_time = progress_poll_interval
	progress_poll_timer.autostart = false
	progress_poll_timer.one_shot = false
	progress_poll_timer.timeout.connect(_poll_vote_progress)
	add_child(progress_poll_timer)

func _on_auth_error(request_id: String, message: String) -> void:
	auth_error.emit(message)

func fetch_current_vote() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/votes/current")
	
	if result.get("success", false):
		_handle_current_vote_success(result)
	else:
		_handle_vote_error(result)
	
	_set_loading(false)

func _handle_current_vote_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	current_cycle = data.get("vote_cycle", {})
	candidates = data.get("candidates", [])
	has_voted = data.get("has_voted", false)
	
	if has_voted:
		var cycle_id: String = current_cycle.get("vote_cycle_id", "")
		if cycle_id != "":
			GameState.record_vote_participation(cycle_id)
	
	last_error.clear()
	current_vote_loaded.emit()

func _handle_vote_error(result: Dictionary) -> void:
	var err_code: String = result.get("code", "UNKNOWN_ERROR")
	var err_message: String = result.get("message", "投票操作失败")
	
	last_error = {
		"code": err_code,
		"message": err_message,
		"is_auth_error": result.get("is_auth_error", false),
		"is_server_error": result.get("is_server_error", false),
		"is_client_error": result.get("is_client_error", false)
	}
	
	vote_error.emit(err_code, err_message)

func submit_vote(candidate_id: String, idempotency_key: String = "") -> bool:
	if has_voted:
		last_error = {"code": "ALREADY_VOTED", "message": "您在本周期已投票"}
		vote_error.emit("ALREADY_VOTED", "您在本周期已投票")
		return false
	
	if is_cycle_open() == false:
		last_error = {"code": "INVALID_VOTE_STATE", "message": "投票周期状态不允许投票"}
		vote_error.emit("INVALID_VOTE_STATE", "投票周期状态不允许投票")
		return false
	
	if idempotency_key == "":
		idempotency_key = _generate_idempotency_key()
	
	var body: Dictionary = {
		"candidate_id": candidate_id
	}
	
	_set_loading(true)
	var result: Dictionary = APIManager.post("/votes/submit", body, {}, idempotency_key)
	
	if result.get("success", false):
		_handle_vote_submit_success()
		_set_loading(false)
		return true
	else:
		_handle_vote_error(result)
		_set_loading(false)
		return false

func _handle_vote_submit_success() -> void:
	has_voted = true
	var cycle_id: String = current_cycle.get("vote_cycle_id", "")
	if cycle_id != "":
		GameState.record_vote_participation(cycle_id)
	last_error.clear()
	vote_submitted.emit()

func fetch_history(limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var endpoint: String = "/votes/history?limit=%d&offset=%d" % [limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		vote_history = data.get("items", [])
		last_error.clear()
		vote_history_loaded.emit()
	else:
		_handle_vote_error(result)
	
	_set_loading(false)

func fetch_vote_history(limit: int = 20, offset: int = 0) -> void:
	"""投票历史查询别名（用于个人中心）"""
	fetch_history(limit, offset)

func get_candidate_by_id(candidate_id: String) -> Dictionary:
	for candidate in candidates:
		if candidate.get("candidate_id", "") == candidate_id:
			return candidate
	return {}

func get_candidate_count() -> int:
	return candidates.size()

func is_cycle_open() -> bool:
	return current_cycle.get("status", "") == "open"

func get_winner() -> Dictionary:
	for candidate in candidates:
		if candidate.get("is_winner", false):
			return candidate
	return {}

func get_total_votes() -> int:
	var total: int = 0
	for candidate in candidates:
		total += candidate.get("vote_count", 0)
	return total

func get_candidate_percentage(candidate_id: String) -> float:
	var total: int = get_total_votes()
	if total == 0:
		return 0.0
	
	for candidate in candidates:
		if candidate.get("candidate_id", "") == candidate_id:
			return float(candidate.get("vote_count", 0)) / float(total) * 100.0
	return 0.0

func get_cycle_status() -> String:
	return current_cycle.get("status", "")

func get_cycle_title() -> String:
	return current_cycle.get("title", "")

func get_cycle_description() -> String:
	return current_cycle.get("description", "")

func get_cycle_end_time() -> String:
	return current_cycle.get("end_time", "")

func can_vote() -> bool:
	return is_cycle_open() and not has_voted

func is_auth_error() -> bool:
	return last_error.get("is_auth_error", false)

func is_server_error() -> bool:
	return last_error.get("is_server_error", false)

func refresh() -> void:
	fetch_current_vote()

func _set_loading(loading: bool) -> void:
	if is_loading != loading:
		is_loading = loading
		loading_changed.emit(is_loading)

func _generate_idempotency_key() -> String:
	var timestamp: String = str(Time.get_unix_time_from_system())
	var random: String = str(randi())
	return "vote_%s_%s_%s" % [timestamp, GameState.player_id, random]

func reset() -> void:
	current_cycle.clear()
	candidates.clear()
	vote_history.clear()
	has_voted = false
	is_loading = false
	last_error.clear()
	current_progress.clear()
	_chart_data_cache.clear()
	stop_progress_polling()

func get_vote_history_with_landing() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	for item in vote_history:
		var landed_item: Dictionary = item.duplicate()
		landed_item["is_landed"] = is_vote_landed(item)
		result.append(landed_item)
	return result

func is_vote_landed(vote_item: Dictionary) -> bool:
	var content_package: Dictionary = vote_item.get("content_package", {})
	return not content_package.is_empty()

func get_content_package_for_vote(cycle_id: String) -> Dictionary:
	for item in vote_history:
		if item.get("vote_cycle_id", item.get("cycle_id", "")) == cycle_id:
			return item.get("content_package", {})
	return {}

func get_landed_at(vote_item: Dictionary) -> String:
	var content_package: Dictionary = vote_item.get("content_package", {})
	return content_package.get("released_at", "")

func get_affected_regions(vote_item: Dictionary) -> Array[String]:
	var content_package: Dictionary = vote_item.get("content_package", {})
	var payload: Dictionary = content_package.get("payload", {})
	var regions: Array = payload.get("regions", [])
	var result: Array[String] = []
	for region in regions:
		if typeof(region) == TYPE_DICTIONARY:
			result.append(region.get("name", region.get("region_id", "")))
		else:
			result.append(str(region))
	return result

func fetch_discussions(vote_cycle_id: String, sort_by: String = "time", limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var endpoint: String = "/votes/discussions/%s?sort_by=%s&limit=%d&offset=%d" % [vote_cycle_id, sort_by, limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		discussions = data.get("items", [])
		discussions_meta = result.get("meta", {})
		last_error.clear()
		discussions_loaded.emit(discussions, discussions_meta)
	else:
		_handle_vote_error(result)
	
	_set_loading(false)

func create_discussion(vote_cycle_id: String, content: String) -> bool:
	if content.strip_edges() == "":
		last_error = {"code": "DISCUSSION_CONTENT_EMPTY", "message": "讨论内容不能为空"}
		vote_error.emit("DISCUSSION_CONTENT_EMPTY", "讨论内容不能为空")
		return false
	
	if content.length() > 500:
		last_error = {"code": "DISCUSSION_CONTENT_TOO_LONG", "message": "讨论内容不能超过500字"}
		vote_error.emit("DISCUSSION_CONTENT_TOO_LONG", "讨论内容不能超过500字")
		return false
	
	var body: Dictionary = {
		"content": content
	}
	
	_set_loading(true)
	var result: Dictionary = APIManager.post("/votes/discussions/%s" % vote_cycle_id, body)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		var new_discussion: Dictionary = data.get("discussion", {})
		discussions.insert(0, new_discussion)
		last_error.clear()
		discussion_created.emit(new_discussion)
		_set_loading(false)
		return true
	else:
		_handle_vote_error(result)
		_set_loading(false)
		return false

func like_discussion(discussion_id: String) -> bool:
	_set_loading(true)
	var result: Dictionary = APIManager.post("/votes/discussions/%s/like" % discussion_id)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		var like_count: int = data.get("like_count", 0)
		_update_discussion_like_count(discussion_id, like_count)
		last_error.clear()
		discussion_like_changed.emit(discussion_id, true, like_count)
		_set_loading(false)
		return true
	else:
		_handle_vote_error(result)
		_set_loading(false)
		return false

func unlike_discussion(discussion_id: String) -> bool:
	_set_loading(true)
	var result: Dictionary = APIManager.delete("/votes/discussions/%s/like" % discussion_id)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		var like_count: int = data.get("like_count", 0)
		_update_discussion_like_count(discussion_id, like_count)
		last_error.clear()
		discussion_like_changed.emit(discussion_id, false, like_count)
		_set_loading(false)
		return true
	else:
		_handle_vote_error(result)
		_set_loading(false)
		return false

func _update_discussion_like_count(discussion_id: String, like_count: int) -> void:
	for i in range(discussions.size()):
		if discussions[i].get("discussion_id", "") == discussion_id:
			discussions[i]["like_count"] = like_count
			break

func fetch_replies(discussion_id: String, limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var endpoint: String = "/votes/discussions/%s/replies?limit=%d&offset=%d" % [discussion_id, limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		current_discussion_id = discussion_id
		var data: Dictionary = result.get("data", {})
		replies = data.get("items", [])
		replies_meta = result.get("meta", {})
		last_error.clear()
		replies_loaded.emit(discussion_id, replies, replies_meta)
	else:
		_handle_vote_error(result)
	
	_set_loading(false)

func create_reply(discussion_id: String, content: String) -> bool:
	if content.strip_edges() == "":
		last_error = {"code": "REPLY_CONTENT_EMPTY", "message": "回复内容不能为空"}
		vote_error.emit("REPLY_CONTENT_EMPTY", "回复内容不能为空")
		return false
	
	if content.length() > 500:
		last_error = {"code": "REPLY_CONTENT_TOO_LONG", "message": "回复内容不能超过500字"}
		vote_error.emit("REPLY_CONTENT_TOO_LONG", "回复内容不能超过500字")
		return false
	
	var body: Dictionary = {
		"content": content
	}
	
	_set_loading(true)
	var result: Dictionary = APIManager.post("/votes/discussions/%s/replies" % discussion_id, body)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		var new_reply: Dictionary = data.get("reply", {})
		replies.append(new_reply)
		_increment_discussion_reply_count(discussion_id)
		last_error.clear()
		reply_created.emit(new_reply)
		_set_loading(false)
		return true
	else:
		_handle_vote_error(result)
		_set_loading(false)
		return false

func _increment_discussion_reply_count(discussion_id: String) -> void:
	for i in range(discussions.size()):
		if discussions[i].get("discussion_id", "") == discussion_id:
			discussions[i]["reply_count"] = discussions[i].get("reply_count", 0) + 1
			break

func like_reply(reply_id: String) -> bool:
	_set_loading(true)
	var result: Dictionary = APIManager.post("/votes/replies/%s/like" % reply_id)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		var like_count: int = data.get("like_count", 0)
		_update_reply_like_count(reply_id, like_count)
		last_error.clear()
		_set_loading(false)
		return true
	else:
		_handle_vote_error(result)
		_set_loading(false)
		return false

func unlike_reply(reply_id: String) -> bool:
	_set_loading(true)
	var result: Dictionary = APIManager.delete("/votes/replies/%s/like" % reply_id)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		var like_count: int = data.get("like_count", 0)
		_update_reply_like_count(reply_id, like_count)
		last_error.clear()
		_set_loading(false)
		return true
	else:
		_handle_vote_error(result)
		_set_loading(false)
		return false

func _update_reply_like_count(reply_id: String, like_count: int) -> void:
	for i in range(replies.size()):
		if replies[i].get("reply_id", "") == reply_id:
			replies[i]["like_count"] = like_count
			break

func get_discussion_by_id(discussion_id: String) -> Dictionary:
	for discussion in discussions:
		if discussion.get("discussion_id", "") == discussion_id:
			return discussion
	return {}

func reset_discussions() -> void:
	discussions.clear()
	current_discussion_id = ""
	replies.clear()
	discussions_meta.clear()
	replies_meta.clear()

func fetch_vote_progress() -> void:
	var result: Dictionary = APIManager.get("/votes/current/progress")
	if result.get("success", false):
		_handle_progress_success(result)
	else:
		_handle_vote_error(result)

func start_progress_polling() -> void:
	if is_polling_progress:
		return
	is_polling_progress = true
	if progress_poll_timer:
		progress_poll_timer.start()
		fetch_vote_progress()

func stop_progress_polling() -> void:
	is_polling_progress = false
	if progress_poll_timer:
		progress_poll_timer.stop()

func _poll_vote_progress() -> void:
	fetch_vote_progress()

func _handle_progress_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	current_progress = data
	last_error.clear()
	vote_progress_updated.emit(current_progress)

func get_current_progress() -> Dictionary:
	return current_progress.duplicate()

func get_total_votes_from_progress() -> int:
	return current_progress.get("total_votes", 0)

func get_leading_candidate_id() -> String:
	return str(current_progress.get("leading_candidate_id", ""))

func get_candidate_progress(candidate_id: String) -> Dictionary:
	for candidate in current_progress.get("candidates", []):
		if str(candidate.get("candidate_id", "")) == candidate_id:
			return candidate.duplicate()
	return {}

func fetch_vote_result_chart_data(vote_cycle_id: String, chart_type: String = "pie") -> void:
	"""获取投票结果的图表数据。

	参数：
		vote_cycle_id: 投票周期ID
		chart_type: 图表类型（pie 或 bar），默认为 pie
	"""
	# 检查缓存
	var cache_key: String = "%s_%s" % [vote_cycle_id, chart_type]
	if _chart_data_cache.has(cache_key):
		chart_data_loaded.emit(_chart_data_cache[cache_key])
		return

	_set_loading(true)
	var endpoint: String = "/votes/history/%s/chart-data?chart_type=%s" % [vote_cycle_id, chart_type]
	var result: Dictionary = APIManager.get(endpoint)

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		# 缓存数据
		_chart_data_cache[cache_key] = data
		last_error.clear()
		chart_data_loaded.emit(data)
	else:
		_handle_vote_error(result)

	_set_loading(false)

func clear_chart_data_cache() -> void:
	"""清空图表数据缓存。"""
	_chart_data_cache.clear()

func get_cached_chart_data(vote_cycle_id: String, chart_type: String = "pie") -> Dictionary:
	"""从缓存获取图表数据。"""
	var cache_key: String = "%s_%s" % [vote_cycle_id, chart_type]
	if _chart_data_cache.has(cache_key):
		return _chart_data_cache[cache_key].duplicate()
	return {}