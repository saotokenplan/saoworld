extends "res://addons/gut/test.gd"
## FeedbackManager 单元测试

func test_initial_state() -> void:
	var fm := FeedbackManager
	assert_eq(fm._pending_feedbacks, {}, "初始 _pending_feedbacks 应为空字典")

func test_signal_declarations() -> void:
	var fm := FeedbackManager
	assert_true(fm.has_signal("feedback_submitted"), "应声明 feedback_submitted 信号")
	assert_true(fm.has_signal("feedback_failed"), "应声明 feedback_failed 信号")

func test_feedback_types_constant() -> void:
	var fm := FeedbackManager
	var types = fm.FEEDBACK_TYPES
	assert_eq(types.size(), 4, "应有4种反馈类型")
	assert_true(types.has("bug"), "应包含 bug 类型")
	assert_true(types.has("suggestion"), "应包含 suggestion 类型")
	assert_true(types.has("question"), "应包含 question 类型")
	assert_true(types.has("other"), "应包含 other 类型")

func test_priorities_constant() -> void:
	var fm := FeedbackManager
	var priorities = fm.PRIORITIES
	assert_eq(priorities.size(), 4, "应有4种优先级")
	assert_true(priorities.has("low"), "应包含 low 优先级")
	assert_true(priorities.has("medium"), "应包含 medium 优先级")
	assert_true(priorities.has("high"), "应包含 high 优先级")
	assert_true(priorities.has("critical"), "应包含 critical 优先级")

func test_get_feedback_type_name_valid() -> void:
	var fm := FeedbackManager
	assert_eq(fm.get_feedback_type_name("bug"), "Bug报告", "bug 类型名称应为 Bug报告")
	assert_eq(fm.get_feedback_type_name("suggestion"), "功能建议", "suggestion 类型名称应为 功能建议")
	assert_eq(fm.get_feedback_type_name("question"), "问题咨询", "question 类型名称应为 问题咨询")
	assert_eq(fm.get_feedback_type_name("other"), "其他", "other 类型名称应为 其他")

func test_get_feedback_type_name_invalid() -> void:
	var fm := FeedbackManager
	assert_eq(fm.get_feedback_type_name("invalid"), "未知类型", "无效类型应返回 未知类型")

func test_get_priority_name_valid() -> void:
	var fm := FeedbackManager
	assert_eq(fm.get_priority_name("low"), "低", "low 优先级名称应为 低")
	assert_eq(fm.get_priority_name("medium"), "中", "medium 优先级名称应为 中")
	assert_eq(fm.get_priority_name("high"), "高", "high 优先级名称应为 高")
	assert_eq(fm.get_priority_name("critical"), "紧急", "critical 优先级名称应为 紧急")

func test_get_priority_name_invalid() -> void:
	var fm := FeedbackManager
	assert_eq(fm.get_priority_name("invalid"), "未知", "无效优先级应返回 未知")

func test_get_all_feedback_types_returns_copy() -> void:
	var fm := FeedbackManager
	var types = fm.get_all_feedback_types()
	assert_eq(types.size(), 4, "应返回4种类型")
	types["test"] = "测试"
	var original = fm.get_all_feedback_types()
	assert_eq(original.size(), 4, "修改副本不应影响原始数据")

func test_get_all_priorities_returns_copy() -> void:
	var fm := FeedbackManager
	var priorities = fm.get_all_priorities()
	assert_eq(priorities.size(), 4, "应返回4种优先级")
	priorities["test"] = "测试"
	var original = fm.get_all_priorities()
	assert_eq(original.size(), 4, "修改副本不应影响原始数据")

func test_submit_feedback_invalid_type_emits_failed() -> void:
	var fm := FeedbackManager
	var error_captured: Dictionary = {}
	fm.feedback_failed.connect(func(err):
		error_captured = err
	)
	var result = fm.submit_feedback("invalid_type", "测试标题", "测试内容")
	assert_eq(result, "", "无效类型应返回空 request_id")
	assert_eq(error_captured.get("code", ""), "INVALID_ARGUMENT", "错误码应为 INVALID_ARGUMENT")

func test_submit_feedback_invalid_priority_emits_failed() -> void:
	var fm := FeedbackManager
	var error_captured: Dictionary = {}
	fm.feedback_failed.connect(func(err):
		error_captured = err
	)
	var result = fm.submit_feedback("bug", "测试标题", "测试内容", "invalid_priority")
	assert_eq(result, "", "无效优先级应返回空 request_id")
	assert_eq(error_captured.get("code", ""), "INVALID_ARGUMENT", "错误码应为 INVALID_ARGUMENT")

func test_submit_bug_report_shortcut() -> void:
	var fm := FeedbackManager
	var original_submit = fm.submit_feedback
	var called_with: Array = []
	fm.submit_feedback = func(
		feedback_type: String,
		title: String,
		content: String,
		priority: String = "medium",
		region_id: String = "",
		chapter_id: String = "",
		attachment_urls: Array[String] = [],
		metadata: Dictionary = {}
	) -> String:
		called_with = [feedback_type, title, content, priority, region_id, chapter_id]
		return "req_test_001"
	var result = fm.submit_bug_report("Bug标题", "Bug内容", "high", "region_01", "chapter_01")
	assert_eq(result, "req_test_001", "应返回 submit_feedback 的返回值")
	assert_eq(called_with[0], "bug", "反馈类型应为 bug")
	assert_eq(called_with[1], "Bug标题", "标题应传递正确")
	assert_eq(called_with[2], "Bug内容", "内容应传递正确")
	assert_eq(called_with[3], "high", "优先级应为 high")
	assert_eq(called_with[4], "region_01", "区域ID应传递正确")
	assert_eq(called_with[5], "chapter_01", "章节ID应传递正确")
	fm.submit_feedback = original_submit

