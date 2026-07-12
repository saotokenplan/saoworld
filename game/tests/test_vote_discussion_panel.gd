extends "res://addons/gut/test.gd"
## VoteDiscussionPanel 单元测试
## 覆盖 S4-02 投票讨论区的 UI 组件逻辑

const SCRIPT_PATH: String = "res://scripts/ui/vote_discussion_panel.gd"

func _make_panel() -> Control:
	var node: Control = Control.new()
	var script: GDScript = load(SCRIPT_PATH)
	node.set_script(script)
	return node

func test_script_loads() -> void:
	var script: GDScript = load(SCRIPT_PATH)
	assert_true(script != null, "vote_discussion_panel.gd 脚本应能加载")

func test_has_back_pressed_signal() -> void:
	var panel: Control = _make_panel()
	assert_true(panel.has_signal("back_pressed"), "应暴露 back_pressed 信号")
	panel.queue_free()

func test_has_view_content_pressed_signal() -> void:
	var panel: Control = _make_panel()
	assert_true(panel.has_signal("view_content_pressed"), "应暴露 view_content_pressed 信号")
	panel.queue_free()

func test_initial_vote_cycle_id_empty() -> void:
	var panel: Control = _make_panel()
	assert_eq(panel.vote_cycle_id, "", "初始 vote_cycle_id 应为空字符串")
	panel.queue_free()

func test_initial_current_sort_is_time() -> void:
	var panel: Control = _make_panel()
	assert_eq(panel.current_sort, "time", "初始 current_sort 应为 time")
	panel.queue_free()

func test_initial_discussion_items_empty() -> void:
	var panel: Control = _make_panel()
	assert_eq(panel.discussion_items.size(), 0, "初始 discussion_items 应为空数组")
	panel.queue_free()

func test_initial_reply_items_empty() -> void:
	var panel: Control = _make_panel()
	assert_eq(panel.reply_items.size(), 0, "初始 reply_items 应为空数组")
	panel.queue_free()

func test_initial_current_discussion_id_empty() -> void:
	var panel: Control = _make_panel()
	assert_eq(panel.current_discussion_id, "", "初始 current_discussion_id 应为空字符串")
	panel.queue_free()

func test_initial_is_loading_false() -> void:
	var panel: Control = _make_panel()
	assert_false(panel.is_loading, "初始 is_loading 应为 false")
	panel.queue_free()

func test_set_vote_cycle_sets_id() -> void:
	var panel: Control = _make_panel()
	panel.set_vote_cycle("vc_test_001", "测试周期")
	assert_eq(panel.vote_cycle_id, "vc_test_001", "set_vote_cycle 应设置 vote_cycle_id")
	panel.queue_free()

func test_set_vote_cycle_with_empty_id_no_refresh() -> void:
	var panel: Control = _make_panel()
	panel.set_vote_cycle("", "")
	assert_eq(panel.vote_cycle_id, "", "空 vote_cycle_id 不应触发刷新")
	panel.queue_free()

func test_clear_discussions_empty_array() -> void:
	var panel: Control = _make_panel()
	panel.discussion_items = [PanelContainer.new(), PanelContainer.new()]
	panel._clear_discussions()
	assert_eq(panel.discussion_items.size(), 0, "_clear_discussions 应清空 discussion_items")
	panel.queue_free()

func test_clear_replies_empty_array() -> void:
	var panel: Control = _make_panel()
	panel.reply_items = [PanelContainer.new(), PanelContainer.new()]
	panel._clear_replies()
	assert_eq(panel.reply_items.size(), 0, "_clear_replies 应清空 reply_items")
	panel.queue_free()

func test_on_reply_back_pressed_hides_panel() -> void:
	var panel: Control = _make_panel()
	panel.reply_panel = Control.new()
	panel.reply_panel.visible = true
	panel.current_discussion_id = "disc_test_001"
	panel._on_reply_back_pressed()
	assert_false(panel.reply_panel.visible, "点击返回后回复面板应隐藏")
	assert_eq(panel.current_discussion_id, "", "点击返回后 current_discussion_id 应清空")
	panel.queue_free()

func test_on_view_replies_sets_current_discussion_id() -> void:
	var panel: Control = _make_panel()
	panel.reply_panel = Control.new()
	var discussion: Dictionary = {
		"discussion_id": "disc_test_001",
		"content": "这是一条测试讨论内容"
	}
	panel._on_view_replies(discussion)
	assert_eq(panel.current_discussion_id, "disc_test_001", "查看回复时应设置 current_discussion_id")
	panel.queue_free()

