extends Node
## NPCPanel GUT 测试
## 覆盖 NPC 列表加载、选择信号

var npc_panel_script: GDScript

func before_all() -> void:
	npc_panel_script = load("res://scripts/ui/npc_panel.gd")

func test_signals_declared() -> void:
	assert_true(npc_panel_script.has_signal("npc_selected"), "should have npc_selected signal")
	assert_true(npc_panel_script.has_signal("back_to_menu"), "should have back_to_menu signal")

func test_npcs_initial_empty() -> void:
	var instance: PanelContainer = npc_panel_script.new()
	assert_eq(instance.npcs.size(), 0, "npcs should be empty initially")
	instance.queue_free()

func test_load_npcs_sets_data() -> void:
	var instance: PanelContainer = npc_panel_script.new()
	var test_npcs: Array[Dictionary] = [
		{"npc_id": "npc_1", "name": "Test NPC 1", "role": "Blacksmith"},
		{"npc_id": "npc_2", "name": "Test NPC 2", "role": "Merchant"}
	]
	instance.load_npcs(test_npcs)
	assert_eq(instance.npcs.size(), 2, "npcs should have 2 items after loading")
	assert_eq(instance.npcs[0].get("npc_id", ""), "npc_1", "first npc should be npc_1")
	assert_eq(instance.npcs[1].get("npc_id", ""), "npc_2", "second npc should be npc_2")
	instance.queue_free()

func test_load_npcs_overwrites_previous() -> void:
	var instance: PanelContainer = npc_panel_script.new()
	instance.load_npcs([{"npc_id": "npc_1", "name": "A", "role": "B"}])
	instance.load_npcs([{"npc_id": "npc_2", "name": "C", "role": "D"}])
	assert_eq(instance.npcs.size(), 1, "npcs should be overwritten, not appended")
	assert_eq(instance.npcs[0].get("npc_id", ""), "npc_2", "npc should be the new one")
	instance.queue_free()

func test_load_npcs_empty_list() -> void:
	var instance: PanelContainer = npc_panel_script.new()
	instance.load_npcs([])
	assert_eq(instance.npcs.size(), 0, "npcs should be empty when loading empty list")
	instance.queue_free()
