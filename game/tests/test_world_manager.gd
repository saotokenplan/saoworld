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

func test_region_type_constants() -> void:
	var world := WorldManager
	assert_true(world.REGION_TYPE.has("core"), "应包含核心区域类型")
	assert_true(world.REGION_TYPE.has("expansion"), "应包含扩展区域类型")

func test_get_region_type_info() -> void:
	var world := WorldManager
	var info: Dictionary = world.get_region_type_info("core")
	assert_eq(info["name"], "核心区域", "核心区域名称正确")
	assert_eq(info["icon"], "🏰", "核心区域图标正确")

func test_get_region_type_info_unknown() -> void:
	var world := WorldManager
	var info: Dictionary = world.get_region_type_info("unknown")
	assert_eq(info["name"], "unknown", "未知类型应返回原类型名")

func test_get_regions_by_chapter() -> void:
	var world := WorldManager
	world.regions = [
		{"region_id": "region_001", "chapter_id": "ch01"},
		{"region_id": "region_002", "chapter_id": "ch01"},
		{"region_id": "region_003", "chapter_id": "ch02"}
	]
	var ch01_regions: Array[Dictionary] = world.get_regions_by_chapter("ch01")
	assert_eq(ch01_regions.size(), 2, "应返回 2 个 ch01 区域")

func test_get_regions_by_type() -> void:
	var world := WorldManager
	world.regions = [
		{"region_id": "region_001", "type": "core"},
		{"region_id": "region_002", "type": "expansion"},
		{"region_id": "region_003", "type": "expansion"}
	]
	var core_regions: Array[Dictionary] = world.get_regions_by_type("core")
	assert_eq(core_regions.size(), 1, "应返回 1 个核心区域")

func test_is_region_unlocked_active() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_001", "status": "active"}]
	assert_true(world.is_region_unlocked("region_001"), "活跃区域应视为已解锁")

func test_is_region_unlocked_locked() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_001", "status": "locked"}]
	assert_false(world.is_region_unlocked("region_001"), "锁定区域应视为未解锁")

func test_get_unlocked_region_count() -> void:
	var world := WorldManager
	world.regions = [
		{"region_id": "region_001", "status": "active"},
		{"region_id": "region_002", "status": "active"},
		{"region_id": "region_003", "status": "locked"}
	]
	assert_eq(world.get_unlocked_region_count(), 2, "应返回 2 个已解锁区域")

func test_get_region_progression() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_001", "quest_count": 5}]
	var progression: Dictionary = world.get_region_progression("region_001")
	assert_eq(progression["total_quests"], 5, "总任务数正确")

func test_get_region_progression_no_region() -> void:
	var world := WorldManager
	var progression: Dictionary = world.get_region_progression("nonexistent")
	assert_eq(progression["completed_quests"], 0, "不存在的区域应返回 0")

func test_get_region_reputation() -> void:
	var world := WorldManager
	assert_eq(world.get_region_reputation("region_001"), 0, "默认声望值应为 0")

func test_search_regions_by_name() -> void:
	var world := WorldManager
	world.regions = [
		{"region_id": "region_001", "name": "铁卫城周边", "description": "测试区域"},
		{"region_id": "region_002", "name": "灰谷废墟", "description": "测试区域"}
	]
	var results: Array[Dictionary] = world.search_regions("铁卫")
	assert_eq(results.size(), 1, "应找到 1 个匹配区域")

func test_search_regions_by_description() -> void:
	var world := WorldManager
	world.regions = [
		{"region_id": "region_001", "name": "测试区域", "description": "包含搜索关键词"},
		{"region_id": "region_002", "name": "其他区域", "description": "不包含"}
	]
	var results: Array[Dictionary] = world.search_regions("搜索关键词")
	assert_eq(results.size(), 1, "应通过描述找到匹配区域")

