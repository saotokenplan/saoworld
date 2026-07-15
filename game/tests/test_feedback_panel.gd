extends "res://addons/gut/test.gd"
## FeedbackPanel 单元测试

func _setup() -> void:
	var scene = load("res://scenes/ui/FeedbackPanel.tscn")
	if scene:
		add_child(scene.instantiate())

func test_signal_declarations() -> void:
	var panel = $FeedbackPanel
	assert_true(panel != null, "FeedbackPanel 节点应存在")

func test_max_title_length_constant() -> void:
	var panel = $FeedbackPanel
	assert_eq(panel.MAX_TITLE_LENGTH, 256, "标题最大长度应为 256")

func test_max_content_length_constant() -> void:
	var panel = $FeedbackPanel
	assert_eq(panel.MAX_CONTENT_LENGTH, 5000, "内容最大长度应为 5000")

func test_initial_title_input_empty() -> void:
	var panel = $FeedbackPanel
	assert_eq(panel.title_input.text, "", "初始标题输入应为空")

func test_initial_content_input_empty() -> void:
	var panel = $FeedbackPanel
	assert_eq(panel.content_input.text, "", "初始内容输入应为空")

func test_initial_region_input_empty() -> void:
	var panel = $FeedbackPanel
	assert_eq(panel.region_input.text, "", "初始区域输入应为空")

func test_initial_chapter_input_empty() -> void:
	var panel = $FeedbackPanel
	assert_eq(panel.chapter_input.text, "", "初始章节输入应为空")

func test_initial_submit_button_enabled() -> void:
	var panel = $FeedbackPanel
	assert_false(panel.submit_button.disabled, "初始提交按钮应可用")

func test_initial_loading_indicator_hidden() -> void:
	var panel = $FeedbackPanel
	assert_false(panel.loading_indicator.visible, "初始加载指示器应隐藏")

func test_clear_form_clears_all_inputs() -> void:
	var panel = $FeedbackPanel
	panel.title_input.text = "测试标题"
	panel.content_input.text = "测试内容"
	panel.region_input.text = "region_01"
	panel.chapter_input.text = "chapter_01"
	panel._clear_form()
	assert_eq(panel.title_input.text, "", "清空后标题应为空")
	assert_eq(panel.content_input.text, "", "清空后内容应为空")
	assert_eq(panel.region_input.text, "", "清空后区域应为空")
	assert_eq(panel.chapter_input.text, "", "清空后章节应为空")

func test_validate_input_empty_title_returns_false() -> void:
	var panel = $FeedbackPanel
	panel.title_input.text = ""
	panel.content_input.text = "测试内容"
	var result = panel._validate_input()
	assert_false(result, "空标题应验证失败")

func test_validate_input_whitespace_title_returns_false() -> void:
	var panel = $FeedbackPanel
	panel.title_input.text = "   "
	panel.content_input.text = "测试内容"
	var result = panel._validate_input()
	assert_false(result, "纯空白标题应验证失败")

func test_validate_input_empty_content_returns_false() -> void:
	var panel = $FeedbackPanel
	panel.title_input.text = "测试标题"
	panel.content_input.text = ""
	var result = panel._validate_input()
	assert_false(result, "空内容应验证失败")

func test_validate_input_valid_returns_true() -> void:
	var panel = $FeedbackPanel
	panel.title_input.text = "测试标题"
	panel.content_input.text = "测试内容"
	var result = panel._validate_input()
	assert_true(result, "有效输入应验证成功")

func test_title_length_truncation() -> void:
	var panel = $FeedbackPanel
	var long_title = "A" * 300
	panel.title_input.text = long_title
	panel._on_title_changed(long_title)
	assert_le(panel.title_input.text.length(), 256, "标题长度不应超过最大限制")

func test_set_loading_true() -> void:
	var panel = $FeedbackPanel
	panel._set_loading(true)
	assert_true(panel.loading_indicator.visible, "加载中指示器应显示")
	assert_true(panel.submit_button.disabled, "加载中提交按钮应禁用")

func test_set_loading_false() -> void:
	var panel = $FeedbackPanel
	panel._set_loading(true)
	panel._set_loading(false)
	assert_false(panel.loading_indicator.visible, "加载结束指示器应隐藏")
	assert_false(panel.submit_button.disabled, "加载结束提交按钮应可用")

func test_show_message_sets_text_and_visibility() -> void:
	var panel = $FeedbackPanel
	panel._show_message("测试消息", Color(1, 0, 0))
	assert_eq(panel.message_label.text, "测试消息", "消息文本应正确设置")
	assert_true(panel.message_label.visible, "消息标签应显示")

func test_hide_message_hides_label() -> void:
	var panel = $FeedbackPanel
	panel._show_message("测试消息")
	panel._hide_message()
	assert_false(panel.message_label.visible, "隐藏后消息标签应不可见")

func test_show_panel_clears_and_shows() -> void:
	var panel = $FeedbackPanel
	panel.title_input.text = "旧标题"
	panel.content_input.text = "旧内容"
	panel.hide()
	panel.show_panel()
	assert_true(panel.visible, "show_panel 后面板应显示")
	assert_eq(panel.title_input.text, "", "show_panel 应清空标题")
	assert_eq(panel.content_input.text, "", "show_panel 应清空内容")

func test_feedback_type_option_has_items() -> void:
	var panel = $FeedbackPanel
	assert_gt(panel.feedback_type_option.item_count, 0, "反馈类型选项应有条目")

func test_priority_option_has_items() -> void:
	var panel = $FeedbackPanel
	assert_gt(panel.priority_option.item_count, 0, "优先级选项应有条目")
