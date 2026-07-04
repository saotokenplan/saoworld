extends Node
## 投票相关状态管理
## 负责管理当前投票周期、候选项、投票历史等状态

signal current_vote_loaded
signal vote_submitted
signal vote_history_loaded
signal vote_error(error_code: String, message: String)
signal loading_changed(is_loading: bool)

var current_cycle: Dictionary = {}
var candidates: Array[Dictionary] = []
var vote_history: Array[Dictionary] = []
var has_voted: bool = false
var is_loading: bool = false
var last_error: Dictionary = {}
var schema_version: int = 1

func _ready() -> void:
	pass

func fetch_current_vote() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/votes/current")
	if result.get("success", false):
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
	else:
		last_error = {
			"code": result.get("code", "UNKNOWN_ERROR"),
			"message": result.get("message", "Failed to fetch vote")
		}
		vote_error.emit(result.get("code", "UNKNOWN_ERROR"), result.get("message", "Failed to fetch vote"))
	_set_loading(false)

func submit_vote(candidate_id: String, idempotency_key: String = "") -> bool:
	if has_voted:
		return false
	
	if idempotency_key == "":
		idempotency_key = _generate_idempotency_key()
	
	var body: Dictionary = {
		"candidate_id": candidate_id
	}
	
	_set_loading(true)
	var result: Dictionary = APIManager.post("/votes/submit", body, {}, idempotency_key)
	
	if result.get("success", false):
		has_voted = true
		var cycle_id: String = current_cycle.get("vote_cycle_id", "")
		if cycle_id != "":
			GameState.record_vote_participation(cycle_id)
		last_error.clear()
		_set_loading(false)
		vote_submitted.emit()
		return true
	else:
		last_error = {
			"code": result.get("code", "UNKNOWN_ERROR"),
			"message": result.get("message", "Failed to submit vote")
		}
		_set_loading(false)
		vote_error.emit(result.get("code", "UNKNOWN_ERROR"), result.get("message", "Failed to submit vote"))
		return false

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
		last_error = {
			"code": result.get("code", "UNKNOWN_ERROR"),
			"message": result.get("message", "Failed to fetch history")
		}
		vote_error.emit(result.get("code", "UNKNOWN_ERROR"), result.get("message", "Failed to fetch history"))
	_set_loading(false)

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

func refresh() -> void:
	fetch_current_vote()

func _set_loading(loading: bool) -> void:
	if is_loading != loading:
		is_loading = loading
		loading_changed.emit(is_loading)

func _generate_idempotency_key() -> String:
	return "vote_%s_%s" % [str(Time.get_unix_time_from_system()), GameState.player_id]

func reset() -> void:
	current_cycle.clear()
	candidates.clear()
	vote_history.clear()
	has_voted = false
	is_loading = false
	last_error.clear()
