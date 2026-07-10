extends Node

signal current_vote_loaded
signal vote_submitted
signal vote_history_loaded
signal vote_error(error_code: String, message: String)
signal loading_changed(is_loading: bool)
signal auth_error(message: String)

var current_cycle: Dictionary = {}
var candidates: Array[Dictionary] = []
var vote_history: Array[Dictionary] = []
var has_voted: bool = false
var is_loading: bool = false
var last_error: Dictionary = {}
var schema_version: int = 1

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)

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