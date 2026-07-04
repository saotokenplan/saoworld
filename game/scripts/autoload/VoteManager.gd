extends Node
## 投票相关状态管理
## 负责管理当前投票周期、候选项、投票历史等状态

signal current_vote_loaded
signal vote_submitted
signal vote_history_loaded
signal vote_error(error_code: String, message: String)

var current_cycle: Dictionary = {}
var candidates: Array[Dictionary] = []
var vote_history: Array[Dictionary] = []
var has_voted: bool = false
var schema_version: int = 1

func _ready() -> void:
	pass

func fetch_current_vote() -> void:
	var result: Dictionary = APIManager.get("/votes/current")
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		current_cycle = data.get("vote_cycle", {})
		candidates = data.get("candidates", [])
		has_voted = data.get("has_voted", false)
		current_vote_loaded.emit()
	else:
		vote_error.emit(result.get("code", "UNKNOWN_ERROR"), result.get("message", "Failed to fetch vote"))

func submit_vote(candidate_id: String, idempotency_key: String = "") -> bool:
	if idempotency_key == "":
		idempotency_key = _generate_idempotency_key()
	
	var body: Dictionary = {
		"candidate_id": candidate_id
	}
	
	var result: Dictionary = APIManager.post("/votes/submit", body, {}, idempotency_key)
	
	if result.get("success", false):
		has_voted = true
		vote_submitted.emit()
		return true
	else:
		vote_error.emit(result.get("code", "UNKNOWN_ERROR"), result.get("message", "Failed to submit vote"))
		return false

func fetch_history(limit: int = 20, offset: int = 0) -> void:
	var endpoint: String = "/votes/history?limit=%d&offset=%d" % [limit, offset]
	var result: Dictionary = APIManager.get(endpoint)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		vote_history = data.get("items", [])
		vote_history_loaded.emit()
	else:
		vote_error.emit(result.get("code", "UNKNOWN_ERROR"), result.get("message", "Failed to fetch history"))

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

func _generate_idempotency_key() -> String:
	return "vote_%s_%s" % [str(Time.get_unix_time_from_system()), GameState.player_id]

func reset() -> void:
	current_cycle.clear()
	candidates.clear()
	vote_history.clear()
	has_voted = false
