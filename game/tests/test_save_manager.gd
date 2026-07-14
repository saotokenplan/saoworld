extends GutTest
## SaveManager 存档系统测试
## 注意：S8-01 第三阶段后 save_game/load_game 改为异步（Thread），
## 测试需在保存/加载后等待线程完成再验证结果。

var test_save_path: String = "user://test_saves/"

func before_all() -> void:
	# 创建测试存档目录
	var dir := DirAccess.open("user://")
	if dir and not dir.dir_exists("test_saves"):
		dir.make_dir("test_saves")

func after_all() -> void:
	# 清理测试存档
	var dir := DirAccess.open("user://test_saves/")
	if dir:
		var files: PackedStringArray = dir.get_files()
		for file in files:
			dir.remove(file)

func before_each() -> void:
	# 重置游戏状态与缓存
	GameState.reset_state()
	PlayerManager.reset()
	SaveManager.reset_cache()

func test_save_and_load_cycle() -> void:
	# 设置初始游戏状态
	GameState.player_id = "test_player_001"
	GameState.player_name = "测试玩家"
	GameState.player_level = 5
	GameState.player_exp = 1200
	GameState.chapter_id = "chapter_02"
	GameState.player_health = 80
	GameState.player_max_health = 120
	GameState.player_attack = 15
	GameState.player_defense = 8
	GameState.unlocked_regions = ["region_01", "region_02"]

	# 添加任务进度
	PlayerManager.player_quests = [
		{"quest_id": "quest_001", "status": "active", "progress": 50},
		{"quest_id": "quest_002", "status": "completed", "progress": 100}
	]
	PlayerManager._update_quest_index()

	# 保存游戏（异步启动）
	var save_result: Dictionary = SaveManager.save_game("test_slot")
	assert_true(save_result.get("success", false), "保存应该成功启动")
	# 等待异步保存完成
	await _wait_for_save_complete()

	# 验证存档文件存在
	assert_true(SaveManager.has_save_file("test_slot"), "存档文件应该存在")

	# 重置游戏状态
	GameState.reset_state()
	PlayerManager.reset()

	# 加载游戏（异步启动）
	var load_result: Dictionary = SaveManager.load_game("test_slot")
	assert_true(load_result.get("success", false), "加载应该成功启动")
	# 等待异步加载完成
	await _wait_for_load_complete()

	# 验证游戏状态恢复
	assert_eq(GameState.player_id, "test_player_001", "玩家ID应该恢复")
	assert_eq(GameState.player_name, "测试玩家", "玩家名称应该恢复")
	assert_eq(GameState.player_level, 5, "玩家等级应该恢复")
	assert_eq(GameState.player_exp, 1200, "经验值应该恢复")
	assert_eq(GameState.chapter_id, "chapter_02", "章节ID应该恢复")
	assert_eq(GameState.player_health, 80, "血量应该恢复")
	assert_eq(GameState.player_max_health, 120, "最大血量应该恢复")
	assert_eq(GameState.player_attack, 15, "攻击力应该恢复")
	assert_eq(GameState.player_defense, 8, "防御力应该恢复")
	assert_eq(GameState.unlocked_regions.size(), 2, "解锁区域数量应该正确")

	# 验证任务进度恢复
	assert_eq(PlayerManager.player_quests.size(), 2, "任务数量应该正确")

func test_save_data_schema() -> void:
	# 保存游戏
	var save_result: Dictionary = SaveManager.save_game("test_schema")
	assert_true(save_result.get("success", false), "保存应该成功启动")
	await _wait_for_save_complete()

	# 读取存档文件
	var save_path: String = "user://saves/save_test_schema.json"
	var file := FileAccess.open(save_path, FileAccess.READ)
	if not file:
		fail_test("无法打开存档文件")
		return

	var content: String = file.get_as_text()
	file.close()

	var parsed: Variant = JSON.parse_string(content)
	if typeof(parsed) != TYPE_DICTIONARY:
		fail_test("存档数据格式错误")
		return

	var save_data: Dictionary = parsed

	# 验证存档数据结构
	assert_true(save_data.has("schema_version"), "应该有schema_version字段")
	assert_true(save_data.has("save_id"), "应该有save_id字段")
	assert_true(save_data.has("created_at"), "应该有created_at字段")
	assert_true(save_data.has("updated_at"), "应该有updated_at字段")
	assert_true(save_data.has("player_profile"), "应该有player_profile字段")
	assert_true(save_data.has("player_position"), "应该有player_position字段")
	assert_true(save_data.has("player_attributes"), "应该有player_attributes字段")
	assert_true(save_data.has("player_progress"), "应该有player_progress字段")
	assert_true(save_data.has("quest_progress"), "应该有quest_progress字段")
	assert_true(save_data.has("play_stats"), "应该有play_stats字段")

	# 验证版本号
	assert_eq(save_data.get("schema_version"), SaveManager.SAVE_SCHEMA_VERSION, "版本号应该匹配")

