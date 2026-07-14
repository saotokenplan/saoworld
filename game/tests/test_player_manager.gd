extends "res://addons/gut/test.gd"

func before_each() -> void:
	PlayerManager.reset()

func test_player_manager_initial_state() -> void:
	var player := PlayerManager
	assert_eq(player.player_info.size(), 0, "初始玩家信息应为空")
	assert_eq(player.player_quests.size(), 0, "初始任务列表应为空")
	assert_eq(player.player_regions.size(), 0, "初始区域列表应为空")
	assert_false(player.is_loading, "初始状态不应为加载中")

func test_quest_status_constants() -> void:
	var player := PlayerManager
	assert_true(player.QUEST_STATUS.has("available"))
	assert_true(player.QUEST_STATUS.has("active"))
	assert_true(player.QUEST_STATUS.has("completed"))
	assert_true(player.QUEST_STATUS.has("failed"))

func test_quest_status_info() -> void:
	var player := PlayerManager
	var info: Dictionary = player.get_quest_status_info("active")
	assert_eq(info["name"], "进行中", "进行中状态名称正确")
	assert_eq(info["color"], "#FF9800", "进行中状态颜色正确")

func test_get_player_quest_by_id() -> void:
	var player := PlayerManager
	player.player_quests = [
		{"quest_id": "quest_001", "name": "Test Quest"},
		{"quest_id": "quest_002", "name": "Another Quest"}
	]
	player._update_quest_index()
	var quest: Dictionary = player.get_player_quest_by_id("quest_001")
	assert_eq(quest["quest_id"], "quest_001", "应正确获取任务")

func test_get_player_quest_by_id_not_found() -> void:
	var player := PlayerManager
	player.player_quests = [{"quest_id": "quest_001"}]
	player._update_quest_index()
	var quest: Dictionary = player.get_player_quest_by_id("quest_999")
	assert_eq(quest.size(), 0, "不存在的任务应返回空字典")

func test_get_player_quests_by_status() -> void:
	var player := PlayerManager
	player.player_quests = [
		{"quest_id": "quest_001", "status": "active"},
		{"quest_id": "quest_002", "status": "active"},
		{"quest_id": "quest_003", "status": "completed"}
	]
	var active: Array[Dictionary] = player.get_player_quests_by_status("active")
	assert_eq(active.size(), 2, "应返回 2 个进行中任务")

func test_get_active_quests() -> void:
	var player := PlayerManager
	player.player_quests = [
		{"quest_id": "quest_001", "status": "active"},
		{"quest_id": "quest_002", "status": "available"}
	]
	var active: Array[Dictionary] = player.get_active_quests()
	assert_eq(active.size(), 1, "应返回 1 个进行中任务")

func test_get_available_quests() -> void:
	var player := PlayerManager
	player.player_quests = [
		{"quest_id": "quest_001", "status": "available"},
		{"quest_id": "quest_002", "status": "active"}
	]
	var available: Array[Dictionary] = player.get_available_quests()
	assert_eq(available.size(), 1, "应返回 1 个可接取任务")

func test_get_completed_quests() -> void:
	var player := PlayerManager
	player.player_quests = [
		{"quest_id": "quest_001", "status": "completed"},
		{"quest_id": "quest_002", "status": "active"}
	]
	var completed: Array[Dictionary] = player.get_completed_quests()
	assert_eq(completed.size(), 1, "应返回 1 个已完成任务")

func test_is_quest_active() -> void:
	var player := PlayerManager
	player.player_quests = [{"quest_id": "quest_001", "status": "active"}]
	player._update_quest_index()
	assert_true(player.is_quest_active("quest_001"), "进行中任务应返回 true")
	assert_false(player.is_quest_active("quest_999"), "不存在的任务应返回 false")

func test_is_quest_completed() -> void:
	var player := PlayerManager
	player.player_quests = [{"quest_id": "quest_001", "status": "completed"}]
	player._update_quest_index()
	assert_true(player.is_quest_completed("quest_001"), "已完成任务应返回 true")
	assert_false(player.is_quest_completed("quest_999"), "不存在的任务应返回 false")

