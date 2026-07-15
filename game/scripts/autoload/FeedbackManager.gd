extends Node

## 反馈管理器 - 处理用户反馈提交
##
## 负责向 ops-service 的反馈 API 提交玩家反馈

signal feedback_submitted(feedback_id: String)
signal feedback_failed(error: Dictionary)

const FEEDBACK_TYPES: Dictionary = {
	"bug": "Bug报告",
	"suggestion": "功能建议",
	"question": "问题咨询",
	"other": "其他"
}

const PRIORITIES: Dictionary = {
	"low": "低",
	"medium": "中",
	"high": "高",
	"critical": "紧急"
}

var _pending_feedbacks: Dictionary = {}


func _ready() -> void:
	# 连接 APIManager 的信号
	var api_manager = _get_api_manager()
	if api_manager:
		api_manager.request_completed.connect(_on_request_completed)
		api_manager.request_failed.connect(_on_request_failed)


func _get_api_manager() -> Node:
	var api_manager = get_node_or_null("/root/APIManager")
	if api_manager == null:
		push_error("FeedbackManager: APIManager not found")
	return api_manager


## 提交反馈
func submit_feedback(
	feedback_type: String,
	title: String,
	content: String,
	priority: String = "medium",
	region_id: String = "",
	chapter_id: String = "",
	attachment_urls: Array[String] = [],
	metadata: Dictionary = {}
) -> String:
	"""提交用户反馈到服务端
	
	Args:
		feedback_type: 反馈类型 (bug/suggestion/question/other)
		title: 反馈标题
		content: 反馈内容
		priority: 优先级 (low/medium/high/critical)
		region_id: 相关区域ID（可选）
		chapter_id: 相关章节ID（可选）
		attachment_urls: 附件URL列表（可选）
		metadata: 元数据（可选）
	
	Returns:
		request_id: 请求ID，用于追踪请求状态
	"""
	var api_manager = _get_api_manager()
	if api_manager == null:
		var error = {"code": "NETWORK_ERROR", "message": "APIManager 不可用"}
		feedback_failed.emit(error)
		return ""
	
	# 验证反馈类型
	if not FEEDBACK_TYPES.has(feedback_type):
		var error = {"code": "INVALID_ARGUMENT", "message": "无效的反馈类型: %s" % feedback_type}
		feedback_failed.emit(error)
		return ""
	
	# 验证优先级
	if not PRIORITIES.has(priority):
		var error = {"code": "INVALID_ARGUMENT", "message": "无效的优先级: %s" % priority}
		feedback_failed.emit(error)
		return ""
	
	# 构建请求体
	var body: Dictionary = {
		"feedback_type": feedback_type,
		"title": title,
		"content": content,
		"priority": priority
	}
	
	if region_id != "":
		body["region_id"] = region_id
	if chapter_id != "":
		body["chapter_id"] = chapter_id
	if attachment_urls.size() > 0:
		body["attachment_urls"] = attachment_urls
	if metadata.size() > 0:
		body["metadata"] = metadata
	
	# 发送请求
	var request_id = api_manager.post("/feedback", body)
	
	# 记录待处理反馈
	_pending_feedbacks[request_id] = {
		"feedback_type": feedback_type,
		"title": title,
		"content": content,
		"priority": priority
	}
	
	return request_id


## 提交Bug报告
func submit_bug_report(
	title: String,
	content: String,
	priority: String = "high",
	region_id: String = "",
	chapter_id: String = "",
	attachment_urls: Array[String] = []
) -> String:
	"""提交Bug报告的快捷方法"""
	return submit_feedback(
		"bug",
		title,
		content,
		priority,
		region_id,
		chapter_id,
		attachment_urls
	)


## 提交功能建议
func submit_suggestion(
	title: String,
	content: String,
	priority: String = "medium"
) -> String:
	"""提交功能建议的快捷方法"""
	return submit_feedback(
		"suggestion",
		title,
		content,
		priority
	)


## 提交问题咨询
func submit_question(
	title: String,
	content: String
) -> String:
	"""提交问题咨询的快捷方法"""
	return submit_feedback(
		"question",
		title,
		content,
		"medium"
	)


## 获取反馈类型名称
func get_feedback_type_name(feedback_type: String) -> String:
	"""获取反馈类型的显示名称"""
	return FEEDBACK_TYPES.get(feedback_type, "未知类型")


## 获取优先级名称
func get_priority_name(priority: String) -> String:
	"""获取优先级的显示名称"""
	return PRIORITIES.get(priority, "未知")


## 获取所有反馈类型
func get_all_feedback_types() -> Dictionary:
	"""获取所有可用的反馈类型"""
	return FEEDBACK_TYPES.duplicate()


## 获取所有优先级
func get_all_priorities() -> Dictionary:
	"""获取所有可用的优先级"""
	return PRIORITIES.duplicate()


func _on_request_completed(request_id: String, response: Dictionary) -> void:
	"""处理请求完成"""
	if not _pending_feedbacks.has(request_id):
		return
	
	var pending = _pending_feedbacks[request_id]
	_pending_feedbacks.erase(request_id)
	
	# 检查响应
	if response.has("data") and response["data"].has("feedback_id"):
		var feedback_id = response["data"]["feedback_id"]
		feedback_submitted.emit(feedback_id)
	else:
		var error = {"code": "INVALID_RESPONSE", "message": "响应数据格式错误"}
		feedback_failed.emit(error)


func _on_request_failed(request_id: String, error: Dictionary) -> void:
	"""处理请求失败"""
	if not _pending_feedbacks.has(request_id):
		return
	
	_pending_feedbacks.erase(request_id)
	feedback_failed.emit(error)