func test_submit_suggestion_shortcut() -> void:
	var fm := FeedbackManager
	var original_submit = fm.submit_feedback
	var called_with: Array = []
	fm.submit_feedback = func(
		feedback_type: String,
		title: String,
		content: String,
		priority: String = "medium",
		region_id: String = "",
		chapter_id: String = "",
		attachment_urls: Array[String] = [],
		metadata: Dictionary = {}
	) -> String:
		called_with = [feedback_type, title, content, priority]
		return "req_test_002"
	var result = fm.submit_suggestion("建议标题", "建议内容", "medium")
	assert_eq(result, "req_test_002", "应返回 submit_feedback 的返回值")
	assert_eq(called_with[0], "suggestion", "反馈类型应为 suggestion")
	assert_eq(called_with[1], "建议标题", "标题应传递正确")
	assert_eq(called_with[2], "建议内容", "内容应传递正确")
	assert_eq(called_with[3], "medium", "优先级应为 medium")
	fm.submit_feedback = original_submit

func test_submit_question_shortcut() -> void:
	var fm := FeedbackManager
	var original_submit = fm.submit_feedback
	var called_with: Array = []
	fm.submit_feedback = func(
		feedback_type: String,
		title: String,
		content: String,
		priority: String = "medium",
		region_id: String = "",
		chapter_id: String = "",
		attachment_urls: Array[String] = [],
		metadata: Dictionary = {}
	) -> String:
		called_with = [feedback_type, title, content, priority]
		return "req_test_003"
	var result = fm.submit_question("问题标题", "问题内容")
	assert_eq(result, "req_test_003", "应返回 submit_feedback 的返回值")
	assert_eq(called_with[0], "question", "反馈类型应为 question")
	assert_eq(called_with[1], "问题标题", "标题应传递正确")
	assert_eq(called_with[2], "问题内容", "内容应传递正确")
	assert_eq(called_with[3], "medium", "优先级应为 medium")
	fm.submit_feedback = original_submit

func test_on_request_completed_with_valid_response() -> void:
	var fm := FeedbackManager
	fm._pending_feedbacks["req_test_001"] = {
		"feedback_type": "bug",
		"title": "测试",
		"content": "测试内容",
		"priority": "high"
	}
	var submitted_id: String = ""
	fm.feedback_submitted.connect(func(fid):
		submitted_id = fid
	)
	var response: Dictionary = {
		"data": {"feedback_id": "fb_test_001"}
	}
	fm._on_request_completed("req_test_001", response)
	assert_eq(submitted_id, "fb_test_001", "应发出 feedback_submitted 信号并携带 feedback_id")
	assert_false(fm._pending_feedbacks.has("req_test_001"), "完成后应从待处理列表移除")

func test_on_request_completed_with_invalid_response() -> void:
	var fm := FeedbackManager
	fm._pending_feedbacks["req_test_002"] = {
		"feedback_type": "bug",
		"title": "测试",
		"content": "测试内容",
		"priority": "high"
	}
	var error_captured: Dictionary = {}
	fm.feedback_failed.connect(func(err):
		error_captured = err
	)
	var response: Dictionary = {"data": {}}
	fm._on_request_completed("req_test_002", response)
	assert_eq(error_captured.get("code", ""), "INVALID_RESPONSE", "无效响应应发出失败信号")
	assert_false(fm._pending_feedbacks.has("req_test_002"), "失败后应从待处理列表移除")

func test_on_request_completed_ignores_unknown_request() -> void:
	var fm := FeedbackManager
	fm._pending_feedbacks.clear()
	var signal_emitted := false
	fm.feedback_submitted.connect(func(fid):
		signal_emitted = true
	)
	fm.feedback_failed.connect(func(err):
		signal_emitted = true
	)
	fm._on_request_completed("unknown_req", {})
	assert_false(signal_emitted, "未知请求不应触发任何信号")

func test_on_request_failed() -> void:
	var fm := FeedbackManager
	fm._pending_feedbacks["req_test_003"] = {
		"feedback_type": "bug",
		"title": "测试",
		"content": "测试内容",
		"priority": "high"
	}
	var error_captured: Dictionary = {}
	fm.feedback_failed.connect(func(err):
		error_captured = err
	)
	var error_data: Dictionary = {"code": "NETWORK_ERROR", "message": "网络错误"}
	fm._on_request_failed("req_test_003", error_data)
	assert_eq(error_captured.get("code", ""), "NETWORK_ERROR", "应转发错误信息")
	assert_false(fm._pending_feedbacks.has("req_test_003"), "失败后应从待处理列表移除")

func test_on_request_failed_ignores_unknown_request() -> void:
	var fm := FeedbackManager
	fm._pending_feedbacks.clear()
	var signal_emitted := false
	fm.feedback_failed.connect(func(err):
		signal_emitted = true
	)
	fm._on_request_failed("unknown_req", {"code": "ERROR"})
	assert_false(signal_emitted, "未知请求不应触发失败信号")
