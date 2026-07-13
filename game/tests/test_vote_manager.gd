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

func test_is_vote_landed_no_content_package() -> void:
	var vm := VoteManager
	vm.reset()
	var item: Dictionary = {"vote_cycle_id": "vc_001", "title": "周期A"}
	assert_false(vm.is_vote_landed(item), "无 content_package 字段时应返回 false")
	vm.reset()

func test_is_vote_landed_empty_content_package() -> void:
	var vm := VoteManager
	vm.reset()
	var item: Dictionary = {"vote_cycle_id": "vc_001", "content_package": {}}
	assert_false(vm.is_vote_landed(item), "content_package 为空字典时应返回 false")
	vm.reset()

func test_is_vote_landed_with_content_package() -> void:
	var vm := VoteManager
	vm.reset()
	var item: Dictionary = {
		"vote_cycle_id": "vc_001",
		"content_package": {"package_version": "pkg_ch02_waste_20260701_01"}
	}
	assert_true(vm.is_vote_landed(item), "content_package 非空时应返回 true")
	vm.reset()

func test_get_vote_history_with_landing_empty() -> void:
	var vm := VoteManager
	vm.reset()
	vm.vote_history = []
	var result: Array[Dictionary] = vm.get_vote_history_with_landing()
	assert_eq(result.size(), 0, "空历史时应返回空数组")
	vm.reset()

func test_get_vote_history_with_landing_mixed() -> void:
	var vm := VoteManager
	vm.reset()
	var landed_item: Dictionary = {
		"vote_cycle_id": "vc_001",
		"title": "已落地周期",
		"content_package": {"package_version": "pkg_001"}
	}
	var unlanded_item: Dictionary = {
		"vote_cycle_id": "vc_002",
		"title": "未落地周期"
	}
	vm.vote_history = [landed_item, unlanded_item]
	var result: Array[Dictionary] = vm.get_vote_history_with_landing()
	assert_eq(result.size(), 2, "返回数组长度应与历史一致")
	assert_true(result[0].get("is_landed", false), "已落地项应带 is_landed=true 标记")
	assert_false(result[1].get("is_landed", true), "未落地项应带 is_landed=false 标记")
	assert_eq(result[0].get("title", ""), "已落地周期", "原始字段应保留")
	assert_eq(result[1].get("title", ""), "未落地周期", "原始字段应保留")
	assert_eq(vm.vote_history[0].get("is_landed", null), null, "原始历史不应被修改")
	vm.reset()

func test_get_content_package_for_vote_by_vote_cycle_id() -> void:
	var vm := VoteManager
	vm.reset()
	var pkg: Dictionary = {"package_version": "pkg_001"}
	vm.vote_history = [{"vote_cycle_id": "vc_001", "content_package": pkg}]
	var result: Dictionary = vm.get_content_package_for_vote("vc_001")
	assert_eq(result, pkg, "通过 vote_cycle_id 命中时应返回对应 content_package")
	vm.reset()

func test_get_content_package_for_vote_by_cycle_id_alias() -> void:
	var vm := VoteManager
	vm.reset()
	var pkg: Dictionary = {"package_version": "pkg_002"}
	vm.vote_history = [{"cycle_id": "vc_002", "content_package": pkg}]
	var result: Dictionary = vm.get_content_package_for_vote("vc_002")
	assert_eq(result, pkg, "通过 cycle_id 别名命中时应返回对应 content_package")
	vm.reset()

func test_get_content_package_for_vote_not_found() -> void:
	var vm := VoteManager
	vm.reset()
	vm.vote_history = [{"vote_cycle_id": "vc_001", "content_package": {"package_version": "pkg_001"}}]
	var result: Dictionary = vm.get_content_package_for_vote("vc_not_exist")
	assert_eq(result, {}, "未命中时应返回空字典")
	vm.reset()

func test_get_landed_at_with_released_at() -> void:
	var vm := VoteManager
	vm.reset()
	var item: Dictionary = {
		"content_package": {"released_at": "2026-07-13T10:00:00Z"}
	}
	assert_eq(vm.get_landed_at(item), "2026-07-13T10:00:00Z", "有 released_at 时应返回该值")
	vm.reset()

