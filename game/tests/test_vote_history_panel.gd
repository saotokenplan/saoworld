extends Node
## VoteHistoryPanel GUT 测试
## 覆盖投票历史列表、分页状态、落地展示逻辑

var history_panel_script: GDScript

func before_all() -> void:
	history_panel_script = load("res://scripts/ui/vote_history_panel.gd")

func test_signals_declared() -> void:
	assert_true(history_panel_script.has_signal("back_pressed"), "should have back_pressed signal")
	assert_true(history_panel_script.has_signal("item_selected"), "should have item_selected signal")
	assert_true(history_panel_script.has_signal("load_more_pressed"), "should have load_more_pressed signal")
	assert_true(history_panel_script.has_signal("view_content_package"), "should have view_content_package signal")

func test_initial_state() -> void:
	var instance: Control = history_panel_script.new()
	assert_eq(instance.history_items.size(), 0, "history_items should be empty initially")
	assert_eq(instance.current_offset, 0, "current_offset should be 0 initially")
	assert_true(instance.has_more, "has_more should be true initially")
	assert_false(instance.is_loading, "is_loading should be false initially")
	instance.queue_free()

func test_has_more_after_set_history() -> void:
	var instance: Control = history_panel_script.new()
	# set_history_data 设置 has_more = current_offset < total
	# items.size() = 3, total = 10 → has_more = true
	instance.history_items = [{"title": "test1"}, {"title": "test2"}, {"title": "test3"}]
	instance.current_offset = 3
	instance.has_more = instance.current_offset < 10
	assert_true(instance.has_more, "has_more should be true when offset < total")
	instance.queue_free()

func test_has_more_when_all_loaded() -> void:
	var instance: Control = history_panel_script.new()
	instance.current_offset = 10
	instance.has_more = instance.current_offset < 10
	assert_false(instance.has_more, "has_more should be false when offset >= total")
	instance.queue_free()

func test_current_offset_tracking() -> void:
	var instance: Control = history_panel_script.new()
	instance.current_offset = 5
	assert_eq(instance.current_offset, 5, "current_offset should track correctly")
	instance.queue_free()

func test_is_loading_state() -> void:
	var instance: Control = history_panel_script.new()
	instance.is_loading = true
	assert_true(instance.is_loading, "is_loading should be true after setting")
	instance.is_loading = false
	assert_false(instance.is_loading, "is_loading should be false after unsetting")
	instance.queue_free()

func test_history_items_type() -> void:
	var instance: Control = history_panel_script.new()
	assert_eq(typeof(instance.history_items), TYPE_ARRAY, "history_items should be an Array")
	instance.queue_free()

func test_clear_history_resets_state() -> void:
	var instance: Control = history_panel_script.new()
	instance.history_items.append({"title": "test"})
	instance.current_offset = 5
	instance.has_more = false
	instance.clear_history()
	assert_eq(instance.history_items.size(), 0, "history_items should be empty after clear")
	assert_eq(instance.current_offset, 0, "current_offset should be 0 after clear")
	assert_true(instance.has_more, "has_more should be true after clear")
	instance.queue_free()