func test_search_regions_empty() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_001", "name": "测试区域"}]
	var results: Array[Dictionary] = world.search_regions("")
	assert_eq(results.size(), 0, "空查询应返回空结果")

func test_sort_regions_by_name() -> void:
	var world := WorldManager
	world.regions = [
		{"region_id": "region_001", "name": "B区域"},
		{"region_id": "region_002", "name": "A区域"},
		{"region_id": "region_003", "name": "C区域"}
	]
	var sorted_regions: Array[Dictionary] = world.sort_regions("name", true)
	assert_eq(sorted_regions[0]["name"], "A区域", "应按名称升序排序")

func test_sort_regions_descending() -> void:
	var world := WorldManager
	world.regions = [
		{"region_id": "region_001", "name": "B区域"},
		{"region_id": "region_002", "name": "A区域"}
	]
	var sorted_regions: Array[Dictionary] = world.sort_regions("name", false)
	assert_eq(sorted_regions[0]["name"], "B区域", "应按名称降序排序")

func test_npc_cache_initial_state() -> void:
	var world := WorldManager
	assert_eq(world.npc_cache.size(), 0, "初始 NPC 缓存应为空")
	assert_eq(world.npc_list.size(), 0, "初始 NPC 列表应为空")

func test_get_npc_by_id_from_cache() -> void:
	var world := WorldManager
	world.npc_cache["npc_test_01"] = {"npc_id": "npc_test_01", "name": "测试NPC"}
	var npc: Dictionary = world.get_npc_by_id("npc_test_01")
	assert_eq(npc["npc_id"], "npc_test_01", "应从缓存获取 NPC")

func test_get_npc_by_id_not_found() -> void:
	var world := WorldManager
	var npc: Dictionary = world.get_npc_by_id("nonexistent")
	assert_eq(npc.size(), 0, "不存在的 NPC 应返回空字典")

func test_get_npcs_by_region() -> void:
	var world := WorldManager
	world.npc_list = [
		{"npc_id": "npc_01", "location": "loc_ironward_city"},
		{"npc_id": "npc_02", "location": "loc_ironward_city"},
		{"npc_id": "npc_03", "location": "loc_grayvalley_center"}
	]
	var npcs: Array[Dictionary] = world.get_npcs_by_region("loc_ironward_city")
	assert_eq(npcs.size(), 2, "应返回 2 个铁卫城 NPC")

func test_get_npcs_by_faction() -> void:
	var world := WorldManager
	world.npc_list = [
		{"npc_id": "npc_01", "faction": "faction_ironward"},
		{"npc_id": "npc_02", "faction": "faction_ironward"},
		{"npc_id": "npc_03", "faction": "faction_harvest"}
	]
	var npcs: Array[Dictionary] = world.get_npcs_by_faction("faction_ironward")
	assert_eq(npcs.size(), 2, "应返回 2 个铁卫联盟 NPC")

func test_get_npc_count() -> void:
	var world := WorldManager
	world.npc_list = [
		{"npc_id": "npc_01"},
		{"npc_id": "npc_02"},
		{"npc_id": "npc_03"}
	]
	assert_eq(world.get_npc_count(), 3, "应返回 3 个 NPC")

func test_clear_npc_cache() -> void:
	var world := WorldManager
	world.npc_cache["npc_01"] = {"npc_id": "npc_01"}
	world.npc_list = [{"npc_id": "npc_01"}]
	world.clear_npc_cache()
	assert_eq(world.npc_cache.size(), 0, "NPC 缓存应被清除")
	assert_eq(world.npc_list.size(), 0, "NPC 列表应被清除")

# ====== S1-08 客户端 UI 优化新增方法测试（auto-20260711-0200） ======

func test_get_region_unlock_requirement_text_locked() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_test_01", "status": "locked"}]
	world.region_cache["region_test_01"] = {"region_id": "region_test_01", "status": "locked"}
	var text: String = world.get_region_unlock_requirement_text("region_test_01")
	assert_true(text.contains("需要声望"), "锁定区域应提示需要声望")
	assert_true(text.contains(str(PlayerManager.REGION_UNLOCK_THRESHOLD)), "应包含阈值数值")