func test_get_landed_at_without_content_package() -> void:
	var vm := VoteManager
	vm.reset()
	var item: Dictionary = {"vote_cycle_id": "vc_001"}
	assert_eq(vm.get_landed_at(item), "", "无 content_package 时应返回空字符串")
	vm.reset()

func test_get_affected_regions_with_dict_array() -> void:
	var vm := VoteManager
	vm.reset()
	var item: Dictionary = {
		"content_package": {
			"payload": {
				"regions": [
					{"name": "铁卫城周边", "region_type": "core"},
					{"region_id": "region_wasteland_01"}
				]
			}
		}
	}
	var result: Array[String] = vm.get_affected_regions(item)
	assert_eq(result.size(), 2, "应返回 2 个区域名称")
	assert_eq(result[0], "铁卫城周边", "第一个区域应取 name 字段")
	assert_eq(result[1], "region_wasteland_01", "无 name 时应取 region_id")
	vm.reset()

func test_get_affected_regions_with_string_array() -> void:
	var vm := VoteManager
	vm.reset()
	var item: Dictionary = {
		"content_package": {
			"payload": {
				"regions": ["region_alpha", "region_beta"]
			}
		}
	}
	var result: Array[String] = vm.get_affected_regions(item)
	assert_eq(result.size(), 2, "字符串数组应返回 2 个元素")
	assert_eq(result[0], "region_alpha", "第一个元素应原样返回")
	assert_eq(result[1], "region_beta", "第二个元素应原样返回")
	vm.reset()

func test_get_affected_regions_empty() -> void:
	var vm := VoteManager
	vm.reset()
	var item: Dictionary = {"content_package": {}}
	var result: Array[String] = vm.get_affected_regions(item)
	assert_eq(result.size(), 0, "无 payload 或 regions 时应返回空数组")
	vm.reset()

func test_discussions_initial_state() -> void:
	var vm := VoteManager
	assert_eq(vm.discussions, [], "初始 discussions 应为空数组")
	assert_eq(vm.current_discussion_id, "", "初始 current_discussion_id 应为空字符串")
	assert_eq(vm.replies, [], "初始 replies 应为空数组")

func test_reset_discussions() -> void:
	var vm := VoteManager
	vm.discussions = [{"discussion_id": "d1", "content": "test"}]
	vm.current_discussion_id = "d1"
	vm.replies = [{"reply_id": "r1", "content": "reply"}]
	vm.discussions_meta = {"total": 1}
	vm.replies_meta = {"total": 1}
	vm.reset_discussions()
	assert_eq(vm.discussions, [], "重置后 discussions 应为空数组")
	assert_eq(vm.current_discussion_id, "", "重置后 current_discussion_id 应为空")
	assert_eq(vm.replies, [], "重置后 replies 应为空数组")
	assert_eq(vm.discussions_meta, {}, "重置后 discussions_meta 应为空字典")
	assert_eq(vm.replies_meta, {}, "重置后 replies_meta 应为空字典")

func test_get_discussion_by_id_found() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var d1: Dictionary = {"discussion_id": "d_001", "content": "讨论1", "like_count": 5}
	var d2: Dictionary = {"discussion_id": "d_002", "content": "讨论2", "like_count": 10}
	vm.discussions = [d1, d2]
	var result: Dictionary = vm.get_discussion_by_id("d_001")
	assert_eq(result, d1, "应能通过ID找到讨论")
	vm.reset_discussions()

func test_get_discussion_by_id_not_found() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var d1: Dictionary = {"discussion_id": "d_001", "content": "讨论1"}
	vm.discussions = [d1]
	var result: Dictionary = vm.get_discussion_by_id("d_not_exist")
	assert_eq(result, {}, "找不到讨论时应返回空字典")
	vm.reset_discussions()

