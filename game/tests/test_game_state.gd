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

func test_initial_level_and_exp() -> void:
	var state := GameState
	assert_eq(state.player_level, 1, "初始等级应为 1")
	assert_eq(state.player_exp, 0, "初始经验值应为 0")

func test_add_exp() -> void:
	var state := GameState
	state.add_exp(100)
	assert_eq(state.player_exp, 100, "增加 100 经验后应为 100")
	state.add_exp(50)
	assert_eq(state.player_exp, 150, "再增加 50 经验后应为 150")
	state.reset_state()

func test_vote_participation_initial() -> void:
	var state := GameState
	assert_eq(state.vote_participation.size(), 0, "初始投票参与记录应为空数组")
	assert_eq(state.last_vote_cycle_id, "", "初始 last_vote_cycle_id 应为空字符串")
	assert_false(state.has_voted_in_cycle("any"), "初始状态下 has_voted_in_cycle 应返回 false")

func test_record_vote_participation() -> void:
	var state := GameState
	state.record_vote_participation("cycle_001")
	assert_true(state.has_voted_in_cycle("cycle_001"), "记录后 cycle_001 应返回 true")
	assert_false(state.has_voted_in_cycle("cycle_002"), "未记录的 cycle_002 应返回 false")
	assert_eq(state.last_vote_cycle_id, "cycle_001", "last_vote_cycle_id 应为 cycle_001")
	state.reset_state()

func test_duplicate_vote_participation() -> void:
	var state := GameState
	state.record_vote_participation("cycle_001")
	state.record_vote_participation("cycle_001")
	assert_eq(state.vote_participation.size(), 1, "重复记录后 vote_participation 中应只有一个 cycle_001")
	state.reset_state()

func test_reset_state_includes_new_fields() -> void:
	var state := GameState
	state.player_level = 5
	state.player_exp = 1000
	state.record_vote_participation("cycle_001")
	state.reset_state()
	assert_eq(state.player_level, 1, "重置后 player_level 应为 1")
	assert_eq(state.player_exp, 0, "重置后 player_exp 应为 0")
	assert_eq(state.vote_participation.size(), 0, "重置后 vote_participation 应为空")
	assert_eq(state.last_vote_cycle_id, "", "重置后 last_vote_cycle_id 应为空")
