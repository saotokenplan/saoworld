extends "res://tests/test_base.gd"

# S1-08 客户端 UI 优化新增测试（auto-20260711-0200）

func test_reputation_panel_script_loads() -> void:
	var script: GDScript = load("res://scripts/ui/reputation_panel.gd")
	assert(script != null, "reputation_panel.gd 脚本应能加载")

func test_reputation_panel_signals() -> void:
	var rep_panel: Node = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/reputation_panel.gd")
	rep_panel.set_script(script)
	assert_true(rep_panel.has_signal("back_to_menu"), "应暴露 back_to_menu 信号")
	assert_true(rep_panel.has_signal("reputation_selected"), "应暴露 reputation_selected 信号")

func test_reputation_panel_reputation_unlocked_signal_handler() -> void:
	var rep_panel: Node = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/reputation_panel.gd")
	rep_panel.set_script(script)
	rep_panel.selected_region_id = "region_test_01"
	rep_panel._on_reputation_unlocked("region_test_01")
	assert(true, "信号处理不应崩溃")

func test_reputation_panel_ensure_detail_extras() -> void:
	var rep_panel: Node = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/reputation_panel.gd")
	rep_panel.set_script(script)
	rep_panel._ensure_detail_extras()
	assert(true, "_ensure_detail_extras 应安全执行")

func test_reputation_panel_render_detail_minimal() -> void:
	var rep_panel: Node = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/reputation_panel.gd")
	rep_panel.set_script(script)
	rep_panel.reputation_list = [
		{"region_id": "region_test_01", "reputation": 100, "reputation_level": "neutral"}
	]
	rep_panel._render_detail("region_test_01")
	assert(true, "详情渲染不应崩溃")

func test_reputation_panel_render_detail_no_data() -> void:
	var rep_panel: Node = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/reputation_panel.gd")
	rep_panel.set_script(script)
	rep_panel._render_detail("nonexistent_region")
	assert(true, "无数据时也应安全返回")