func test_update_discussion_like_count() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var d1: Dictionary = {"discussion_id": "d_001", "content": "讨论1", "like_count": 5}
	var d2: Dictionary = {"discussion_id": "d_002", "content": "讨论2", "like_count": 10}
	vm.discussions = [d1.duplicate(), d2.duplicate()]
	vm._update_discussion_like_count("d_001", 15)
	assert_eq(vm.discussions[0]["like_count"], 15, "讨论1的点赞数应更新为15")
	assert_eq(vm.discussions[1]["like_count"], 10, "讨论2的点赞数应保持10")
	vm.reset_discussions()

func test_increment_discussion_reply_count() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var d1: Dictionary = {"discussion_id": "d_001", "content": "讨论1", "reply_count": 3}
	vm.discussions = [d1.duplicate()]
	vm._increment_discussion_reply_count("d_001")
	assert_eq(vm.discussions[0]["reply_count"], 4, "回复数应增加1")
	vm.reset_discussions()

func test_update_reply_like_count() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var r1: Dictionary = {"reply_id": "r_001", "content": "回复1", "like_count": 2}
	var r2: Dictionary = {"reply_id": "r_002", "content": "回复2", "like_count": 5}
	vm.replies = [r1.duplicate(), r2.duplicate()]
	vm._update_reply_like_count("r_002", 8)
	assert_eq(vm.replies[0]["like_count"], 2, "回复1的点赞数应保持2")
	assert_eq(vm.replies[1]["like_count"], 8, "回复2的点赞数应更新为8")
	vm.reset_discussions()

func test_create_discussion_empty_content() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var result: bool = vm.create_discussion("vc_test", "")
	assert_false(result, "空内容应返回false")
	assert_eq(vm.last_error.get("code", ""), "DISCUSSION_CONTENT_EMPTY", "错误码应为 DISCUSSION_CONTENT_EMPTY")
	vm.reset_discussions()

func test_create_discussion_whitespace_content() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var result: bool = vm.create_discussion("vc_test", "   ")
	assert_false(result, "空白内容应返回false")
	assert_eq(vm.last_error.get("code", ""), "DISCUSSION_CONTENT_EMPTY", "错误码应为 DISCUSSION_CONTENT_EMPTY")
	vm.reset_discussions()

func test_create_discussion_too_long() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var long_content: String = ""
	for i in range(501):
		long_content += "a"
	var result: bool = vm.create_discussion("vc_test", long_content)
	assert_false(result, "内容超过500字应返回false")
	assert_eq(vm.last_error.get("code", ""), "DISCUSSION_CONTENT_TOO_LONG", "错误码应为 DISCUSSION_CONTENT_TOO_LONG")
	vm.reset_discussions()

func test_create_reply_empty_content() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var result: bool = vm.create_reply("d_test", "")
	assert_false(result, "空回复应返回false")
	assert_eq(vm.last_error.get("code", ""), "REPLY_CONTENT_EMPTY", "错误码应为 REPLY_CONTENT_EMPTY")
	vm.reset_discussions()

func test_create_reply_too_long() -> void:
	var vm := VoteManager
	vm.reset_discussions()
	var long_content: String = ""
	for i in range(501):
		long_content += "a"
	var result: bool = vm.create_reply("d_test", long_content)
	assert_false(result, "回复超过500字应返回false")
	assert_eq(vm.last_error.get("code", ""), "REPLY_CONTENT_TOO_LONG", "错误码应为 REPLY_CONTENT_TOO_LONG")
	vm.reset_discussions()

# --- 图表数据获取测试 ---

func test_chart_data_cache_initial_state() -> void:
	var vm := VoteManager
	vm.reset()
	assert_eq(vm._chart_data_cache, {}, "初始图表数据缓存应为空字典")
	vm.reset()

func test_clear_chart_data_cache() -> void:
	var vm := VoteManager
	vm.reset()
	vm._chart_data_cache = {"vc_001_pie": {"chart_type": "pie"}}
	vm.clear_chart_data_cache()
	assert_eq(vm._chart_data_cache, {}, "清空后缓存应为空字典")
	vm.reset()