func test_no_save_file() -> void:
	# 删除可能存在的存档
	SaveManager.delete_save("nonexistent")

	# 尝试加载不存在的存档
	var load_result: Dictionary = SaveManager.load_game("nonexistent")
	assert_false(load_result.get("success", true), "加载不存在的存档应该失败")
	assert_not_empty(load_result.get("error", ""), "应该返回错误信息")

	# 验证has_save_file返回false
	assert_false(SaveManager.has_save_file("nonexistent"), "不存在的存档应该返回false")

func test_delete_save() -> void:
	# 创建存档
	GameState.player_name = "删除测试玩家"
	var save_result: Dictionary = SaveManager.save_game("test_delete")
	assert_true(save_result.get("success", false), "保存应该成功启动")
	await _wait_for_save_complete()
	assert_true(SaveManager.has_save_file("test_delete"), "存档应该存在")

	# 删除存档
	var delete_result: bool = SaveManager.delete_save("test_delete")
	assert_true(delete_result, "删除应该成功")
	assert_false(SaveManager.has_save_file("test_delete"), "存档不应该存在")

func test_autosave_trigger() -> void:
	# 模拟自动保存
	var autosave_result: Dictionary = SaveManager.autosave()
	assert_true(autosave_result.get("success", false), "自动保存应该成功启动")
	await _wait_for_save_complete()
	assert_true(SaveManager.has_save_file("autosave"), "自动存档应该存在")

func test_gamestate_restore() -> void:
	# 设置游戏状态
	GameState.player_level = 10
	GameState.player_exp = 5000
	GameState.player_health = 50
	GameState.chapter_id = "chapter_03"

	# 获取存档数据
	var save_data: Dictionary = GameState.get_save_data()
	assert_not_null(save_data, "应该返回存档数据")
	assert_eq(save_data.get("player_level"), 10, "等级应该正确")
	assert_eq(save_data.get("player_exp"), 5000, "经验应该正确")
	assert_eq(save_data.get("chapter_id"), "chapter_03", "章节应该正确")

	# 重置状态
	GameState.reset_state()
	assert_eq(GameState.player_level, 1, "重置后等级应该为1")

	# 从存档恢复
	GameState.restore_from_save_data(save_data)
	assert_eq(GameState.player_level, 10, "恢复后等级应该正确")
	assert_eq(GameState.player_exp, 5000, "恢复后经验应该正确")
	assert_eq(GameState.chapter_id, "chapter_03", "恢复后章节应该正确")

func test_playermanager_quest_restore() -> void:
	# 设置任务数据
	PlayerManager.player_quests = [
		{"quest_id": "quest_active_001", "status": "active", "progress": 30},
		{"quest_id": "quest_completed_001", "status": "completed", "progress": 100}
	]
	PlayerManager._update_quest_index()

	# 获取任务存档数据
	var quest_data: Dictionary = PlayerManager.get_quest_save_data()
	assert_not_null(quest_data, "应该返回任务存档数据")
	assert_true(quest_data.has("quests_active"), "应该有quests_active字段")
	assert_true(quest_data.has("quests_completed"), "应该有quests_completed字段")

	# 重置任务
	PlayerManager.player_quests.clear()
	PlayerManager.quest_index.clear()
	assert_eq(PlayerManager.player_quests.size(), 0, "清空后任务数量应该为0")

	# 从存档恢复
	PlayerManager.restore_quest_from_save_data(quest_data)
	assert_eq(PlayerManager.player_quests.size(), 2, "恢复后任务数量应该正确")

func test_save_info() -> void:
	# 设置游戏状态
	GameState.player_name = "存档信息测试"
	GameState.player_level = 7

	# 保存游戏
	SaveManager.save_game("test_info")
	await _wait_for_save_complete()

	# 获取存档信息
	var info: Dictionary = SaveManager.get_save_info("test_info")
	assert_not_empty(info, "应该返回存档信息")
	assert_eq(info.get("player_name"), "存档信息测试", "玩家名称应该正确")
	assert_eq(info.get("player_level"), 7, "玩家等级应该正确")

func test_quick_save_and_load() -> void:
	# 设置游戏状态
	GameState.player_name = "快速存档测试"

	# 快速保存
	var save_result: Dictionary = SaveManager.quick_save()
	assert_true(save_result.get("success", false), "快速保存应该成功启动")
	await _wait_for_save_complete()
	assert_true(SaveManager.has_save_file("quicksave"), "快速存档应该存在")

	# 重置状态
	GameState.reset_state()

	# 快速加载
	var load_result: Dictionary = SaveManager.quick_load()
	assert_true(load_result.get("success", false), "快速加载应该成功启动")
	await _wait_for_load_complete()
	assert_eq(GameState.player_name, "快速存档测试", "玩家名称应该恢复")

