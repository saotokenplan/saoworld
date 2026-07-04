extends "res://addons/gut/test.gd"
## VoteManager 单元测试

func test_initial_state() -> void:
	var vm := VoteManager
	assert_eq(vm.current_cycle, {}, "初始 current_cycle 应为空字典")
	assert_eq(vm.candidates, [], "初始 candidates 应为空数组")
	assert_false(vm.has_voted, "初始 has_voted 应为 false")
	assert_false(vm.is_loading, "初始 is_loading 应为 false")
	assert_eq(vm.schema_version, 1, "初始 schema_version 应为 1")

func test_reset() -> void:
	var vm := VoteManager
	vm.current_cycle = {"vote_cycle_id": "vc_test", "status": "open"}
	vm.candidates = [{"candidate_id": "c1", "vote_count": 10}]
	vm.vote_history = [{"vote_cycle_id": "vc_old"}]
	vm.has_voted = true
	vm.is_loading = true
	vm.last_error = {"code": "TEST_ERROR", "message": "test"}
	vm.reset()
	assert_eq(vm.current_cycle, {}, "重置后 current_cycle 应为空字典")
	assert_eq(vm.candidates, [], "重置后 candidates 应为空数组")
	assert_eq(vm.vote_history, [], "重置后 vote_history 应为空数组")
	assert_false(vm.has_voted, "重置后 has_voted 应为 false")
	assert_false(vm.is_loading, "重置后 is_loading 应为 false")
	assert_eq(vm.last_error, {}, "重置后 last_error 应为空字典")

func test_get_candidate_count_empty() -> void:
	var vm := VoteManager
	vm.reset()
	assert_eq(vm.get_candidate_count(), 0, "空候选项时 get_candidate_count 应返回 0")
	vm.reset()

func test_get_candidate_by_id_not_found() -> void:
	var vm := VoteManager
	vm.reset()
	assert_eq(vm.get_candidate_by_id("test"), {}, "找不到候选项时应返回空字典")
	vm.reset()

func test_is_cycle_open_no_cycle() -> void:
	var vm := VoteManager
	vm.reset()
	assert_false(vm.is_cycle_open(), "无周期时 is_cycle_open 应返回 false")
	vm.reset()

func test_candidates_with_data() -> void:
	var vm := VoteManager
	vm.reset()
	var c1: Dictionary = {"candidate_id": "cand_001", "title": "方向A", "vote_count": 30}
	var c2: Dictionary = {"candidate_id": "cand_002", "title": "方向B", "vote_count": 20}
	var c3: Dictionary = {"candidate_id": "cand_003", "title": "方向C", "vote_count": 50}
	vm.candidates = [c1, c2, c3]
	assert_eq(vm.get_candidate_count(), 3, "候选项数量应为 3")
	assert_eq(vm.get_candidate_by_id("cand_002"), c2, "应能通过ID找到候选项")
	assert_eq(vm.get_total_votes(), 100, "总票数应为 100")
	assert_eq(vm.get_candidate_percentage("cand_001"), 30.0, "方向A占比应为 30%")
	assert_eq(vm.get_candidate_percentage("cand_003"), 50.0, "方向C占比应为 50%")
	vm.reset()

func test_is_cycle_open_with_data() -> void:
	var vm := VoteManager
	vm.reset()
	vm.current_cycle = {"vote_cycle_id": "vc_open", "status": "open"}
	assert_true(vm.is_cycle_open(), "状态为 open 时 is_cycle_open 应返回 true")
	vm.current_cycle = {"vote_cycle_id": "vc_closed", "status": "closed"}
	assert_false(vm.is_cycle_open(), "状态为 closed 时 is_cycle_open 应返回 false")
	vm.reset()
