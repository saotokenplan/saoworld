extends Node

signal friends_loaded
signal friend_request_sent
signal friend_request_accepted
signal friend_request_rejected
signal friend_deleted
signal friend_status_loaded
signal error_occurred(error_code: String, message: String)

var _friends: Array = []
var _pending_requests: Array = []
var _friend_statuses: Dictionary = {}
var _is_loading: bool = false

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
	_is_loading = false
