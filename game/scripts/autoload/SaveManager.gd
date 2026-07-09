extends Node
## 存档管理单例
## 负责玩家数据的保存、加载、自动保存等核心存档功能

signal save_completed(save_id: String)
signal load_completed(save_id: String)
signal save_failed(error_message: String)
signal load_failed(error_message: String)
signal autosave_triggered
signal autosave_completed

const SAVE_SCHEMA_VERSION: int = 1
const DEFAULT_SAVE_PATH: String = "user://saves/"
const DEFAULT_SAVE_FILE: String = "save_main.json"
const CONFIG_PATH: String = "res://data/config/save_config.json"

var config: Dictionary = {}
var autosave_timer: Timer = null
var last_save_time: int = 0
var play_time_start: int = 0
var is_saving: bool = false
var is_loading: bool = false

func _ready() -> void:
	_load_config()
	_setup_autosave_timer()
	_ensure_save_directory()
	play_time_start = Time.get_ticks_msec()

func _load_config() -> void:
	var file := FileAccess.open(CONFIG_PATH, FileAccess.READ)
	if file:
		var content: String = file.get_as_text()
		file.close()
		var parsed: Variant = JSON.parse_string(content)
		if typeof(parsed) == TYPE_DICTIONARY:
			config = parsed

func _setup_autosave_timer() -> void:
	if not config.get("autosave", {}).get("enabled", true):
		return
	
	autosave_timer = Timer.new()
	var interval: int = config.get("autosave", {}).get("interval_seconds", 300)
	autosave_timer.wait_time = interval
	autosave_timer.one_shot = false
	autosave_timer.timeout.connect(_on_autosave_timer_timeout)
	add_child(autosave_timer)
	autosave_timer.start()

func _ensure_save_directory() -> void:
	var save_path: String = config.get("file", {}).get("save_path", DEFAULT_SAVE_PATH)
	var dir := DirAccess.open("user://")
	if dir and not dir.dir_exists(save_path.replace("user://", "")):
		dir.make_dir_recursive(save_path.replace("user://", ""))

func save_game(slot: String = "main") -> Dictionary:
	if is_saving:
		return {"success": false, "error": "正在保存中"}
	
	is_saving = true
	var save_data: Dictionary = _build_save_data()
	var save_path: String = _get_save_path(slot)
	
	var file := FileAccess.open(save_path, FileAccess.WRITE)
	if not file:
		is_saving = false
		var error_msg: String = "无法创建存档文件: %s" % save_path
		save_failed.emit(error_msg)
		return {"success": false, "error": error_msg}
	
	var json_string: String = JSON.stringify(save_data)
	file.store_string(json_string)
	file.close()
	
	# 备份存档
	if config.get("file", {}).get("backup_enabled", true):
		_create_backup(slot)
	
	is_saving = false
	last_save_time = Time.get_ticks_msec()
	
	var save_id: String = save_data.get("save_id", "")
	save_completed.emit(save_id)
	
	return {"success": true, "save_id": save_id, "path": save_path}

func _build_save_data() -> Dictionary:
	var current_time: String = Time.get_datetime_string_from_system()
	var play_time_seconds: int = _calculate_play_time()
	
	var save_data: Dictionary = {
		"schema_version": SAVE_SCHEMA_VERSION,
		"save_id": _generate_save_id(),
		"created_at": current_time,
		"updated_at": current_time,
		"player_profile": _get_player_profile(),
		"player_position": _get_player_position(),
		"player_attributes": _get_player_attributes(),
		"player_progress": _get_player_progress(),
		"quest_progress": _get_quest_progress(),
		"play_stats": _get_play_stats(play_time_seconds)
	}
	
	return save_data

func _generate_save_id() -> String:
	return "save_%s" % Time.get_datetime_string_from_system().replace(":", "").replace("-", "").replace(" ", "_")

func _get_player_profile() -> Dictionary:
	return {
		"player_id": GameState.player_id,
		"display_name": GameState.player_name,
		"created_at": Time.get_datetime_string_from_system(),
		"last_played_at": Time.get_datetime_string_from_system()
	}

func _get_player_position() -> Dictionary:
	# 从当前场景获取位置信息
	var current_scene_path: String = ""
	var pos_x: float = 0.0
	var pos_y: float = 0.0
	var region_id: String = ""
	
	# 尝试从当前场景获取玩家位置
	if get_tree().current_scene:
		current_scene_path = get_tree().current_scene.scene_file_path
		var player_nodes: Array = get_tree().get_nodes_in_group("player")
		if player_nodes.size() > 0:
			var player: Node2D = player_nodes[0]
			if player is Node2D:
				pos_x = player.global_position.x
				pos_y = player.global_position.y
	
	return {
		"current_scene": current_scene_path,
		"position_x": pos_x,
		"position_y": pos_y,
		"current_region_id": region_id
	}