func test_get_region_unlock_requirement_text_unlocked() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_test_01", "status": "active"}]
	world.region_cache["region_test_01"] = {"region_id": "region_test_01", "status": "active"}
	var text: String = world.get_region_unlock_requirement_text("region_test_01")
	assert_true(text.contains("已解锁"), "活跃区域应显示已解锁")

func test_get_region_reputation_progress() -> void:
	var world := WorldManager
	var progress: Dictionary = world.get_region_reputation_progress("region_test_01")
	assert_true(progress.has("current"), "进度字典应包含 current")
	assert_true(progress.has("required"), "进度字典应包含 required")
	assert_true(progress.has("progress"), "进度字典应包含 progress")
	assert_true(progress.has("unlocked"), "进度字典应包含 unlocked")
	assert_eq(progress["required"], PlayerManager.REGION_UNLOCK_THRESHOLD, "required 应为解锁阈值")
	assert_eq(progress["current"], 0, "默认 current 应为 0")
	assert_eq(progress["unlocked"], false, "默认 unlocked 应为 false")

func test_is_region_locked_by_reputation() -> void:
	var world := WorldManager
	world.regions = [{"region_id": "region_test_01", "status": "locked"}]
	world.region_cache["region_test_01"] = {"region_id": "region_test_01", "status": "locked"}
	assert_true(world.is_region_locked_by_reputation("region_test_01"), "锁定且未达阈值应返回 true")
	world.regions = [{"region_id": "region_test_01", "status": "active"}]
	world.region_cache["region_test_01"] = {"region_id": "region_test_01", "status": "active"}
	assert_false(world.is_region_locked_by_reputation("region_test_01"), "活跃区域应返回 false")
	assert_false(world.is_region_locked_by_reputation("nonexistent"), "不存在区域应返回 false")

# ====== S8-01 客户端性能优化测试（auto-20260715-0600） ======

func test_cache_ttl_constant() -> void:
	var world := WorldManager
	assert_eq(world.CACHE_TTL_SECONDS, 300, "缓存 TTL 应为 300 秒（5分钟）")

func test_invalidate_cache_all() -> void:
	var world := WorldManager
	world._cache_timestamps["regions"] = 1000
	world._cache_timestamps["npcs"] = 2000
	world.invalidate_cache()
	assert_eq(world._cache_timestamps.size(), 0, "清空所有缓存后时间戳应为空")

func test_invalidate_cache_specific() -> void:
	var world := WorldManager
	world._cache_timestamps["regions"] = 1000
	world._cache_timestamps["npcs"] = 2000
	world.invalidate_cache("regions")
	assert_false(world._cache_timestamps.has("regions"), "应清除指定缓存")
	assert_true(world._cache_timestamps.has("npcs"), "不应清除其他缓存")

func test_is_cache_valid_fresh() -> void:
	var world := WorldManager
	world._cache_timestamps["regions"] = Time.get_unix_time_from_system()
	assert_true(world._is_cache_valid("regions"), "新鲜缓存应返回 true")

func test_is_cache_valid_invalid() -> void:
	var world := WorldManager
	assert_false(world._is_cache_valid("nonexistent"), "不存在的缓存键应返回 false")

func test_is_cache_valid_expired() -> void:
	var world := WorldManager
	world._cache_timestamps["regions"] = Time.get_unix_time_from_system() - 600
	assert_false(world._is_cache_valid("regions"), "过期缓存应返回 false")

func test_reset_clears_cache_timestamps() -> void:
	var world := WorldManager
	world._cache_timestamps["regions"] = 1000
	world.reset()
	assert_eq(world._cache_timestamps.size(), 0, "reset 应清除缓存时间戳")