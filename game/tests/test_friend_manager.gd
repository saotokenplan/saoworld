extends "res://addons/gut/test.gd"
## FriendManager 单元测试

func test_initial_state() -> void:
	var fm := FriendManager
	fm.reset()
	assert_eq(fm._friends, [], "初始 _friends 应为空数组")
	assert_eq(fm._pending_requests, [], "初始 _pending_requests 应为空数组")
	assert_eq(fm._friend_statuses, {}, "初始 _friend_statuses 应为空字典")
	assert_false(fm._is_loading, "初始 _is_loading 应为 false")
	fm.reset()

func test_signal_declarations() -> void:
	var fm := FriendManager
	assert_true(fm.has_signal("friends_loaded"), "应声明 friends_loaded 信号")
	assert_true(fm.has_signal("friend_request_sent"), "应声明 friend_request_sent 信号")
	assert_true(fm.has_signal("friend_request_accepted"), "应声明 friend_request_accepted 信号")
	assert_true(fm.has_signal("friend_request_rejected"), "应声明 friend_request_rejected 信号")
	assert_true(fm.has_signal("friend_deleted"), "应声明 friend_deleted 信号")
	assert_true(fm.has_signal("friend_status_loaded"), "应声明 friend_status_loaded 信号")
	assert_true(fm.has_signal("error_occurred"), "应声明 error_occurred 信号")

func test_is_friend_returns_false_for_unknown() -> void:
	var fm := FriendManager
	fm.reset()
	assert_false(fm.is_friend("unknown_player_id"), "未知好友ID应返回 false")
	fm.reset()

func test_get_friend_count_returns_zero_initially() -> void:
	var fm := FriendManager
	fm.reset()
	assert_eq(fm.get_friend_count(), 0, "初始好友数量应为 0")
	fm.reset()

func test_clear_friends_cache() -> void:
	var fm := FriendManager
	fm.reset()
	fm._friends = [{"player_id": "p1", "display_name": "好友1"}]
	assert_eq(fm._friends.size(), 1, "设置后好友列表应有1个元素")
	fm.clear_friends_cache()
	assert_eq(fm._friends, [], "清空缓存后 _friends 应为空数组")
	fm.reset()

func test_clear_pending_cache() -> void:
	var fm := FriendManager
	fm.reset()
	fm._pending_requests = [{"player_id": "p2", "display_name": "请求者"}]
	assert_eq(fm._pending_requests.size(), 1, "设置后待处理列表应有1个元素")
	fm.clear_pending_cache()
	assert_eq(fm._pending_requests, [], "清空缓存后 _pending_requests 应为空数组")
	fm.reset()

func test_is_friend_with_data() -> void:
	var fm := FriendManager
	fm.reset()
	fm._friends = [
		{"player_id": "p_001", "display_name": "好友A"},
		{"player_id": "p_002", "display_name": "好友B"}
	]
	assert_true(fm.is_friend("p_001"), "已存在的好友ID应返回 true")
	assert_true(fm.is_friend("p_002"), "已存在的好友ID应返回 true")
	assert_false(fm.is_friend("p_999"), "不存在的好友ID应返回 false")
	fm.reset()

func test_get_friend_count_with_data() -> void:
	var fm := FriendManager
	fm.reset()
	fm._friends = [
		{"player_id": "p_001", "display_name": "好友A"},
		{"player_id": "p_002", "display_name": "好友B"},
		{"player_id": "p_003", "display_name": "好友C"}
	]
	assert_eq(fm.get_friend_count(), 3, "好友数量应为 3")
	fm.reset()

func test_get_friend_status_default() -> void:
	var fm := FriendManager
	fm.reset()
	var status: String = fm.get_friend_status("unknown_id")
	assert_eq(status, "offline", "未知好友状态应默认为 offline")
	fm.reset()

func test_get_friend_status_with_data() -> void:
	var fm := FriendManager
	fm.reset()
	fm._friend_statuses = {"p_001": "online", "p_002": "away"}
	assert_eq(fm.get_friend_status("p_001"), "online", "已记录的在线状态应返回 online")
	assert_eq(fm.get_friend_status("p_002"), "away", "已记录的离开状态应返回 away")
	fm.reset()

func test_reset() -> void:
	var fm := FriendManager
	fm.reset()
	fm._friends = [{"player_id": "p1"}]
	fm._pending_requests = [{"player_id": "p2"}]
	fm._friend_statuses = {"p1": "online"}
	fm._is_loading = true
	fm.reset()
	assert_eq(fm._friends, [], "重置后 _friends 应为空数组")
	assert_eq(fm._pending_requests, [], "重置后 _pending_requests 应为空数组")
	assert_eq(fm._friend_statuses, {}, "重置后 _friend_statuses 应为空字典")
	assert_false(fm._is_loading, "重置后 _is_loading 应为 false")

func test_remove_friend() -> void:
	var fm := FriendManager
	fm.reset()
	fm._friends = [
		{"player_id": "p_001", "display_name": "好友A"},
		{"player_id": "p_002", "display_name": "好友B"}
	]
	fm._remove_friend("p_001")
	assert_eq(fm._friends.size(), 1, "移除后好友列表应为1个元素")
	assert_eq(fm._friends[0].get("player_id", ""), "p_002", "剩余好友应为 p_002")
	fm.reset()

func test_remove_pending_request() -> void:
	var fm := FriendManager
	fm.reset()
	fm._pending_requests = [
		{"player_id": "p_001", "display_name": "请求者A"},
		{"player_id": "p_002", "display_name": "请求者B"}
	]
	fm._remove_pending_request("p_001")
	assert_eq(fm._pending_requests.size(), 1, "移除后待处理列表应为1个元素")
	assert_eq(fm._pending_requests[0].get("player_id", ""), "p_002", "剩余请求应为 p_002")
	fm.reset()

func test_send_friend_request_empty_id() -> void:
	var fm := FriendManager
	fm.reset()
	fm.send_friend_request("")
	assert_true(fm._is_loading == false, "空ID不应触发加载")
	fm.reset()

func test_delete_friend_empty_id() -> void:
	var fm := FriendManager
	fm.reset()
	fm.delete_friend("")
	assert_true(fm._is_loading == false, "空ID不应触发加载")
	fm.reset()