func _get_player_attributes() -> Dictionary:
	return {
		"level": GameState.player_level,
		"experience": GameState.player_exp,
		"health": GameState.player_health,
		"max_health": GameState.player_max_health,
		"attack": GameState.player_attack,
		"defense": GameState.player_defense,
		"is_alive": GameState.is_alive
	}

func _get_player_progress() -> Dictionary:
	return {
		"chapter_id": GameState.chapter_id,
		"unlocked_regions": GameState.unlocked_regions,
		"vote_participation": GameState.vote_participation
	}

func _get_quest_progress() -> Dictionary:
	var active_quests: Array[Dictionary] = PlayerManager.get_active_quests()
	var completed_quests: Array[Dictionary] = PlayerManager.get_completed_quests()
	
	var active_list: Array = []
	for quest in active_quests:
		active_list.append({
			"quest_id": quest.get("quest_id", ""),
			"progress": quest.get("progress", 0)
		})
	
	var completed_list: Array = []
	for quest in completed_quests:
		completed_list.append(quest.get("quest_id", ""))
	
	return {
		"quests_active": active_list,
		"quests_completed": completed_list
	}

func _get_play_stats(play_time_seconds: int) -> Dictionary:
	return {
		"total_play_time_seconds": play_time_seconds,
		"regions_visited": GameState.unlocked_regions,
		"npcs_met": [],
		"enemies_defeated": 0
	}

func _calculate_play_time() -> int:
	if play_time_start == 0:
		return 0
	return (Time.get_ticks_msec() - play_time_start) / 1000

func load_game(slot: String = "main") -> Dictionary:
	if is_loading:
		return {"success": false, "error": "正在加载中"}
	
	var save_path: String = _get_save_path(slot)
	
	if not has_save_file(slot):
		var error_msg: String = "存档不存在: %s" % slot
		load_failed.emit(error_msg)
		return {"success": false, "error": error_msg}
	
	is_loading = true
	
	var file := FileAccess.open(save_path, FileAccess.READ)
	if not file:
		is_loading = false
		var error_msg: String = "无法读取存档文件: %s" % save_path
		load_failed.emit(error_msg)
		return {"success": false, "error": error_msg}
	
	var content: String = file.get_as_text()
	file.close()
	
	var parsed: Variant = JSON.parse_string(content)
	if typeof(parsed) != TYPE_DICTIONARY:
		is_loading = false
		var error_msg: String = "存档数据格式错误"
		load_failed.emit(error_msg)
		return {"success": false, "error": error_msg}
	
	var save_data: Dictionary = parsed
	
	# 验证存档版本
	if not _validate_save_data(save_data):
		is_loading = false
		var error_msg: String = "存档数据验证失败"
		load_failed.emit(error_msg)
		return {"success": false, "error": error_msg}
	
	# 恢复游戏状态
	_restore_game_state(save_data)
	
	is_loading = false
	play_time_start = Time.get_ticks_msec()
	
	var save_id: String = save_data.get("save_id", "")
	load_completed.emit(save_id)
	
	return {"success": true, "save_id": save_id, "data": save_data}

func _validate_save_data(save_data: Dictionary) -> bool:
	if not save_data.has("schema_version"):
		return false
	
	var schema_version: int = save_data.get("schema_version", 0)
	if schema_version > SAVE_SCHEMA_VERSION:
		push_warning("存档版本高于当前版本: %d > %d" % [schema_version, SAVE_SCHEMA_VERSION])
	
	return true