func test_get_cached_chart_data_empty() -> void:
	var vm := VoteManager
	vm.reset()
	var result: Dictionary = vm.get_cached_chart_data("vc_001", "pie")
	assert_eq(result, {}, "未缓存的图表数据应返回空字典")
	vm.reset()

func test_get_cached_chart_data_with_data() -> void:
	var vm := VoteManager
	vm.reset()
	var chart_data: Dictionary = {
		"chart_type": "pie",
		"vote_cycle_id": "vc_001",
		"total_votes": 100,
		"items": []
	}
	vm._chart_data_cache = {"vc_001_pie": chart_data}
	var result: Dictionary = vm.get_cached_chart_data("vc_001", "pie")
	assert_eq(result["chart_type"], "pie", "应返回缓存的图表类型")
	assert_eq(result["vote_cycle_id"], "vc_001", "应缓存的投票周期ID")
	vm.reset()

func test_fetch_vote_result_chart_data_method_exists() -> void:
	var vm := VoteManager
	assert_true(vm.has_method("fetch_vote_result_chart_data"), "VoteManager应有fetch_vote_result_chart_data方法")
	vm.reset()

func test_get_cached_chart_data_default_chart_type() -> void:
	var vm := VoteManager
	vm.reset()
	var chart_data: Dictionary = {"chart_type": "pie", "vote_cycle_id": "vc_001"}
	vm._chart_data_cache = {"vc_001_pie": chart_data}
	var result: Dictionary = vm.get_cached_chart_data("vc_001")
	assert_eq(result["chart_type"], "pie", "默认图表类型应为pie")
	vm.reset()

# --- 投票复盘报告测试 ---

func test_vote_review_cache_initial_state() -> void:
	var vm := VoteManager
	vm.reset()
	assert_eq(vm._vote_review_cache, {}, "初始复盘报告缓存应为空字典")
	vm.reset()

func test_clear_vote_review_cache() -> void:
	var vm := VoteManager
	vm.reset()
	vm._vote_review_cache = {"vc_001": {"vote_cycle_id": "vc_001"}}
	vm.clear_vote_review_cache()
	assert_eq(vm._vote_review_cache, {}, "清空后复盘报告缓存应为空字典")
	vm.reset()

func test_get_vote_review_empty() -> void:
	var vm := VoteManager
	vm.reset()
	var result: Dictionary = vm.get_vote_review("vc_001")
	assert_eq(result, {}, "未缓存的复盘报告应返回空字典")
	vm.reset()

func test_get_vote_review_with_data() -> void:
	var vm := VoteManager
	vm.reset()
	var review_data: Dictionary = {
		"vote_cycle_id": "vc_001",
		"total_votes": 100,
		"winning_candidate": {"title": "方向A"}
	}
	vm._vote_review_cache = {"vc_001": review_data}
	var result: Dictionary = vm.get_vote_review("vc_001")
	assert_eq(result["vote_cycle_id"], "vc_001", "应返回缓存的复盘报告")
	assert_eq(result["total_votes"], 100, "总票数应匹配")
	assert_eq(result["winning_candidate"]["title"], "方向A", "获胜候选标题应匹配")
	vm.reset()

func test_fetch_vote_review_method_exists() -> void:
	var vm := VoteManager
	assert_true(vm.has_method("fetch_vote_review"), "VoteManager 应有 fetch_vote_review 方法")
	assert_true(vm.has_method("get_vote_review"), "VoteManager 应有 get_vote_review 方法")
	assert_true(vm.has_method("clear_vote_review_cache"), "VoteManager 应有 clear_vote_review_cache 方法")
	vm.reset()

func test_fetch_vote_review_empty_cycle_id() -> void:
	var vm := VoteManager
	vm.reset()
	vm.fetch_vote_review("")
	assert_eq(vm.last_error.get("code", ""), "INVALID_VOTE_CYCLE_ID", "空周期ID应返回 INVALID_VOTE_CYCLE_ID")
	vm.reset()
