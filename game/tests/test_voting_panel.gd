extends Node
## VotingPanel GUT 测试
## 覆盖投票界面状态管理、候选项选择、提交按钮逻辑

var voting_panel_script: GDScript

func before_all() -> void:
	voting_panel_script = load("res://scripts/ui/voting_panel.gd")

func test_signals_declared() -> void:
	assert_true(voting_panel_script.has_signal("vote_submitted"), "should have vote_submitted signal")
	assert_true(voting_panel_script.has_signal("back_pressed"), "should have back_pressed signal")
	assert_true(voting_panel_script.has_signal("open_discussion_pressed"), "should have open_discussion_pressed signal")

func test_initial_state_fields() -> void:
	# 验证脚本定义了所需的变量
	var instance: Control = voting_panel_script.new()
	assert_eq(instance.selected_candidate_id, "", "selected_candidate_id should be empty initially")
	assert_false(instance.has_voted, "has_voted should be false initially")
	assert_false(instance.is_loading, "is_loading should be false initially")
	instance.queue_free()

func test_has_voted_changes() -> void:
	var instance: Control = voting_panel_script.new()
	instance.has_voted = true
	assert_true(instance.has_voted, "has_voted should be true after setting")
	instance.has_voted = false
	assert_false(instance.has_voted, "has_voted should be false after unsetting")
	instance.queue_free()

func test_selected_candidate_id_changes() -> void:
	var instance: Control = voting_panel_script.new()
	instance.selected_candidate_id = "candidate_1"
	assert_eq(instance.selected_candidate_id, "candidate_1", "selected_candidate_id should be updated")
	instance.queue_free()

func test_is_loading_state() -> void:
	var instance: Control = voting_panel_script.new()
	instance.is_loading = true
	assert_true(instance.is_loading, "is_loading should be true after setting")
	instance.is_loading = false
	assert_false(instance.is_loading, "is_loading should be false after unsetting")
	instance.queue_free()

func test_candidate_buttons_initial_empty() -> void:
	var instance: Control = voting_panel_script.new()
	assert_eq(instance.candidate_buttons.size(), 0, "candidate_buttons should be empty initially")
	instance.queue_free()
