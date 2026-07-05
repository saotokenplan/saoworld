extends "res://addons/gut/test.gd"

func test_dialog_flow_with_multiple_lines() -> void:
	var dialog: NPCDialog = NPCDialog.new()
	var npc_data: Dictionary = {
		"name": "测试NPC",
		"dialogs": [
			{"text": "你好，旅行者。"},
			{"text": "欢迎来到我们的村庄。"},
			{"text": "有什么我可以帮助你的吗？"}
		]
	}
	
	dialog.open_dialog(npc_data)
	assert_eq(dialog.current_npc.get("name"), "测试NPC", "NPC名称应正确设置")
	assert_eq(dialog.current_dialog_index, 0, "初始对话索引应为0")
	
	var signals_received: Array = []
	dialog.dialog_closed.connect(func():
		signals_received.append("dialog_closed")
	)
	
	dialog._on_next_button_pressed()
	assert_eq(dialog.current_dialog_index, 1, "点击继续后索引应为1")
	
	dialog._on_next_button_pressed()
	assert_eq(dialog.current_dialog_index, 2, "再次点击继续后索引应为2")
	
	dialog._on_next_button_pressed()
	assert_eq(signals_received.size(), 1, "对话结束时应发射 dialog_closed 信号")
	assert_eq(signals_received[0], "dialog_closed", "信号应为 dialog_closed")

func test_dialog_flow_with_quest_offer() -> void:
	var dialog: NPCDialog = NPCDialog.new()
	var npc_data: Dictionary = {
		"name": "任务NPC",
		"dialogs": [
			{"text": "你看起来很强大。"},
			{"text": "我有一个任务需要你帮忙。", "quest_id": "quest_test_01"}
		]
	}
	
	dialog.open_dialog(npc_data)
	assert_eq(dialog.current_dialog_index, 0, "初始对话索引应为0")
	
	dialog._on_next_button_pressed()
	assert_eq(dialog.current_dialog_index, 1, "点击继续后索引应为1")
	assert_eq(dialog.current_quest_id, "quest_test_01", "当前任务ID应正确设置")
	
	var signals_received: Array = []
	dialog.accept_quest.connect(func(quest_id: String):
		signals_received.append({"signal": "accept_quest", "quest_id": quest_id})
	)
	dialog.dialog_closed.connect(func():
		signals_received.append("dialog_closed")
	)
	
	dialog._on_accept_quest_button_pressed()
	assert_eq(signals_received.size(), 2, "接受任务时应发射 accept_quest 和 dialog_closed 信号")
	assert_eq(signals_received[0]["signal"], "accept_quest", "第一个信号应为 accept_quest")
	assert_eq(signals_received[0]["quest_id"], "quest_test_01", "任务ID应正确传递")
	assert_eq(signals_received[1], "dialog_closed", "第二个信号应为 dialog_closed")

func test_dialog_close_button() -> void:
	var dialog: NPCDialog = NPCDialog.new()
	var npc_data: Dictionary = {
		"name": "关闭测试NPC",
		"dialogs": [{"text": "按关闭按钮试试。"}]
	}
	
	dialog.open_dialog(npc_data)
	
	var signals_received: Array = []
	dialog.dialog_closed.connect(func():
		signals_received.append("dialog_closed")
	)
	
	dialog._on_close_button_pressed()
	assert_eq(signals_received.size(), 1, "点击关闭按钮应发射 dialog_closed 信号")

func test_empty_dialogs() -> void:
	var dialog: NPCDialog = NPCDialog.new()
	var npc_data: Dictionary = {
		"name": "无声NPC",
		"dialogs": []
	}
	
	dialog.open_dialog(npc_data)
	assert_eq(dialog.current_dialog_index, 0, "初始对话索引应为0")
	
	var signals_received: Array = []
	dialog.dialog_closed.connect(func():
		signals_received.append("dialog_closed")
	)
	
	dialog._show_current_dialog()
	assert_eq(signals_received.size(), 1, "空对话应立即结束并发射 dialog_closed 信号")

func test_dialog_without_quest() -> void:
	var dialog: NPCDialog = NPCDialog.new()
	var npc_data: Dictionary = {
		"name": "普通NPC",
		"dialogs": [{"text": "只是打个招呼。"}]
	}
	
	dialog.open_dialog(npc_data)
	assert_eq(dialog.current_quest_id, "", "无任务时 quest_id 应为空")
	
	var signals_received: Array = []
	dialog.accept_quest.connect(func(quest_id: String):
		signals_received.append(quest_id)
	)
	
	dialog._on_next_button_pressed()
	assert_eq(signals_received.size(), 0, "无任务时不应发射 accept_quest 信号")