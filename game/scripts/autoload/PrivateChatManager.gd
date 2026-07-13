extends Node
## 私聊消息管理器（自动加载单例）
##
## 负责私聊消息的 API 交互、缓存管理和信号通知。

# === 信号 ===

signal message_sent(message: Dictionary)
signal message_received(message: Dictionary)
signal conversation_loaded(friend_id: String, messages: Array)
signal unread_count_updated(count: int)
signal message_read(message_id: String)
signal error_occurred(error_message: String)

# === 常量 ===

const API_BASE: String = "/api/v1/player/messages"

# === 状态 ===

var _conversations: Dictionary = {}  # friend_id -> Array[Dictionary]
var _unread_messages: Array[Dictionary] = []
var _unread_count: int = 0
var _is_loading: bool = false


# === 公共方法 ===


func send_message(receiver_id: String, content: String) -> void:
	"""发送私聊消息。

	Args:
		receiver_id: 接收者ID
		content: 消息内容（1-500字符）
	"""
	if content.is_empty() or content.length() > 500:
		error_occurred.emit("消息内容长度必须在1-500字符之间")
		return

	var payload := {
		"receiver_id": receiver_id,
		"content": content
	}

	APIManager.post(API_BASE, payload).bind(
		_on_send_message_success,
		_on_send_message_error
	)


func get_recent_conversations(limit: int = 20) -> void:
	"""获取最近对话列表。

	Args:
		limit: 返回数量限制
	"""
	var url := "%s/conversations?limit=%d" % [API_BASE, limit]
	APIManager.get(url).bind(
		_on_get_conversations_success,
		_on_get_conversations_error
	)


func get_conversation_with_friend(friend_id: String, limit: int = 50, offset: int = 0) -> void:
	"""获取与指定好友的对话历史。

	Args:
		friend_id: 好友ID
		limit: 返回数量限制
		offset: 偏移量
	"""
	var url := "%s/conversations/%s?limit=%d&offset=%d" % [API_BASE, friend_id, limit, offset]
	APIManager.get(url).bind(
		func(data): _on_get_conversation_success(friend_id, data),
		_on_get_conversation_error
	)


func mark_message_read(message_id: String) -> void:
	"""标记消息为已读。

	Args:
		message_id: 消息ID
	"""
	var url := "%s/%s/read" % [API_BASE, message_id]
	APIManager.post(url, {}).bind(
		_on_mark_read_success,
		_on_mark_read_error
	)


func get_unread_messages(limit: int = 50) -> void:
	"""获取未读消息列表。

	Args:
		limit: 返回数量限制
	"""
	var url := "%s/unread?limit=%d" % [API_BASE, limit]
	APIManager.get(url).bind(
		_on_get_unread_success,
		_on_get_unread_error
	)


func get_unread_count() -> void:
	"""获取未读消息数。"""
	var url := "%s/unread/count" % API_BASE
	APIManager.get(url).bind(
		_on_get_unread_count_success,
		_on_get_unread_count_error
	)


# === 状态查询 ===


func get_cached_conversation(friend_id: String) -> Array:
	"""获取缓存的对话历史。

	Args:
		friend_id: 好友ID

	Returns:
		消息列表
	"""
	return _conversations.get(friend_id, [])


func get_cached_unread_messages() -> Array:
	"""获取缓存的未读消息列表。

	Returns:
		未读消息列表
	"""
	return _unread_messages.duplicate()


func get_cached_unread_count() -> int:
	"""获取缓存的未读消息数。

	Returns:
		未读消息数
	"""
	return _unread_count


func is_loading() -> bool:
	"""是否正在加载。

	Returns:
		是否正在加载
	"""
	return _is_loading


# === 回调处理 ===


func _on_send_message_success(data: Dictionary) -> void:
	var message := _parse_message(data)
	message_sent.emit(message)
	# 更新本地缓存
	var friend_id: String = str(message.get("receiver_id", ""))
	if friend_id not in _conversations:
		_conversations[friend_id] = []
	_conversations[friend_id].push_front(message)


func _on_send_message_error(error: Dictionary) -> void:
	error_occurred.emit("发送消息失败: %s" % error.get("message", "未知错误"))


func _on_get_conversations_success(data: Dictionary) -> void:
	var conversations: Array = data.get("conversations", [])
	for conv in conversations:
		var friend_id: String = str(conv.get("friend_id", ""))
		var latest: Dictionary = conv.get("latest_message", {})
		if not latest.is_empty():
			if friend_id not in _conversations:
				_conversations[friend_id] = []
			# 只缓存最新消息
			_conversations[friend_id] = [_parse_message(latest)]


func _on_get_conversations_error(error: Dictionary) -> void:
	error_occurred.emit("获取对话列表失败: %s" % error.get("message", "未知错误"))


func _on_get_conversation_success(friend_id: String, data: Dictionary) -> void:
	var messages: Array = data.get("messages", [])
	var parsed_messages: Array = []
	for msg in messages:
		parsed_messages.append(_parse_message(msg))
	_conversations[friend_id] = parsed_messages
	conversation_loaded.emit(friend_id, parsed_messages)


func _on_get_conversation_error(error: Dictionary) -> void:
	error_occurred.emit("获取对话历史失败: %s" % error.get("message", "未知错误"))


func _on_mark_read_success(data: Dictionary) -> void:
	var message := _parse_message(data)
	var message_id: String = str(message.get("message_id", ""))
	message_read.emit(message_id)
	# 更新缓存中的消息状态
	_update_message_read_status(message_id)


func _on_mark_read_error(error: Dictionary) -> void:
	error_occurred.emit("标记已读失败: %s" % error.get("message", "未知错误"))


func _on_get_unread_success(data: Dictionary) -> void:
	var messages: Array = data.get("messages", [])
	var parsed_messages: Array = []
	for msg in messages:
		parsed_messages.append(_parse_message(msg))
	_unread_messages = parsed_messages
	message_received.emit_array(parsed_messages)


func _on_get_unread_error(error: Dictionary) -> void:
	error_occurred.emit("获取未读消息失败: %s" % error.get("message", "未知错误"))


func _on_get_unread_count_success(data: Dictionary) -> void:
	_unread_count = data.get("unread_count", 0)
	unread_count_updated.emit(_unread_count)


func _on_get_unread_count_error(error: Dictionary) -> void:
	error_occurred.emit("获取未读消息数失败: %s" % error.get("message", "未知错误"))


# === 辅助方法 ===


func _parse_message(data: Dictionary) -> Dictionary:
	"""解析消息数据。

	Args:
		data: 原始消息数据

	Returns:
		解析后的消息字典
	"""
	return {
		"message_id": str(data.get("message_id", "")),
		"sender_id": str(data.get("sender_id", "")),
		"receiver_id": str(data.get("receiver_id", "")),
		"content": str(data.get("content", "")),
		"is_read": bool(data.get("is_read", false)),
		"created_at": str(data.get("created_at", ""))
	}


func _update_message_read_status(message_id: String) -> void:
	"""更新消息已读状态。

	Args:
		message_id: 消息ID
	"""
	for friend_id in _conversations:
		for msg in _conversations[friend_id]:
			if str(msg.get("message_id", "")) == message_id:
				msg["is_read"] = true

	for msg in _unread_messages:
		if str(msg.get("message_id", "")) == message_id:
			msg["is_read"] = true

	if _unread_count > 0:
		_unread_count -= 1
		unread_count_updated.emit(_unread_count)


func reset() -> void:
	"""重置所有状态。"""
	_conversations.clear()
	_unread_messages.clear()
	_unread_count = 0
	_is_loading = false