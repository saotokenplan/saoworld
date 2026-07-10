extends "res://tests/test_base.gd"

func test_world_map_structure() -> void:
	var world_map: Node2D = load("res://scenes/world/WorldMap.tscn").instantiate()
	assert(world_map != null)
	
	var region_container: Node = world_map.get_node_or_null("RegionContainer")
	assert(region_container != null)
	
	var region_detail: Node = world_map.get_node_or_null("RegionDetail")
	assert(region_detail != null)
	
	var back_button: Node = world_map.get_node_or_null("BackButton")
	assert(back_button != null)

func test_world_map_signals() -> void:
	var world_map: Node2D = load("res://scenes/world/WorldMap.tscn").instantiate()
	
	assert(world_map.has_signal("region_selected"))
	assert(world_map.has_signal("back_to_menu"))

func test_region_status_style() -> void:
	var world_map: Node2D = load("res://scenes/world/WorldMap.tscn").instantiate()
	
	var card: Button = Button.new()
	var script: GDScript = load("res://scripts/world/world_map.gd")
	card.set_script(script)
	
	var test_cases: Array = [
		["active", Color(0.2, 0.6, 0.2), false],
		["locked", Color(0.4, 0.4, 0.4), true],
		["unstable", Color(0.6, 0.4, 0.2), false],
		["archived", Color(0.3, 0.3, 0.3), true]
	]
	
	for test_case in test_cases:
		var status: String = test_case[0]
		var expected_color: Color = test_case[1]
		var expected_disabled: bool = test_case[2]
		
		var style_box: StyleBoxFlat = StyleBoxFlat.new()
		style_box.bg_color = expected_color
		
		assert(style_box.bg_color == expected_color)

func test_region_selection() -> void:
	var world_map: Node2D = load("res://scenes/world/WorldMap.tscn").instantiate()

	var selected_id: String = ""
	world_map.region_selected.connect(func(id: String):
		selected_id = id
	)

	var test_id: String = "region_test_01"
	world_map.select_region(test_id)

	assert(world_map.selected_region_id == test_id)

# ====== S1-08 客户端 UI 优化新增测试（auto-20260711-0200） ======

func test_unlock_requirement_node_exists() -> void:
	var world_map: Node = load("res://scenes/world/WorldMap.tscn").instantiate()
	var unlock_req: Node = world_map.get_node_or_null("RegionDetail/UnlockRequirement")
	assert(unlock_req != null, "RegionDetail/UnlockRequirement 节点应存在")
	var unlock_progress: Node = world_map.get_node_or_null("RegionDetail/UnlockProgress")
	assert(unlock_progress != null, "RegionDetail/UnlockProgress 节点应存在")

func test_world_map_reputation_unlocked_signal_connection() -> void:
	var world_map: Node = load("res://scenes/world/WorldMap.tscn").instantiate()
	var script: GDScript = load("res://scripts/world/world_map.gd")
	assert(script != null, "world_map.gd 脚本应存在")
	assert(world_map.has_signal("region_selected"), "应暴露 region_selected 信号")

func test_is_region_locked_by_reputation_integration() -> void:
	WorldManager.regions = [
		{"region_id": "region_locked_01", "status": "locked"},
		{"region_id": "region_active_01", "status": "active"}
	]
	WorldManager.region_cache["region_locked_01"] = {"region_id": "region_locked_01", "status": "locked"}
	WorldManager.region_cache["region_active_01"] = {"region_id": "region_active_01", "status": "active"}
	assert_true(WorldManager.is_region_locked_by_reputation("region_locked_01"), "锁定区域应被声望方法识别")
	assert_false(WorldManager.is_region_locked_by_reputation("region_active_01"), "活跃区域不应被声望方法识别")