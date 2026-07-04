extends "res://addons/gut/test.gd"
## GameState 单元测试

func test_initial_state() -> void:
	var state := GameState
	assert_eq(state.get_chapter(), "chapter_01", "默认章节应为 chapter_01")
	assert_false(state.is_logged_in(), "初始状态应为未登录")
	assert_eq(state.get_player_id(), "", "初始玩家ID应为空")

func test_set_player_info() -> void:
	var state := GameState
	state.set_player_info("player_test_001", "测试玩家")
	assert_true(state.is_logged_in(), "设置玩家信息后应为已登录状态")
	assert_eq(state.get_player_id(), "player_test_001", "玩家ID应匹配")
	assert_eq(state.player_name, "测试玩家", "玩家名称应匹配")
	state.reset_state()

func test_unlock_region() -> void:
	var state := GameState
	assert_false(state.is_region_unlocked("region_test_01"), "初始区域应未解锁")
	state.unlock_region("region_test_01")
	assert_true(state.is_region_unlocked("region_test_01"), "解锁后区域应为已解锁状态")
	state.reset_state()

func test_set_chapter() -> void:
	var state := GameState
	state.set_chapter("chapter_02")
	assert_eq(state.get_chapter(), "chapter_02", "章节应已切换")
	state.set_chapter("chapter_01")

func test_reset_state() -> void:
	var state := GameState
	state.set_player_info("player_test_002", "重置测试")
	state.unlock_region("region_test_02")
	state.set_chapter("chapter_03")
	state.reset_state()
	assert_false(state.is_logged_in(), "重置后应为未登录状态")
	assert_eq(state.get_player_id(), "", "重置后玩家ID应为空")
	assert_eq(state.get_chapter(), "chapter_01", "重置后章节应恢复默认")
	assert_false(state.is_region_unlocked("region_test_02"), "重置后区域应恢复未解锁")