func test_is_region_unlocked() -> void:
	var player := PlayerManager
	player.player_regions = [{"region_id": "region_001", "unlocked": true}]
	player._update_region_index()
	assert_true(player.is_region_unlocked("region_001"), "已解锁区域应返回 true")
	assert_false(player.is_region_unlocked("region_999"), "不存在的区域应返回 false")

func test_get_unlocked_regions() -> void:
	var player := PlayerManager
	player.player_regions = [
		{"region_id": "region_001", "unlocked": true},
		{"region_id": "region_002", "unlocked": false},
		{"region_id": "region_003", "unlocked": true}
	]
	var unlocked: Array[Dictionary] = player.get_unlocked_regions()
	assert_eq(unlocked.size(), 2, "应返回 2 个已解锁区域")

func test_get_player_info_methods() -> void:
	var player := PlayerManager
	player.player_info = {
		"player_id": "player_001",
		"player_name": "TestPlayer",
		"level": 10,
		"reputation": 1000
	}
	assert_eq(player.get_player_id(), "player_001")
	assert_eq(player.get_player_name(), "TestPlayer")
	assert_eq(player.get_player_level(), 10)
	assert_eq(player.get_player_reputation(), 1000)

func test_reset() -> void:
	var player := PlayerManager
	player.player_info = {"player_id": "player_001"}
	player.player_quests = [{"quest_id": "quest_001"}]
	player.player_regions = [{"region_id": "region_001"}]
	player._update_quest_index()
	player._update_region_index()
	player.is_loading = true
	player.last_error = {"code": "TEST_ERROR"}
	player.reset()
	assert_eq(player.player_info.size(), 0)
	assert_eq(player.player_quests.size(), 0)
	assert_eq(player.player_regions.size(), 0)
	assert_false(player.is_loading)
	assert_eq(player.last_error.size(), 0)

# ===== 索引优化测试（S8-01 第四阶段）=====

func test_quest_index_initial_empty() -> void:
	var player := PlayerManager
	player.reset()
	assert_eq(player.quest_index.size(), 0, "quest_index 初始应为空")

func test_update_quest_index_builds_index() -> void:
	var player := PlayerManager
	player.player_quests = [
		{"quest_id": "quest_a", "status": "active"},
		{"quest_id": "quest_b", "status": "completed"},
		{"quest_id": "quest_c", "status": "available"}
	]
	player._update_quest_index()
	assert_eq(player.quest_index.size(), 3, "索引应包含 3 个任务")
	assert_true(player.quest_index.has("quest_a"), "索引应包含 quest_a")
	assert_true(player.quest_index.has("quest_b"), "索引应包含 quest_b")
	assert_true(player.quest_index.has("quest_c"), "索引应包含 quest_c")

func test_update_quest_index_skips_empty_id() -> void:
	var player := PlayerManager
	player.player_quests = [
		{"quest_id": "quest_a", "status": "active"},
		{"quest_id": "", "status": "completed"},
		{"name": "no_id_quest"}
	]
	player._update_quest_index()
	assert_eq(player.quest_index.size(), 1, "空 ID 任务不应进入索引")
	assert_true(player.quest_index.has("quest_a"), "索引应仅包含 quest_a")

func test_update_quest_index_clears_before_rebuild() -> void:
	var player := PlayerManager
	player.player_quests = [
		{"quest_id": "quest_old", "status": "active"},
		{"quest_id": "quest_a", "status": "active"}
	]
	player._update_quest_index()
	assert_eq(player.quest_index.size(), 2, "初始索引 2 个任务")
	# 重新设置任务列表（不含 quest_old），索引应被重建而非追加
	player.player_quests = [{"quest_id": "quest_new", "status": "active"}]
	player._update_quest_index()
	assert_eq(player.quest_index.size(), 1, "重建后索引应仅 1 个任务")
	assert_false(player.quest_index.has("quest_old"), "旧任务不应残留在索引中")
	assert_true(player.quest_index.has("quest_new"), "新任务应在索引中")