# ===== 异步存档与缓存机制测试（S8-01 第三阶段）=====

func test_save_info_cache_ttl_constant() -> void:
	assert_eq(SaveManager.SAVE_INFO_CACHE_TTL, 60000, "缓存 TTL 常量应为 60000 毫秒")

func test_save_info_cache_initial_empty() -> void:
	SaveManager.reset_cache()
	assert_eq(SaveManager.save_info_cache.size(), 0, "save_info_cache 初始应为空")
	assert_eq(SaveManager.save_info_cache_timestamps.size(), 0, "save_info_cache_timestamps 初始应为空")

func test_is_saving_is_loading_initial_false() -> void:
	assert_false(SaveManager.is_saving, "is_saving 初始应为 false")
	assert_false(SaveManager.is_loading, "is_loading 初始应为 false")

func test_is_save_info_cache_valid_no_entry() -> void:
	SaveManager.reset_cache()
	# 缓存中无对应槽位，应返回 false
	assert_false(SaveManager._is_save_info_cache_valid("nonexistent_slot"), "无缓存条目时应返回 false")

func test_update_save_info_cache_writes_entry() -> void:
	SaveManager.reset_cache()
	var info: Dictionary = {"player_name": "缓存测试", "player_level": 5}
	SaveManager._update_save_info_cache("test_cache_slot", info)
	assert_true(SaveManager.save_info_cache.has("test_cache_slot"), "缓存应包含写入的槽位")
	assert_eq(SaveManager.save_info_cache["test_cache_slot"]["player_name"], "缓存测试", "缓存数据应正确")
	assert_true(SaveManager.save_info_cache_timestamps.has("test_cache_slot"), "时间戳应被记录")

func test_is_save_info_cache_valid_after_update() -> void:
	SaveManager.reset_cache()
	var info: Dictionary = {"player_name": "有效缓存测试"}
	SaveManager._update_save_info_cache("valid_slot", info)
	# 写入后立即检查应有效（未超 TTL）
	assert_true(SaveManager._is_save_info_cache_valid("valid_slot"), "刚写入的缓存应有效")

func test_invalidate_save_info_cache_single_slot() -> void:
	SaveManager.reset_cache()
	SaveManager._update_save_info_cache("slot_a", {"name": "A"})
	SaveManager._update_save_info_cache("slot_b", {"name": "B"})
	# 仅失效 slot_a
	SaveManager._invalidate_save_info_cache("slot_a")
	assert_false(SaveManager.save_info_cache.has("slot_a"), "slot_a 缓存应被清除")
	assert_false(SaveManager.save_info_cache_timestamps.has("slot_a"), "slot_a 时间戳应被清除")
	assert_true(SaveManager.save_info_cache.has("slot_b"), "slot_b 缓存应保留")

func test_invalidate_save_info_cache_all() -> void:
	SaveManager._update_save_info_cache("slot_a", {"name": "A"})
	SaveManager._update_save_info_cache("slot_b", {"name": "B"})
	# 传空字符串应清空全部
	SaveManager._invalidate_save_info_cache("")
	assert_eq(SaveManager.save_info_cache.size(), 0, "全部缓存应被清空")
	assert_eq(SaveManager.save_info_cache_timestamps.size(), 0, "全部时间戳应被清空")

func test_reset_cache_clears_all() -> void:
	SaveManager._update_save_info_cache("slot_a", {"name": "A"})
	SaveManager._update_save_info_cache("slot_b", {"name": "B"})
	SaveManager.reset_cache()
	assert_eq(SaveManager.save_info_cache.size(), 0, "reset_cache 后缓存应为空")
	assert_eq(SaveManager.save_info_cache_timestamps.size(), 0, "reset_cache 后时间戳应为空")

func test_get_save_info_uses_cache_on_second_call() -> void:
	SaveManager.reset_cache()
	# 准备存档
	GameState.player_name = "缓存命中测试"
	GameState.player_level = 8
	SaveManager.save_game("test_cache_hit")
	await _wait_for_save_complete()

	# 第一次调用：从文件读取并写入缓存
	var info_first: Dictionary = SaveManager.get_save_info("test_cache_hit")
	assert_eq(info_first.get("player_name"), "缓存命中测试", "首次读取应返回正确玩家名")
	assert_true(SaveManager.save_info_cache.has("test_cache_hit"), "首次读取后应写入缓存")

	# 第二次调用：应命中缓存（数据一致）
	var info_second: Dictionary = SaveManager.get_save_info("test_cache_hit")
	assert_eq(info_second.get("player_name"), "缓存命中测试", "缓存命中应返回相同数据")
	assert_eq(info_second.get("player_level"), 8, "缓存命中应返回相同等级")

	# 清理
	SaveManager.delete_save("test_cache_hit")
	SaveManager.reset_cache()

