extends "res://addons/gut/test.gd"

func test_world_manager_initial_state() -> void:
	var world := WorldManager
	assert_eq(world.regions.size(), 0, "初始区域列表应为空")
	assert_eq(world.region_cache.size(), 0, "初始区域缓存应为空")
	assert_false(world.is_loading, "初始状态不应为加载中")

func test_region_status_constants() -> void:
	var world := WorldManager
	assert_true(world.REGION_STATUS.has("locked"))
	assert_true(world.REGION_STATUS.has("active"))
	assert_true(world.REGION_STATUS.has("unstable"))
	assert_true(world.REGION_STATUS.has("archived"))

func test_region_status_info() -> void:
	var world := WorldManager
	var info: Dictionary = world.get_region_status_info("active")
	assert_eq(info["name"], "活跃", "活跃状态名称正确")
	assert_eq(info["color"], "#4CAF50", "活跃状态颜色正确")

func test_get_region_status_info_unknown() -> void:
	var world := WorldManager
	var info: Dictionary = world.get_region_status_info("unknown_status")
	assert_eq(info["name"], "unknown_status", "未知状态应返回原状态名")

func test_is_region_active() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_001", "status": "active"}]
	assert_true(world.is_region_active("region_001"), "活跃区域应返回 true")
	assert_false(world.is_region_active("region_999"), "不存在的区域应返回 false")

func test_is_region_locked() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_001", "status": "locked"}]
	assert_true(world.is_region_locked("region_001"), "锁定区域应返回 true")
	assert_false(world.is_region_locked("region_999"), "不存在的区域应返回 false")

func test_get_region_by_id_from_cache() -> void:
	var world := WorldManager
	world.region_cache["region_001"] = {"region_id": "region_001", "name": "Test Region"}
	var region: Dictionary = world.get_region_by_id("region_001")
	assert_eq(region["region_id"], "region_001", "应从缓存获取区域")

func test_get_region_by_id_from_list() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_001", "name": "Test Region"}]
	var region: Dictionary = world.get_region_by_id("region_001")
	assert_eq(region["region_id"], "region_001", "应从列表获取区域")

func test_get_regions_by_status() -> void:
	var world := WorldManager
	world.regions = [
		{"region_id": "region_001", "status": "active"},
		{"region_id": "region_002", "status": "active"},
		{"region_id": "region_003", "status": "locked"}
	]
	var active_regions: Array[Dictionary] = world.get_regions_by_status("active")
	assert_eq(active_regions.size(), 2, "应返回 2 个活跃区域")

func test_get_active_regions() -> void:
	var world := WorldManager
	world.regions = [
		{"region_id": "region_001", "status": "active"},
		{"region_id": "region_002", "status": "locked"}
	]
	var active: Array[Dictionary] = world.get_active_regions()
	assert_eq(active.size(), 1, "应返回 1 个活跃区域")

func test_clear_cache() -> void:
	var world := WorldManager
	world.region_cache["region_001"] = {"region_id": "region_001"}
	world.clear_cache()
	assert_eq(world.region_cache.size(), 0, "缓存应被清除")

func test_reset() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_001"}]
	world.region_cache["region_001"] = {"region_id": "region_001"}
	world.is_loading = true
	world.last_error = {"code": "TEST_ERROR"}
	world.reset()
	assert_eq(world.regions.size(), 0)
	assert_eq(world.region_cache.size(), 0)
	assert_false(world.is_loading)
	assert_eq(world.last_error.size(), 0)