func test_get_player_quest_by_id_uses_index() -> void:
	var player := PlayerManager
	player.player_quests = [
		{"quest_id": "quest_001", "name": "Indexed Quest", "status": "active"}
	]
	player._update_quest_index()
	# 通过索引查询应返回完整任务数据
	var quest: Dictionary = player.get_player_quest_by_id("quest_001")
	assert_eq(quest.get("name", ""), "Indexed Quest", "应通过索引返回完整任务数据")
	assert_eq(quest.get("status", ""), "active", "应通过索引返回任务状态")

func test_region_index_initial_empty() -> void:
	var player := PlayerManager
	player.reset()
	assert_eq(player.region_index.size(), 0, "region_index 初始应为空")

func test_update_region_index_builds_index() -> void:
	var player := PlayerManager
	player.player_regions = [
		{"region_id": "region_a", "unlocked": true},
		{"region_id": "region_b", "unlocked": false}
	]
	player._update_region_index()
	assert_eq(player.region_index.size(), 2, "索引应包含 2 个区域")
	assert_true(player.region_index.has("region_a"), "索引应包含 region_a")
	assert_true(player.region_index.has("region_b"), "索引应包含 region_b")

func test_update_region_index_skips_empty_id() -> void:
	var player := PlayerManager
	player.player_regions = [
		{"region_id": "region_a", "unlocked": true},
		{"region_id": "", "unlocked": false}
	]
	player._update_region_index()
	assert_eq(player.region_index.size(), 1, "空 ID 区域不应进入索引")
	assert_true(player.region_index.has("region_a"), "索引应仅包含 region_a")

func test_get_player_region_by_id_uses_index() -> void:
	var player := PlayerManager
	player.player_regions = [
		{"region_id": "region_001", "unlocked": true, "reputation": 500}
	]
	player._update_region_index()
	var region: Dictionary = player.get_player_region_by_id("region_001")
	assert_eq(region.get("reputation", 0), 500, "应通过索引返回完整区域数据")

func test_get_player_region_by_id_not_found() -> void:
	var player := PlayerManager
	player.player_regions = [{"region_id": "region_001", "unlocked": true}]
	player._update_region_index()
	var region: Dictionary = player.get_player_region_by_id("region_999")
	assert_eq(region.size(), 0, "不存在的区域应返回空字典")

func test_reset_clears_indexes() -> void:
	var player := PlayerManager
	player.player_quests = [{"quest_id": "quest_001", "status": "active"}]
	player.player_regions = [{"region_id": "region_001", "unlocked": true}]
	player._update_quest_index()
	player._update_region_index()
	assert_eq(player.quest_index.size(), 1, "重置前任务索引应有数据")
	assert_eq(player.region_index.size(), 1, "重置前区域索引应有数据")
	player.reset()
	assert_eq(player.quest_index.size(), 0, "reset 后 quest_index 应清空")
	assert_eq(player.region_index.size(), 0, "reset 后 region_index 应清空")

# ===== 预排序声望级别测试（S8-01 第四阶段）=====

func test_sorted_reputation_levels_populated() -> void:
	var player := PlayerManager
	# _ready 在 Autoload 初始化时已调用 _prepare_reputation_levels
	assert_eq(player.sorted_reputation_levels.size(), 6, "应有 6 个声望级别")

func test_sorted_reputation_levels_descending_threshold() -> void:
	var player := PlayerManager
	# 预排序应按 threshold 降序（exalted 42000 > revered 21000 > ...）
	var thresholds: Array = []
	for level_info in player.sorted_reputation_levels:
		thresholds.append(level_info["threshold"])
	# 验证降序
	for i in range(thresholds.size() - 1):
		assert_true(thresholds[i] >= thresholds[i + 1], "声望阈值应降序排列")

func test_sorted_reputation_levels_has_level_name() -> void:
	var player := PlayerManager
	for level_info in player.sorted_reputation_levels:
		assert_true(level_info.has("level_name"), "每个级别应包含 level_name 字段")
		assert_true(level_info.has("threshold"), "每个级别应包含 threshold 字段")

func test_calculate_reputation_level_exalted() -> void:
	var player := PlayerManager
	assert_eq(player.calculate_reputation_level(42000), "exalted", "42000 应为崇拜")
	assert_eq(player.calculate_reputation_level(50000), "exalted", "50000 应为崇拜")

