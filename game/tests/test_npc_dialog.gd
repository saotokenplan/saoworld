extends GutTest

var dialog: Node = null
const DIALOG_SCENE: PackedScene = preload("res://scenes/ui/npc/NPCDialog.tscn")

func before_each() -> void:
	if DIALOG_SCENE:
		dialog = DIALOG_SCENE.instantiate()
		add_child(dialog)

func after_each() -> void:
	if is_instance_valid(dialog):
		dialog.queue_free()

func test_dialog_scene_loads() -> void:
	assert_not_null(dialog, "NPCDialog 场景应能正常加载")

func test_dialog_initial_state() -> void:
	assert_false(dialog.visible, "对话框初始应为隐藏状态")

func test_open_dialog_with_tree_data() -> void:
	var npc_data: Dictionary = {
		"npc_id": "npc_test_01",
		"name": "测试NPC",
		"title": "测试头衔",
		"dialog_tree": {
			"start": "first_meet",
			"nodes": {
				"first_meet": {
					"id": "first_meet",
					"text": "欢迎来到测试区域！",
					"speaker": "npc",
					"choices": [
						{"text": "你好", "next": "greet"},
						{"text": "告辞", "next": "goodbye"}
					]
				},
				"greet": {
					"id": "greet",
					"text": "很高兴见到你，旅行者。",
					"speaker": "npc",
					"choices": [
						{"text": "告辞", "next": "goodbye"}
					]
				},
				"goodbye": {
					"id": "goodbye",
					"text": "",
					"speaker": "npc",
					"choices": [],
					"is_end": true
				}
			}
		}
	}

	dialog.open_dialog(npc_data)
	assert_true(dialog.visible, "打开对话后应可见")
	assert_eq(dialog.get_current_node_id(), "first_meet", "初始节点应为 first_meet")

func test_dialog_tree_branching() -> void:
	var npc_data: Dictionary = {
		"npc_id": "npc_test_02",
		"name": "分支测试NPC",
		"title": "测试",
		"dialog_tree": {
			"start": "start",
			"nodes": {
				"start": {
					"id": "start",
					"text": "请选择你的道路。",
					"speaker": "npc",
					"choices": [
						{"text": "光明之路", "next": "light"},
						{"text": "黑暗之路", "next": "dark"}
					]
				},
				"light": {
					"id": "light",
					"text": "你选择了光明。",
					"speaker": "npc",
					"choices": [
						{"text": "确认", "next": "end"}
					]
				},
				"dark": {
					"id": "dark",
					"text": "你选择了黑暗。",
					"speaker": "npc",
					"choices": [
						{"text": "确认", "next": "end"}
					]
				},
				"end": {
					"id": "end",
					"text": "",
					"speaker": "npc",
					"choices": [],
					"is_end": true
				}
			}
		}
	}

	dialog.open_dialog(npc_data)
	assert_eq(dialog.get_current_node_id(), "start")
	watch_signals(dialog)
	
	dialog._on_choice_selected(0)
	assert_signal_emitted(dialog, "accept_quest", 0)
	assert_eq(dialog.get_current_node_id(), "light", "选择光明后节点应跳转到 light")

func test_dialog_quest_trigger() -> void:
	var npc_data: Dictionary = {
		"npc_id": "npc_test_03",
		"name": "任务NPC",
		"title": "任务发布者",
		"related_quests": ["quest_test_01"],
		"dialog_tree": {
			"start": "start",
			"nodes": {
				"start": {
					"id": "start",
					"text": "我有一个任务给你。",
					"speaker": "npc",
					"quest_trigger": "quest_test_01",
					"choices": [
						{"text": "接受", "next": "accepted", "action": "accept_quest"},
						{"text": "拒绝", "next": "refused"}
					]
				},
				"accepted": {
					"id": "accepted",
					"text": "太好了，任务已接取。",
					"speaker": "npc",
					"choices": [
						{"text": "告辞", "next": "goodbye"}
					]
				},
				"refused": {
					"id": "refused",
					"text": "好的，下次再来。",
					"speaker": "npc",
					"choices": [
						{"text": "告辞", "next": "goodbye"}
					]
				},
				"goodbye": {
					"id": "goodbye",
					"text": "",
					"speaker": "npc",
					"choices": [],
					"is_end": true
				}
			}
		}
	}

	dialog.open_dialog(npc_data)
	watch_signals(dialog)
	
	dialog._on_choice_selected(0)
	assert_signal_emitted(dialog, "accept_quest", 1)
	assert_signal_emit_parameters(dialog, "accept_quest", ["quest_test_01"])

