extends "res://tests/test_base.gd"

func test_quest_panel_structure() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	var quest_list: Node = quest_panel.get_node_or_null("QuestList")
	assert(quest_list != null)
	
	var quest_detail: Node = quest_panel.get_node_or_null("QuestDetail")
	assert(quest_detail != null)
	
	var back_button: Node = quest_panel.get_node_or_null("BackButton")
	assert(back_button != null)
	
	var accept_button: Node = quest_panel.get_node_or_null("QuestDetail/AcceptButton")
	assert(accept_button != null)

func test_quest_panel_signals() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	assert(quest_panel.has_signal("quest_selected"))
	assert(quest_panel.has_signal("back_to_menu"))
	assert(quest_panel.has_signal("open_npc_dialog"))

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

func test_quest_accept() -> void:
	var quest_panel: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_panel.gd")
	quest_panel.set_script(script)
	
	var quest: Dictionary = {
		"quest_id": "test_quest_01",
		"title": "测试任务",
		"description": "测试描述",
		"status": "available",
		"objectives": [],
		"rewards": {}
	}
	
	quest_panel.quests = [quest]
	quest_panel.selected_quest_id = "test_quest_01"
	
	quest_panel._on_accept_button_pressed()
	
	assert(quest["status"] == "active")