func test_on_view_replies_shows_reply_panel() -> void:
	var panel: Control = _make_panel()
	panel.reply_panel = Control.new()
	panel.reply_panel.visible = false
	var discussion: Dictionary = {
		"discussion_id": "disc_test_001",
		"content": "测试讨论"
	}
	panel._on_view_replies(discussion)
	assert_true(panel.reply_panel.visible, "查看回复时应显示回复面板")
	panel.queue_free()

func test_on_view_replies_short_content_title() -> void:
	var panel: Control = _make_panel()
	panel.reply_panel = Control.new()
	panel.reply_discussion_title = Label.new()
	panel.add_child(panel.reply_discussion_title)
	var discussion: Dictionary = {
		"discussion_id": "disc_test_001",
		"content": "短内容"
	}
	panel._on_view_replies(discussion)
	assert_eq(panel.reply_discussion_title.text, "短内容", "短内容标题应完整显示")
	panel.queue_free()

func test_on_view_replies_long_content_truncated() -> void:
	var panel: Control = _make_panel()
	panel.reply_panel = Control.new()
	panel.reply_discussion_title = Label.new()
	panel.add_child(panel.reply_discussion_title)
	var long_content: String = "a" * 60
	var discussion: Dictionary = {
		"discussion_id": "disc_test_001",
		"content": long_content
	}
	panel._on_view_replies(discussion)
	assert_eq(panel.reply_discussion_title.text.length(), 53, "长内容标题应截断为50字加...")
	assert_true(panel.reply_discussion_title.text.ends_with("..."), "长内容标题应以...结尾")
	panel.queue_free()

func test_on_loading_changed_sets_is_loading() -> void:
	var panel: Control = _make_panel()
	panel._on_loading_changed(true)
	assert_true(panel.is_loading, "加载状态应设置为 true")
	panel._on_loading_changed(false)
	assert_false(panel.is_loading, "加载状态应设置为 false")
	panel.queue_free()

func test_on_back_pressed_emits_signal() -> void:
	var panel: Control = _make_panel()
	var signal_emitted: bool = false
	panel.back_pressed.connect(func():
		signal_emitted = true
	)
	panel._on_back_pressed()
	assert_true(signal_emitted, "_on_back_pressed 应发射 back_pressed 信号")
	panel.queue_free()

func test_discussions_loaded_empty_sets_status() -> void:
	var panel: Control = _make_panel()
	panel.status_label = Label.new()
	panel.add_child(panel.status_label)
	panel.discussions_container = VBoxContainer.new()
	panel.add_child(panel.discussions_container)
	panel._on_discussions_loaded([], {"total": 0})
	assert_eq(panel.status_label.text, "暂无讨论，快来发表第一条讨论吧！", "空讨论应显示提示文本")
	panel.queue_free()

func test_discussions_loaded_with_data_clears_status() -> void:
	var panel: Control = _make_panel()
	panel.status_label = Label.new()
	panel.add_child(panel.status_label)
	panel.discussions_container = VBoxContainer.new()
	panel.add_child(panel.discussions_container)
	var discussions: Array = [
		{"discussion_id": "d1", "player_id": "player_001", "content": "测试讨论", "like_count": 5, "reply_count": 3, "created_at": "2026-07-13"}
	]
	panel._on_discussions_loaded(discussions, {"total": 1})
	assert_eq(panel.status_label.text, "", "有讨论数据时状态文本应清空")
	assert_eq(panel.discussion_items.size(), 1, "应渲染 1 条讨论")
	panel.queue_free()

func test_discussions_loaded_multiple_items() -> void:
	var panel: Control = _make_panel()
	panel.status_label = Label.new()
	panel.add_child(panel.status_label)
	panel.discussions_container = VBoxContainer.new()
	panel.add_child(panel.discussions_container)
	var discussions: Array = [
		{"discussion_id": "d1", "player_id": "player_001", "content": "讨论1", "like_count": 5, "reply_count": 3, "created_at": "2026-07-13"},
		{"discussion_id": "d2", "player_id": "player_002", "content": "讨论2", "like_count": 10, "reply_count": 7, "created_at": "2026-07-12"},
		{"discussion_id": "d3", "player_id": "player_003", "content": "讨论3", "like_count": 2, "reply_count": 1, "created_at": "2026-07-11"}
	]
	panel._on_discussions_loaded(discussions, {"total": 3})
	assert_eq(panel.discussion_items.size(), 3, "应渲染 3 条讨论")
	panel.queue_free()

