extends "res://addons/gut/test.gd"

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
	var quest: Dictionary = player.get_player_quest_by_id("quest_001")
	assert_eq(quest["quest_id"], "quest_001", "应正确获取任务")

func test_get_player_quest_by_id_not_found() -> void:
	var player := PlayerManager
	player.player_quests = [{"quest_id": "quest_001"}]
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
	assert_true(player.is_quest_active("quest_001"), "进行中任务应返回 true")
	assert_false(player.is_quest_active("quest_999"), "不存在的任务应返回 false")

func test_is_quest_completed() -> void:
	var player := PlayerManager
	player.player_quests = [{"quest_id": "quest_001", "status": "completed"}]
	assert_true(player.is_quest_completed("quest_001"), "已完成任务应返回 true")
	assert_false(player.is_quest_completed("quest_999"), "不存在的任务应返回 false")

func test_is_region_unlocked() -> void:
	var player := PlayerManager
	player.player_regions = [{"region_id": "region_001", "unlocked": true}]
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
	player.is_loading = true
	player.last_error = {"code": "TEST_ERROR"}
	player.reset()
	assert_eq(player.player_info.size(), 0)
	assert_eq(player.player_quests.size(), 0)
	assert_eq(player.player_regions.size(), 0)
	assert_false(player.is_loading)
	assert_eq(player.last_error.size(), 0)