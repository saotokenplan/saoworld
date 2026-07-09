extends "res://addons/gut/test.gd"

func test_core_region_scene_structure() -> void:
	var region: Node2D = load("res://scenes/world/CoreRegion.tscn").instantiate()
	assert_not_null(region.get_node_or_null("Ground"), "区域场景应包含地面节点")
	assert_not_null(region.get_node_or_null("Obstacles"), "区域场景应包含障碍物节点")
	assert_not_null(region.get_node_or_null("Boundaries"), "区域场景应包含边界节点")
	assert_not_null(region.get_node_or_null("BackButton"), "区域场景应包含返回按钮")
	assert_not_null(region.get_node_or_null("TitleLabel"), "区域场景应包含标题标签")
	region.queue_free()

func test_core_region_spawns_player() -> void:
	var region: Node2D = load("res://scenes/world/CoreRegion.tscn").instantiate()
	add_child_autofree(region)
	
	var player: CharacterBody2D = region.get_player()
	assert_not_null(player, "区域应实例化玩家角色")
	assert_is(player, CharacterBody2D, "玩家应为 CharacterBody2D 类型")

func test_core_region_enter_signal() -> void:
	var region: Node2D = load("res://scenes/world/CoreRegion.tscn").instantiate()
	
	var signals_received: Array = []
	region.region_entered.connect(func(region_id: String):
		signals_received.append(region_id)
	)
	
	add_child_autofree(region)
	
	assert_eq(signals_received.size(), 1, "进入区域时应发射 region_entered 信号")
	assert_eq(signals_received[0], "region_core_ironward", "信号应传递默认区域 ID")

func test_core_region_back_signal() -> void:
	var region: Node2D = load("res://scenes/world/CoreRegion.tscn").instantiate()
	add_child_autofree(region)
	
	var signals_received: Array = []
	region.back_to_world_map.connect(func():
		signals_received.append("back_to_world_map")
	)
	
	region._on_back_button_pressed()
	assert_eq(signals_received.size(), 1, "点击返回按钮应发射 back_to_world_map 信号")

func test_core_region_set_data() -> void:
	var region: Node2D = load("res://scenes/world/CoreRegion.tscn").instantiate()
	add_child_autofree(region)
	
	var test_data: Dictionary = {
		"region_id": "region_test_01",
		"name": "测试区域"
	}
	region.set_region_data(test_data)
	
	assert_eq(region.region_id, "region_test_01", "区域 ID 应更新")
	assert_eq(region.region_name, "测试区域", "区域名称应更新")