func test_dialog_fallback_linear_mode() -> void:
	var npc_data: Dictionary = {
		"npc_id": "npc_test_linear",
		"name": "线性对话NPC",
		"title": "测试",
		"dialogs": [
			{"id": "dia1", "text": "第一句话。", "condition": "default"},
			{"id": "dia2", "text": "第二句话。", "condition": "default"}
		]
	}

	dialog.open_dialog(npc_data)
	assert_true(dialog.visible, "线性模式也应显示对话框")

func test_empty_npc_data_handling() -> void:
	var empty_npc: Dictionary = {}
	dialog.open_dialog(empty_npc)
	assert_false(dialog.visible, "空 NPC 数据不应显示对话框或立即关闭")

func test_met_npcs_tracking() -> void:
	var npc_data: Dictionary = {
		"npc_id": "npc_met_test",
		"name": "首次见面测试",
		"title": "测试",
		"dialog_tree": {
			"start": "first_meet",
			"nodes": {
				"first_meet": {
					"id": "first_meet",
					"text": "初次见面！",
					"speaker": "npc",
					"choices": [
						{"text": "再见", "next": "goodbye"}
					]
				},
				"default": {
					"id": "default",
					"text": "又见面了。",
					"speaker": "npc",
					"choices": [
						{"text": "再见", "next": "goodbye"}
					]
				},
				"goodbye": {
					"id": "goodbye",
					"text": "",
					"speaker": "npc",
					"choices": [],
					"is_end": true
				}
			}
		}
	}

	dialog.open_dialog(npc_data)
	var first_node: String = dialog.get_current_node_id()
	assert_eq(first_node, "first_meet", "第一次见面应进入 first_meet 节点")

	var met: Dictionary = dialog.get_met_npcs()
	assert_true(met.has("npc_met_test"), "应记录已见面的 NPC")

func test_dialog_close_signal() -> void:
	var npc_data: Dictionary = {
		"npc_id": "npc_close_test",
		"name": "关闭测试",
		"title": "测试",
		"dialog_tree": {
			"start": "start",
			"nodes": {
				"start": {
					"id": "start",
					"text": "测试文本",
					"speaker": "npc",
					"choices": [
						{"text": "关闭", "next": "goodbye"}
					]
				},
				"goodbye": {
					"id": "goodbye",
					"text": "",
					"speaker": "npc",
					"choices": [],
					"is_end": true
				}
			}
		}
	}

	dialog.open_dialog(npc_data)
	watch_signals(dialog)
	
	dialog._on_choice_selected(0)
	assert_signal_emitted(dialog, "dialog_closed", 1)
	assert_false(dialog.visible, "关闭后对话框应隐藏")

func test_set_met_npcs_persistence() -> void:
	var pre_met: Dictionary = {"npc_old": true}
	dialog.set_met_npcs(pre_met)
	
	var current: Dictionary = dialog.get_met_npcs()
	assert_true(current.has("npc_old"), "预设的 met_npcs 应保留")

func test_get_current_quest_trigger_no_trigger() -> void:
	var npc_data: Dictionary = {
		"npc_id": "npc_no_trigger",
		"name": "无触发器NPC",
		"title": "测试",
		"dialog_tree": {
			"start": "start",
			"nodes": {
				"start": {
					"id": "start",
					"text": "没有触发器的对话。",
					"speaker": "npc",
					"choices": [
						{"text": "结束", "next": "goodbye"}
					]
				},
				"goodbye": {
					"id": "goodbye",
					"text": "",
					"speaker": "npc",
					"choices": [],
					"is_end": true
				}
			}
		}
	}

	dialog.open_dialog(npc_data)
	var trigger: String = dialog.get_current_quest_trigger()
	assert_eq(trigger, "", "无触发器时应返回空字符串")
