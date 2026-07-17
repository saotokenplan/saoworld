extends Node

signal friends_loaded
signal friend_request_sent
signal friend_request_accepted
signal friend_request_rejected
signal friend_deleted
signal friend_status_loaded
signal error_occurred(error_code: String, message: String)

# 协作任务相关信号
signal collab_quests_active_loaded
signal collab_quests_pending_loaded
signal collab_quests_history_loaded
signal collab_quest_created
signal collab_quest_accepted
signal collab_quest_rejected
signal collab_quest_progress_updated
signal collab_quest_completed
signal collab_quest_detail_loaded

var _friends: Array = []
var _pending_requests: Array = []
var _friend_statuses: Dictionary = {}
var _is_loading: bool = false

# 协作任务相关状态
var _active_collab_quests: Array = []
var _pending_collab_quests: Array = []
var _history_collab_quests: Array = []
var _current_collab_quest: Dictionary = {}

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)

func _on_auth_error(request_id: String, message: String) -> void:
	error_occurred.emit("AUTH_ERROR", message)

func fetch_friends() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/friends")

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_friends = data.get("items", [])
		error_occurred.emit("", "")
		friends_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_pending_requests() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/friends/requests/pending")

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_pending_requests = data.get("items", [])
		error_occurred.emit("", "")
		friend_status_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func send_friend_request(friend_id: String) -> void:
	if friend_id == "":
		error_occurred.emit("INVALID_FRIEND_ID", "好友ID不能为空")
		return

	_set_loading(true)
	var body: Dictionary = {"friend_id": friend_id}
	var result: Dictionary = APIManager.post("/friends/requests", body)

	if result.get("success", false):
		friend_request_sent.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func accept_friend_request(player_id: String) -> void:
	if player_id == "":
		error_occurred.emit("INVALID_PLAYER_ID", "玩家ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/friends/requests/%s/accept" % player_id)

	if result.get("success", false):
		_remove_pending_request(player_id)
		friend_request_accepted.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func reject_friend_request(player_id: String) -> void:
	if player_id == "":
		error_occurred.emit("INVALID_PLAYER_ID", "玩家ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/friends/requests/%s/reject" % player_id)

	if result.get("success", false):
		_remove_pending_request(player_id)
		friend_request_rejected.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func delete_friend(friend_id: String) -> void:
	if friend_id == "":
		error_occurred.emit("INVALID_FRIEND_ID", "好友ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.delete("/friends/%s" % friend_id)

	if result.get("success", false):
		_remove_friend(friend_id)
		friend_deleted.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func get_friend_status(friend_id: String) -> String:
	return _friend_statuses.get(friend_id, "offline")

func is_friend(friend_id: String) -> bool:
	for friend in _friends:
		if friend.get("player_id", "") == friend_id:
			return true
	return false

func get_friend_count() -> int:
	return _friends.size()

# === 协作任务相关 API ===

func create_collab_quest(
	friend_id: String,
	quest_type: String,
	title: String,
	description: String,
	objectives: Dictionary,
	rewards: Dictionary,
	expires_at: String
) -> void:
	if friend_id == "":
		error_occurred.emit("INVALID_FRIEND_ID", "好友ID不能为空")
		return
	if title == "":
		error_occurred.emit("INVALID_TITLE", "任务标题不能为空")
		return
	if quest_type == "":
		quest_type = "hunt"

	_set_loading(true)
	var body: Dictionary = {
		"friend_id": friend_id,
		"quest_type": quest_type,
		"title": title
	}
	if description != "":
		body["description"] = description
	if objectives.size() > 0:
		body["objectives"] = objectives
	if rewards.size() > 0:
		body["rewards"] = rewards
	if expires_at != "":
		body["expires_at"] = expires_at

	var result: Dictionary = APIManager.post("/friend/collab-quests", body)

	if result.get("success", false):
		_current_collab_quest = result.get("data", {})
		collab_quest_created.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func accept_collab_quest(quest_id: String) -> void:
	if quest_id == "":
		error_occurred.emit("INVALID_QUEST_ID", "任务ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/friend/collab-quests/%s/accept" % quest_id)

	if result.get("success", false):
		_current_collab_quest = result.get("data", {})
		_remove_pending_collab_quest(quest_id)
		collab_quest_accepted.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func reject_collab_quest(quest_id: String) -> void:
	if quest_id == "":
		error_occurred.emit("INVALID_QUEST_ID", "任务ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/friend/collab-quests/%s/reject" % quest_id)

	if result.get("success", false):
		_remove_pending_collab_quest(quest_id)
		collab_quest_rejected.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func update_collab_quest_progress(quest_id: String, progress_data: Dictionary) -> void:
	if quest_id == "":
		error_occurred.emit("INVALID_QUEST_ID", "任务ID不能为空")
		return

	_set_loading(true)
	var body: Dictionary = {"progress_data": progress_data}
	var result: Dictionary = APIManager.post("/friend/collab-quests/%s/progress" % quest_id, body)

	if result.get("success", false):
		_current_collab_quest = result.get("data", {})
		collab_quest_progress_updated.emit(quest_id, _current_collab_quest)
	else:
		_handle_error(result)

	_set_loading(false)

func complete_collab_quest(quest_id: String) -> void:
	if quest_id == "":
		error_occurred.emit("INVALID_QUEST_ID", "任务ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/friend/collab-quests/%s/complete" % quest_id)

	if result.get("success", false):
		_current_collab_quest = result.get("data", {})
		collab_quest_completed.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_active_collab_quests() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/friend/collab-quests/active")

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_active_collab_quests = data.get("quests", data.get("items", []))
		collab_quests_active_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_pending_collab_quests() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/friend/collab-quests/pending")

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_pending_collab_quests = data.get("quests", data.get("items", []))
		collab_quests_pending_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_collab_quest_history(limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/friend/collab-quests/history?limit=%d&offset=%d" % [limit, offset])

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_history_collab_quests = data.get("quests", data.get("items", []))
		collab_quests_history_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func get_active_collab_quests() -> Array:
	return _active_collab_quests.duplicate()

func get_pending_collab_quests() -> Array:
	return _pending_collab_quests.duplicate()

func get_history_collab_quests() -> Array:
	return _history_collab_quests.duplicate()

func get_current_collab_quest() -> Dictionary:
	return _current_collab_quest.duplicate()

func _remove_pending_collab_quest(quest_id: String) -> void:
	for i in range(_pending_collab_quests.size() - 1, -1, -1):
		if _pending_collab_quests[i].get("quest_id", "") == quest_id:
			_pending_collab_quests.remove_at(i)
			return

func clear_friends_cache() -> void:
	_friends.clear()

func clear_pending_cache() -> void:
	_pending_requests.clear()

func _remove_pending_request(player_id: String) -> void:
	for i in range(_pending_requests.size() - 1, -1, -1):
		if _pending_requests[i].get("player_id", "") == player_id:
			_pending_requests.remove_at(i)
			return

func _remove_friend(friend_id: String) -> void:
	for i in range(_friends.size() - 1, -1, -1):
		if _friends[i].get("player_id", "") == friend_id:
			_friends.remove_at(i)
			return

func _handle_error(result: Dictionary) -> void:
	var err_code: String = result.get("code", "UNKNOWN_ERROR")
	var err_message: String = result.get("message", "操作失败")
	error_occurred.emit(err_code, err_message)

func _set_loading(loading: bool) -> void:
	_is_loading = loading

func reset() -> void:
	_friends.clear()
	_pending_requests.clear()
	_friend_statuses.clear()
	_active_collab_quests.clear()
	_pending_collab_quests.clear()
	_history_collab_quests.clear()
	_current_collab_quest.clear()
	_is_loading = false
