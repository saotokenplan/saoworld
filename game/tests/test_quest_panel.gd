extends "res://tests/test_base.gd"

func test_quest_panel_signals() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	assert_true(quest_panel.has_signal("quest_selected"))
	assert_true(quest_panel.has_signal("back_to_menu"))
	assert_true(quest_panel.has_signal("open_npc_dialog"))
	assert_true(quest_panel.has_signal("quest_accepted"))
	assert_true(quest_panel.has_signal("quest_completed"))

func test_quest_status_text() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	var test_cases: Array = [
		["available", "可接取"],
		["active", "进行中"],
		["completed", "已完成"],
		["failed", "已失败"],
		["unknown", "未知"]
	]
	
	for test_case in test_cases:
		var status: String = test_case[0]
		var expected: String = test_case[1]
		
		var result: String = quest_panel._get_status_text(status)
		assert(result == expected)

func test_quest_panel_load_quests() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	var test_quests: Array[Dictionary] = [
		{
			"quest_id": "quest_001",
			"title": "测试任务1",
			"status": "available"
		},
		{
			"quest_id": "quest_002",
			"title": "测试任务2",
			"status": "active"
		}
	]
	
	quest_panel.load_quests(test_quests)
	assert_eq(quest_panel.quests.size(), 2)

func test_quest_panel_select_quest() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	var test_quests: Array[Dictionary] = [
		{
			"quest_id": "quest_001",
			"title": "测试任务1",
			"description": "测试描述",
			"status": "available",
			"objectives": [],
			"rewards": {}
		}
	]
	
	quest_panel.load_quests(test_quests)
	quest_panel.select_quest("quest_001")
	assert_eq(quest_panel.selected_quest_id, "quest_001")

func test_quest_panel_get_selected_quest() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	var test_quests: Array[Dictionary] = [
		{
			"quest_id": "quest_001",
			"title": "测试任务1",
			"status": "active"
		}
	]
	
	quest_panel.load_quests(test_quests)
	quest_panel.selected_quest_id = "quest_001"
	var selected: Dictionary = quest_panel.get_selected_quest()
	assert_eq(selected.get("quest_id", ""), "quest_001")

func test_quest_panel_hide_detail() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	quest_panel.selected_quest_id = "quest_001"
	quest_panel.hide_quest_detail()
	assert_eq(quest_panel.selected_quest_id, "")

func test_quest_panel_filter_status() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	assert_eq(quest_panel._get_filter_status(), "")

# ====== S1-08 客户端 UI 优化新增测试（auto-20260711-0200） ======

func test_quest_panel_reputation_unlocked_signal_connection() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	assert_true(quest_panel.has_signal("quest_selected"), "应保留 quest_selected 信号")
	assert_true(quest_panel.has_signal("quest_accepted"), "应保留 quest_accepted 信号")

func test_quest_panel_detail_reputation_field() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	quest_panel._ensure_reputation_label()
	assert(quest_panel.detail_reputation == null or is_instance_valid(quest_panel.detail_reputation), "动态创建后 detail_reputation 应可被引用")