func test_get_save_info_returns_empty_for_nonexistent() -> void:
	SaveManager.reset_cache()
	var info: Dictionary = SaveManager.get_save_info("nonexistent_info_slot")
	assert_eq(info.size(), 0, "不存在的存档应返回空字典")
	assert_false(SaveManager.save_info_cache.has("nonexistent_info_slot"), "不存在的存档不应写入缓存")

func test_async_save_game_returns_started_status() -> void:
	SaveManager.reset_cache()
	GameState.player_name = "异步保存测试"
	# 异步保存应立即返回启动状态，而非等待保存完成
	var result: Dictionary = SaveManager.save_game("test_async_save")
	assert_true(result.get("success", false), "异步保存应返回 success=true")
	assert_eq(result.get("message", ""), "保存已启动", "异步保存应返回启动消息")
	# 异步返回不应包含 save_id（save_id 在线程完成后通过信号传递）
	assert_false(result.has("save_id"), "异步启动返回不应包含 save_id")
	# 等待保存线程完成
	await _wait_for_save_complete()
	assert_true(SaveManager.has_save_file("test_async_save"), "异步保存完成后文件应存在")
	# 清理
	SaveManager.delete_save("test_async_save")
	SaveManager.reset_cache()

func test_async_load_game_returns_started_status() -> void:
	# 先准备一个存档
	GameState.player_name = "异步加载准备"
	SaveManager.save_game("test_async_load_prep")
	await _wait_for_save_complete()
	GameState.reset_state()

	# 异步加载应立即返回启动状态
	var result: Dictionary = SaveManager.load_game("test_async_load_prep")
	assert_true(result.get("success", false), "异步加载应返回 success=true")
	assert_eq(result.get("message", ""), "加载已启动", "异步加载应返回启动消息")
	# 等待加载线程完成
	await _wait_for_load_complete()
	assert_eq(GameState.player_name, "异步加载准备", "异步加载完成后玩家名应恢复")
	# 清理
	SaveManager.delete_save("test_async_load_prep")
	SaveManager.reset_cache()

func test_async_load_nonexistent_returns_failure() -> void:
	var result: Dictionary = SaveManager.load_game("nonexistent_async_load")
	assert_false(result.get("success", true), "加载不存在的存档应返回失败")
	assert_not_empty(result.get("error", ""), "应返回错误信息")

func test_save_invalidate_cache_on_save() -> void:
	SaveManager.reset_cache()
	# 准备存档并读取信息（写入缓存）
	GameState.player_name = "缓存失效测试_初始"
	SaveManager.save_game("test_invalidate")
	await _wait_for_save_complete()
	var info_first: Dictionary = SaveManager.get_save_info("test_invalidate")
	assert_eq(info_first.get("player_name"), "缓存失效测试_初始", "首次读取应返回初始名称")
	assert_true(SaveManager.save_info_cache.has("test_invalidate"), "缓存应已写入")

	# 再次保存（应触发缓存失效）
	GameState.player_name = "缓存失效测试_更新"
	SaveManager.save_game("test_invalidate")
	await _wait_for_save_complete()

	# 保存后缓存应已失效，再次读取应从文件获取最新数据
	var info_second: Dictionary = SaveManager.get_save_info("test_invalidate")
	assert_eq(info_second.get("player_name"), "缓存失效测试_更新", "保存后应返回更新后的名称")
	# 清理
	SaveManager.delete_save("test_invalidate")
	SaveManager.reset_cache()

# 辅助方法：等待保存线程完成
func _wait_for_save_complete(max_wait_msec: int = 2000) -> void:
	var elapsed: int = 0
	var step: int = 50
	while SaveManager.is_saving and elapsed < max_wait_msec:
		OS.delay_msec(step)
		elapsed += step
		# 处理 deferred 调用以触发 _on_save_complete
		var tree: SceneTree = get_tree()
		if tree:
			await tree.process_frame

# 辅助方法：等待加载线程完成
func _wait_for_load_complete(max_wait_msec: int = 2000) -> void:
	var elapsed: int = 0
	var step: int = 50
	while SaveManager.is_loading and elapsed < max_wait_msec:
		OS.delay_msec(step)
		elapsed += step
		# 处理 deferred 调用以触发 _on_load_complete
		var tree: SceneTree = get_tree()
		if tree:
			await tree.process_frame
