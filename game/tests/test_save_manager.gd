extends GutTest
## SaveManager 存档系统测试

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
	# 重置游戏状态
	GameState.reset_state()
	PlayerManager.reset()

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
	
	# 保存游戏
	var save_result: Dictionary = SaveManager.save_game("test_slot")
	assert_true(save_result.get("success", false), "保存应该成功")
	assert_not_null(save_result.get("save_id", null), "应该返回存档ID")
	
	# 验证存档文件存在
	assert_true(SaveManager.has_save_file("test_slot"), "存档文件应该存在")
	
	# 重置游戏状态
	GameState.reset_state()
	PlayerManager.reset()
	
	# 加载游戏
	var load_result: Dictionary = SaveManager.load_game("test_slot")
	assert_true(load_result.get("success", false), "加载应该成功")
	
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
	assert_true(save_result.get("success", false), "保存应该成功")
	
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
	assert_true(save_result.get("success", false), "保存应该成功")
	assert_true(SaveManager.has_save_file("test_delete"), "存档应该存在")
	
	# 删除存档
	var delete_result: bool = SaveManager.delete_save("test_delete")
	assert_true(delete_result, "删除应该成功")
	assert_false(SaveManager.has_save_file("test_delete"), "存档不应该存在")

func test_autosave_trigger() -> void:
	# 模拟自动保存
	var autosave_result: Dictionary = SaveManager.autosave()
	assert_true(autosave_result.get("success", false), "自动保存应该成功")
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
	
	# 获取任务存档数据
	var quest_data: Dictionary = PlayerManager.get_quest_save_data()
	assert_not_null(quest_data, "应该返回任务存档数据")
	assert_true(quest_data.has("quests_active"), "应该有quests_active字段")
	assert_true(quest_data.has("quests_completed"), "应该有quests_completed字段")
	
	# 重置任务
	PlayerManager.player_quests.clear()
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
	assert_true(save_result.get("success", false), "快速保存应该成功")
	assert_true(SaveManager.has_save_file("quicksave"), "快速存档应该存在")
	
	# 重置状态
	GameState.reset_state()
	
	# 快速加载
	var load_result: Dictionary = SaveManager.quick_load()
	assert_true(load_result.get("success", false), "快速加载应该成功")
	assert_eq(GameState.player_name, "快速存档测试", "玩家名称应该恢复")