func test_replies_loaded_empty_sets_status() -> void:
	var panel: Control = _make_panel()
	panel.reply_status_label = Label.new()
	panel.add_child(panel.reply_status_label)
	panel.replies_container = VBoxContainer.new()
	panel.add_child(panel.replies_container)
	panel._on_replies_loaded("disc_test", [], {"total": 0})
	assert_eq(panel.reply_status_label.text, "暂无回复，快来发表第一条回复吧！", "空回复应显示提示文本")
	panel.queue_free()

func test_replies_loaded_with_data_clears_status() -> void:
	var panel: Control = _make_panel()
	panel.reply_status_label = Label.new()
	panel.add_child(panel.reply_status_label)
	panel.replies_container = VBoxContainer.new()
	panel.add_child(panel.replies_container)
	var replies: Array = [
		{"reply_id": "r1", "player_id": "player_001", "content": "测试回复", "like_count": 2, "created_at": "2026-07-13"}
	]
	panel._on_replies_loaded("disc_test", replies, {"total": 1})
	assert_eq(panel.reply_status_label.text, "", "有回复数据时状态文本应清空")
	assert_eq(panel.reply_items.size(), 1, "应渲染 1 条回复")
	panel.queue_free()

func test_discussion_created_clears_input() -> void:
	var panel: Control = _make_panel()
	panel.new_discussion_input = TextEdit.new()
	panel.new_discussion_input.text = "待发布的讨论内容"
	panel.add_child(panel.new_discussion_input)
	panel.submit_discussion_button = Button.new()
	panel.submit_discussion_button.disabled = true
	panel.add_child(panel.submit_discussion_button)
	panel.status_label = Label.new()
	panel.add_child(panel.status_label)
	panel.vote_cycle_id = "vc_test"
	panel._on_discussion_created({"discussion_id": "d_new", "content": "新讨论"})
	assert_eq(panel.new_discussion_input.text, "", "发布成功后应清空输入框")
	assert_false(panel.submit_discussion_button.disabled, "发布成功后按钮应恢复可用")
	assert_eq(panel.status_label.text, "发布成功！", "发布成功后应显示成功提示")
	panel.queue_free()

func test_reply_created_clears_input() -> void:
	var panel: Control = _make_panel()
	panel.new_reply_input = TextEdit.new()
	panel.new_reply_input.text = "待发布的回复内容"
	panel.add_child(panel.new_reply_input)
	panel.submit_reply_button = Button.new()
	panel.submit_reply_button.disabled = true
	panel.add_child(panel.submit_reply_button)
	panel.reply_status_label = Label.new()
	panel.add_child(panel.reply_status_label)
	panel.current_discussion_id = "disc_test"
	panel._on_reply_created({"reply_id": "r_new", "content": "新回复"})
	assert_eq(panel.new_reply_input.text, "", "回复成功后应清空输入框")
	assert_false(panel.submit_reply_button.disabled, "回复成功后按钮应恢复可用")
	assert_eq(panel.reply_status_label.text, "发布成功！", "回复成功后应显示成功提示")
	panel.queue_free()

func test_on_vote_error_updates_status() -> void:
	var panel: Control = _make_panel()
	panel.status_label = Label.new()
	panel.add_child(panel.status_label)
	panel.submit_discussion_button = Button.new()
	panel.submit_discussion_button.disabled = true
	panel.add_child(panel.submit_discussion_button)
	panel.submit_reply_button = Button.new()
	panel.submit_reply_button.disabled = true
	panel.add_child(panel.submit_reply_button)
	panel._on_vote_error("TEST_ERROR", "测试错误信息")
	assert_eq(panel.status_label.text, "错误：测试错误信息", "错误时应显示错误信息")
	assert_false(panel.submit_discussion_button.disabled, "错误时讨论按钮应恢复可用")
	assert_false(panel.submit_reply_button.disabled, "错误时回复按钮应恢复可用")
	panel.queue_free()

func test_sort_tab_changed_to_time() -> void:
	var panel: Control = _make_panel()
	panel.vote_cycle_id = "vc_test"
	panel._on_sort_tab_changed(0)
	assert_eq(panel.current_sort, "time", "切换到第0个标签应设置为 time 排序")
	panel.queue_free()

func test_sort_tab_changed_to_hot() -> void:
	var panel: Control = _make_panel()
	panel.vote_cycle_id = "vc_test"
	panel._on_sort_tab_changed(1)
	assert_eq(panel.current_sort, "hot", "切换到第1个标签应设置为 hot 排序")
	panel.queue_free()
