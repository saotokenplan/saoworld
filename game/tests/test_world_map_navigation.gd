extends "res://addons/gut/test.gd"

func test_world_map_has_enter_region_signal() -> void:
	var world_map: Node2D = load("res://scenes/world/WorldMap.tscn").instantiate()
	assert_true(world_map.has_signal("enter_region_requested"), "世界地图应包含 enter_region_requested 信号")
	assert_true(world_map.has_signal("region_selected"), "世界地图应包含 region_selected 信号")
	assert_true(world_map.has_signal("back_to_menu"), "世界地图应包含 back_to_menu 信号")
	world_map.queue_free()

func test_world_map_enter_button_initially_hidden() -> void:
	var world_map: Node2D = load("res://scenes/world/WorldMap.tscn").instantiate()
	add_child_autofree(world_map)
	
	var enter_button: Button = world_map.get_node_or_null("EnterRegionButton")
	assert_not_null(enter_button, "世界地图应包含进入区域按钮")
	assert_false(enter_button.visible, "初始状态下进入区域按钮应隐藏")

func test_world_map_select_active_region_shows_enter_button() -> void:
	var world_map: Node2D = load("res://scenes/world/WorldMap.tscn").instantiate()
	add_child_autofree(world_map)
	
	var enter_button: Button = world_map.get_node_or_null("EnterRegionButton")
	
	world_map.load_regions([
		{
			"region_id": "region_test_active",
			"name": "活跃区域",
			"description": "测试活跃区域",
			"status": "active",
			"level_range": [1, 10]
		}
	])
	
	world_map.select_region("region_test_active")
	assert_true(enter_button.visible, "选中活跃区域后进入按钮应显示")
	assert_false(enter_button.disabled, "选中活跃区域后进入按钮应可用")

func test_world_map_select_locked_region_hides_enter_button() -> void:
	var world_map: Node2D = load("res://scenes/world/WorldMap.tscn").instantiate()
	add_child_autofree(world_map)
	
	var enter_button: Button = world_map.get_node_or_null("EnterRegionButton")
	
	world_map.load_regions([
		{
			"region_id": "region_test_locked",
			"name": "锁定区域",
			"description": "测试锁定区域",
			"status": "locked",
			"level_range": [1, 10]
		}
	])
	
	world_map.select_region("region_test_locked")
	assert_false(enter_button.visible, "选中锁定区域后进入按钮应隐藏")

func test_world_map_enter_region_emits_signal() -> void:
	var world_map: Node2D = load("res://scenes/world/WorldMap.tscn").instantiate()
	add_child_autofree(world_map)
	
	var signals_received: Array = []
	world_map.enter_region_requested.connect(func(region_id: String):
		signals_received.append(region_id)
	)
	
	world_map.load_regions([
		{
			"region_id": "region_test_active",
			"name": "活跃区域",
			"description": "测试活跃区域",
			"status": "active",
			"level_range": [1, 10]
		}
	])
	
	world_map.select_region("region_test_active")
	world_map._on_enter_region_button_pressed()
	
	assert_eq(signals_received.size(), 1, "点击进入区域按钮应发射信号")
	assert_eq(signals_received[0], "region_test_active", "信号应传递选中的区域 ID")