func _restore_game_state(save_data: Dictionary) -> void:
	# 恢复玩家档案
	var profile: Dictionary = save_data.get("player_profile", {})
	if profile.has("player_id"):
		GameState.player_id = profile["player_id"]
	if profile.has("display_name"):
		GameState.player_name = profile["display_name"]
	
	# 恢复玩家属性
	var attributes: Dictionary = save_data.get("player_attributes", {})
	if attributes.has("level"):
		GameState.player_level = attributes["level"]
	if attributes.has("experience"):
		GameState.player_exp = attributes["experience"]
	if attributes.has("health"):
		GameState.player_health = attributes["health"]
	if attributes.has("max_health"):
		GameState.player_max_health = attributes["max_health"]
	if attributes.has("attack"):
		GameState.player_attack = attributes["attack"]
	if attributes.has("defense"):
		GameState.player_defense = attributes["defense"]
	if attributes.has("is_alive"):
		GameState.is_alive = attributes["is_alive"]
	
	# 恢复玩家进度
	var progress: Dictionary = save_data.get("player_progress", {})
	if progress.has("chapter_id"):
		GameState.chapter_id = progress["chapter_id"]
	if progress.has("unlocked_regions"):
		GameState.unlocked_regions = progress["unlocked_regions"]
	if progress.has("vote_participation"):
		GameState.vote_participation = progress["vote_participation"]
	
	# 恢复任务进度
	_restore_quest_progress(save_data.get("quest_progress", {}))
	
	# 触发状态更新信号
	GameState.player_info_changed.emit()
	GameState.health_changed.emit(GameState.player_health, GameState.player_max_health)

func _restore_quest_progress(quest_data: Dictionary) -> void:
	# 清空当前任务列表
	PlayerManager.player_quests.clear()
	
	# 恢复进行中的任务
	var active_quests: Array = quest_data.get("quests_active", [])
	for quest in active_quests:
		if quest is Dictionary:
			PlayerManager.player_quests.append({
				"quest_id": quest.get("quest_id", ""),
				"status": "active",
				"progress": quest.get("progress", 0)
			})
	
	# 恢复已完成的任务
	var completed_quests: Array = quest_data.get("quests_completed", [])
	for quest_id in completed_quests:
		if quest_id is String:
			PlayerManager.player_quests.append({
				"quest_id": quest_id,
				"status": "completed",
				"progress": 100
			})
	
	PlayerManager.player_quests_loaded.emit()

func has_save_file(slot: String = "main") -> bool:
	var save_path: String = _get_save_path(slot)
	return FileAccess.file_exists(save_path)

func delete_save(slot: String = "main") -> bool:
	var save_path: String = _get_save_path(slot)
	
	if not FileAccess.file_exists(save_path):
		return true
	
	var dir := DirAccess.open("user://saves/")
	if dir:
		var error: int = dir.remove(save_path.replace("user://saves/", ""))
		return error == OK
	
	return false

func get_save_info(slot: String = "main") -> Dictionary:
	if not has_save_file(slot):
		return {}
	
	var save_path: String = _get_save_path(slot)
	var file := FileAccess.open(save_path, FileAccess.READ)
	if not file:
		return {}
	
	var content: String = file.get_as_text()
	file.close()
	
	var parsed: Variant = JSON.parse_string(content)
	if typeof(parsed) != TYPE_DICTIONARY:
		return {}
	
	var save_data: Dictionary = parsed
	
	return {
		"save_id": save_data.get("save_id", ""),
		"created_at": save_data.get("created_at", ""),
		"updated_at": save_data.get("updated_at", ""),
		"player_name": save_data.get("player_profile", {}).get("display_name", ""),
		"player_level": save_data.get("player_attributes", {}).get("level", 1),
		"chapter_id": save_data.get("player_progress", {}).get("chapter_id", "")
	}

func quick_save() -> Dictionary:
	return save_game("quicksave")

func quick_load() -> Dictionary:
	return load_game("quicksave")

func autosave() -> Dictionary:
	autosave_triggered.emit()
	var result: Dictionary = save_game("autosave")
	autosave_completed.emit()
	return result

func _get_save_path(slot: String) -> String:
	var save_path: String = config.get("file", {}).get("save_path", DEFAULT_SAVE_PATH)
	return "%ssave_%s.json" % [save_path, slot]

func _create_backup(slot: String) -> void:
	var save_path: String = _get_save_path(slot)
	var backup_path: String = save_path.replace(".json", ".backup.json")
	
	if not FileAccess.file_exists(save_path):
		return
	
	var dir := DirAccess.open("user://saves/")
	if dir:
		dir.copy(save_path.replace("user://saves/", ""), backup_path.replace("user://saves/", ""))

func _on_autosave_timer_timeout() -> void:
	if config.get("autosave", {}).get("enabled", true):
		autosave()

func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		if config.get("autosave", {}).get("on_exit", true):
			save_game("exit_backup")
		get_tree().quit()

func get_play_time_string() -> String:
	var total_seconds: int = _calculate_play_time()
	var hours: int = total_seconds / 3600
	var minutes: int = (total_seconds % 3600) / 60
	var seconds: int = total_seconds % 60
	return "%02d:%02d:%02d" % [hours, minutes, seconds]