func test_calculate_reputation_level_revered() -> void:
	var player := PlayerManager
	assert_eq(player.calculate_reputation_level(21000), "revered", "21000 应为崇敬")
	assert_eq(player.calculate_reputation_level(41999), "revered", "41999 应为崇敬")

func test_calculate_reputation_level_honored() -> void:
	var player := PlayerManager
	assert_eq(player.calculate_reputation_level(9000), "honored", "9000 应为尊敬")
	assert_eq(player.calculate_reputation_level(20999), "honored", "20999 应为尊敬")

func test_calculate_reputation_level_friendly() -> void:
	var player := PlayerManager
	assert_eq(player.calculate_reputation_level(3000), "friendly", "3000 应为友好")
	assert_eq(player.calculate_reputation_level(8999), "friendly", "8999 应为友好")

func test_calculate_reputation_level_neutral() -> void:
	var player := PlayerManager
	assert_eq(player.calculate_reputation_level(0), "neutral", "0 应为中立")
	assert_eq(player.calculate_reputation_level(2999), "neutral", "2999 应为中立")

func test_calculate_reputation_level_hostile() -> void:
	var player := PlayerManager
	assert_eq(player.calculate_reputation_level(-1), "hostile", "-1 应为敌对")
	assert_eq(player.calculate_reputation_level(-3000), "hostile", "-3000 应为敌对")
	assert_eq(player.calculate_reputation_level(-9999), "hostile", "-9999 应为敌对")

func test_sort_reputation_by_threshold() -> void:
	var player := PlayerManager
	var a: Dictionary = {"threshold": 9000, "level_name": "honored"}
	var b: Dictionary = {"threshold": 3000, "level_name": "friendly"}
	# a.threshold > b.threshold 应返回 true（降序）
	assert_true(player._sort_reputation_by_threshold(a, b), "高阈值应排在前")
	assert_false(player._sort_reputation_by_threshold(b, a), "低阈值应排在后")

# ===== 并行请求测试（S8-01 第四阶段）=====

func test_refresh_all_initializes_pending_requests() -> void:
	var player := PlayerManager
	player.reset()
	assert_eq(player.pending_requests, 0, "初始 pending_requests 应为 0")
	assert_false(player.refresh_all_completed, "初始 refresh_all_completed 应为 false")

func test_refresh_all_sets_pending_to_four() -> void:
	var player := PlayerManager
	# refresh_all 会调用 4 个 async 方法，每个会立即递减 pending_requests
	# 由于 async 方法同步执行 APIManager.get（测试环境无真实网络），
	# 调用后 pending_requests 会经历 4->3->2->1->0 的过程
	player.refresh_all()
	# 调用完成后，4 个 async 方法都已执行并递减，pending_requests 应回到 0
	assert_eq(player.pending_requests, 0, "4 个并行请求完成后 pending_requests 应为 0")
	assert_true(player.refresh_all_completed, "4 个并行请求完成后 refresh_all_completed 应为 true")

func test_decrement_pending_requests() -> void:
	var player := PlayerManager
	player.reset()
	player.pending_requests = 2
	player._decrement_pending_requests()
	assert_eq(player.pending_requests, 1, "递减后应为 1")
	assert_false(player.refresh_all_completed, "还有 1 个未完成，不应标记完成")
	player._decrement_pending_requests()
	assert_eq(player.pending_requests, 0, "再次递减后应为 0")
	assert_true(player.refresh_all_completed, "全部完成后应标记 refresh_all_completed")

func test_decrement_pending_requests_sets_loading_false() -> void:
	var player := PlayerManager
	player.reset()
	player.is_loading = true
	player.pending_requests = 1
	player._decrement_pending_requests()
	assert_false(player.is_loading, "pending_requests 归零后应关闭 loading 状态")

func test_reset_clears_pending_requests() -> void:
	var player := PlayerManager
	player.pending_requests = 3
	player.refresh_all_completed = true
	player.reset()
	assert_eq(player.pending_requests, 0, "reset 后 pending_requests 应为 0")
	assert_false(player.refresh_all_completed, "reset 后 refresh_all_completed 应为 false")
