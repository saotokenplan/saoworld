extends Node
## VoteReviewPanel GUT 测试
## 覆盖复盘报告面板信号、初始状态、数据展示逻辑

var review_panel_script: GDScript

func before_all() -> void:
	review_panel_script = load("res://scripts/ui/voting/vote_review_panel.gd")

func test_signals_declared() -> void:
	assert_true(review_panel_script.has_signal("back_pressed"), "应有 back_pressed 信号")
	assert_true(review_panel_script.has_signal("view_content_package"), "应有 view_content_package 信号")

func test_initial_state() -> void:
	var instance: Control = review_panel_script.new()
	assert_eq(instance.review_data, {}, "review_data 初始应为空字典")
	assert_false(instance.visible, "初始状态面板应不可见")
	instance.queue_free()

func test_show_review_sets_data() -> void:
	var instance: Control = review_panel_script.new()
	var data: Dictionary = {
		"vote_cycle_id": "vc_001",
		"chapter_id": "ch_01",
		"status": "finalized",
		"total_votes": 100,
		"participation_rate": 25.5
	}
	instance.show_review(data)
	assert_eq(instance.review_data, data, "show_review 应设置 review_data")
	assert_true(instance.visible, "show_review 后面板应可见")
	instance.queue_free()

func test_hide_clears_data() -> void:
	var instance: Control = review_panel_script.new()
	instance.review_data = {"vote_cycle_id": "vc_001"}
	instance.visible = true
	instance.hide()
	assert_false(instance.visible, "hide 后面板应不可见")
	assert_eq(instance.review_data, {}, "hide 后应清空 review_data")
	instance.queue_free()

func test_get_cycle_title_with_title() -> void:
	var instance: Control = review_panel_script.new()
	instance.review_data = {"title": "测试周期标题"}
	var title: String = instance._get_cycle_title()
	assert_eq(title, "测试周期标题", "有 title 时应返回 title")
	instance.queue_free()

func test_get_cycle_title_with_cycle_id() -> void:
	var instance: Control = review_panel_script.new()
	instance.review_data = {"vote_cycle_id": "vc_001"}
	var title: String = instance._get_cycle_title()
	assert_true(title.contains("vc_001"), "无 title 时应包含 vote_cycle_id")
	instance.queue_free()

func test_get_status_text() -> void:
	var instance: Control = review_panel_script.new()
	assert_eq(instance._get_status_text("open"), "进行中", "open 应翻译为进行中")
	assert_eq(instance._get_status_text("closed"), "已关闭", "closed 应翻译为已关闭")
	assert_eq(instance._get_status_text("finalized"), "已结算", "finalized 应翻译为已结算")
	assert_eq(instance._get_status_text("unknown"), "unknown", "未知状态应原样返回")
	instance.queue_free()

func test_get_package_status_text() -> void:
	var instance: Control = review_panel_script.new()
	assert_eq(instance._get_package_status_text("live"), "已上线", "live 应翻译为已上线")
	assert_eq(instance._get_package_status_text("gray"), "灰度中", "gray 应翻译为灰度中")
	assert_eq(instance._get_package_status_text("rolled_back"), "已回滚", "rolled_back 应翻译为已回滚")
	instance.queue_free()

func test_format_generated_params() -> void:
	var instance: Control = review_panel_script.new()
	var params: Dictionary = {"npc_count": 3, "difficulty": "hard"}
	var text: String = instance._format_generated_params(params)
	assert_true(text.contains("npc_count: 3"), "应包含 npc_count")
	assert_true(text.contains("difficulty: hard"), "应包含 difficulty")
	instance.queue_free()

func test_format_time_range_unknown() -> void:
	var instance: Control = review_panel_script.new()
	instance.review_data = {}
	assert_eq(instance._format_time_range(), "未知", "无时间时应返回未知")
	instance.queue_free()

func test_format_time_range_with_values() -> void:
	var instance: Control = review_panel_script.new()
	instance.review_data = {"starts_at": "2026-07-01T10:00:00Z", "ends_at": "2026-07-08T10:00:00Z"}
	var text: String = instance._format_time_range()
	assert_true(text.contains("2026-07-01T10:00:00Z"), "应包含开始时间")
	assert_true(text.contains("2026-07-08T10:00:00Z"), "应包含结束时间")
	instance.queue_free()
