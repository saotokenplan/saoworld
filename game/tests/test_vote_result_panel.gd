extends Node
## VoteResultPanel GUT 测试
## 覆盖投票结果展示、百分比计算、获胜者判定逻辑

var result_panel_script: GDScript

func before_all() -> void:
	result_panel_script = load("res://scripts/ui/vote_result_panel.gd")

func test_signals_declared() -> void:
	assert_true(result_panel_script.has_signal("back_pressed"), "should have back_pressed signal")
	assert_true(result_panel_script.has_signal("view_details_pressed"), "should have view_details_pressed signal")

func test_candidate_rows_initial_empty() -> void:
	var instance: Control = result_panel_script.new()
	assert_eq(instance.candidate_rows.size(), 0, "candidate_rows should be empty initially")
	instance.queue_free()

func test_calculate_percentage_zero_total() -> void:
	var instance: Control = result_panel_script.new()
	var result: float = instance._calculate_percentage(10, 0)
	assert_eq(result, 0.0, "percentage should be 0 when total is 0")
	instance.queue_free()

func test_calculate_percentage_normal() -> void:
	var instance: Control = result_panel_script.new()
	var result: float = instance._calculate_percentage(30, 100)
	assert_eq(result, 30.0, "30 out of 100 should be 30%")
	instance.queue_free()

func test_calculate_percentage_full() -> void:
	var instance: Control = result_panel_script.new()
	var result: float = instance._calculate_percentage(100, 100)
	assert_eq(result, 100.0, "100 out of 100 should be 100%")
	instance.queue_free()

func test_calculate_percentage_zero_votes() -> void:
	var instance: Control = result_panel_script.new()
	var result: float = instance._calculate_percentage(0, 100)
	assert_eq(result, 0.0, "0 out of 100 should be 0%")
	instance.queue_free()

func test_find_winner_empty_list() -> void:
	var instance: Control = result_panel_script.new()
	var winner: Dictionary = instance._find_winner([])
	assert_true(winner.is_empty(), "winner should be empty for empty list")
	instance.queue_free()

func test_find_winner_single_candidate() -> void:
	var instance: Control = result_panel_script.new()
	var candidates: Array[Dictionary] = [{"candidate_id": "c1", "title": "A", "vote_count": 10}]
	var winner: Dictionary = instance._find_winner(candidates)
	assert_eq(winner.get("candidate_id", ""), "c1", "single candidate should be winner")
	instance.queue_free()

func test_find_winner_multiple_candidates() -> void:
	var instance: Control = result_panel_script.new()
	var candidates: Array[Dictionary] = [
		{"candidate_id": "c1", "title": "A", "vote_count": 10},
		{"candidate_id": "c2", "title": "B", "vote_count": 25},
		{"candidate_id": "c3", "title": "C", "vote_count": 15}
	]
	var winner: Dictionary = instance._find_winner(candidates)
	assert_eq(winner.get("candidate_id", ""), "c2", "candidate with most votes should win")
	instance.queue_free()

func test_find_winner_tie_returns_first() -> void:
	var instance: Control = result_panel_script.new()
	var candidates: Array[Dictionary] = [
		{"candidate_id": "c1", "title": "A", "vote_count": 20},
		{"candidate_id": "c2", "title": "B", "vote_count": 20}
	]
	var winner: Dictionary = instance._find_winner(candidates)
	assert_eq(winner.get("candidate_id", ""), "c1", "first candidate wins in tie")
	instance.queue_free()

func test_calculate_total_votes_empty() -> void:
	var instance: Control = result_panel_script.new()
	var total: int = instance._calculate_total_votes([])
	assert_eq(total, 0, "total should be 0 for empty list")
	instance.queue_free()

func test_calculate_total_votes_multiple() -> void:
	var instance: Control = result_panel_script.new()
	var candidates: Array[Dictionary] = [
		{"candidate_id": "c1", "vote_count": 10},
		{"candidate_id": "c2", "vote_count": 25},
		{"candidate_id": "c3", "vote_count": 15}
	]
	var total: int = instance._calculate_total_votes(candidates)
	assert_eq(total, 50, "total should be sum of all votes")
	instance.queue_free()

func test_calculate_percentage_with_float() -> void:
	var instance: Control = result_panel_script.new()
	var result: float = instance._calculate_percentage(1, 3)
	# 1/3*100 = 33.333...
	assert_true(result > 33.0 and result < 34.0, "1/3 should be approximately 33.3%")
	instance.queue_free()

# --- 图表绘制测试 ---

func test_draw_pie_chart_method_exists() -> void:
	var instance: Control = result_panel_script.new()
	assert_true(instance.has_method("_draw_pie_chart"), "VoteResultPanel应有_draw_pie_chart方法")
	instance.queue_free()

func test_draw_bar_chart_method_exists() -> void:
	var instance: Control = result_panel_script.new()
	assert_true(instance.has_method("_draw_bar_chart"), "VoteResultPanel应有_draw_bar_chart方法")
	instance.queue_free()

func test_on_pie_chart_button_pressed_method_exists() -> void:
	var instance: Control = result_panel_script.new()
	assert_true(instance.has_method("_on_pie_chart_button_pressed"), "VoteResultPanel应有_on_pie_chart_button_pressed方法")
	instance.queue_free()

func test_on_bar_chart_button_pressed_method_exists() -> void:
	var instance: Control = result_panel_script.new()
	assert_true(instance.has_method("_on_bar_chart_button_pressed"), "VoteResultPanel应有_on_bar_chart_button_pressed方法")
	instance.queue_free()

func test_on_chart_data_loaded_method_exists() -> void:
	var instance: Control = result_panel_script.new()
	assert_true(instance.has_method("_on_chart_data_loaded"), "VoteResultPanel应有_on_chart_data_loaded方法")
	instance.queue_free()

func test_chart_type_initial_value() -> void:
	var instance: Control = result_panel_script.new()
	assert_eq(instance.current_chart_type, "pie", "初始图表类型应为pie")
	instance.queue_free()

func test_chart_data_initial_empty() -> void:
	var instance: Control = result_panel_script.new()
	assert_eq(instance.chart_data, {}, "初始图表数据应为空字典")
	instance.queue_free()
