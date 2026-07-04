extends Node
## 游戏全局状态管理
## 负责管理玩家信息、当前章节、区域状态等全局状态

signal player_info_changed
signal chapter_changed
signal region_unlocked(region_id: String)

var player_id: String = ""
var player_name: String = ""
var chapter_id: String = "chapter_01"
var unlocked_regions: Array[String] = []
var reputation_snapshot: Dictionary = {}
var schema_version: int = 1

func _ready() -> void:
	_load_local_state()

func set_player_info(p_id: String, p_name: String) -> void:
	player_id = p_id
	player_name = p_name
	_save_local_state()
	player_info_changed.emit()

func get_player_id() -> String:
	return player_id

func is_logged_in() -> bool:
	return player_id != ""

func unlock_region(region_id: String) -> void:
	if not region_id in unlocked_regions:
		unlocked_regions.append(region_id)
		_save_local_state()
		region_unlocked.emit(region_id)

func is_region_unlocked(region_id: String) -> bool:
	return region_id in unlocked_regions

func set_chapter(chapter_id: String) -> void:
	self.chapter_id = chapter_id
	_save_local_state()
	chapter_changed.emit()

func get_chapter() -> String:
	return chapter_id

func _save_local_state() -> void:
	var save_data: Dictionary = {
		"schema_version": schema_version,
		"player_id": player_id,
		"player_name": player_name,
		"chapter_id": chapter_id,
		"unlocked_regions": unlocked_regions,
		"reputation_snapshot": reputation_snapshot
	}
	var file := FileAccess.open("user://game_state.json", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(save_data))
		file.close()

func _load_local_state() -> void:
	if not FileAccess.file_exists("user://game_state.json"):
		return
	var file := FileAccess.open("user://game_state.json", FileAccess.READ)
	if file:
		var content: String = file.get_as_text()
		file.close()
		var parsed: Variant = JSON.parse_string(content)
		if typeof(parsed) == TYPE_DICTIONARY:
			var data: Dictionary = parsed
			if data.has("schema_version"):
				schema_version = data["schema_version"]
			if data.has("player_id"):
				player_id = data["player_id"]
			if data.has("player_name"):
				player_name = data["player_name"]
			if data.has("chapter_id"):
				chapter_id = data["chapter_id"]
			if data.has("unlocked_regions"):
				unlocked_regions = data["unlocked_regions"]
			if data.has("reputation_snapshot"):
				reputation_snapshot = data["reputation_snapshot"]

func reset_state() -> void:
	player_id = ""
	player_name = ""
	chapter_id = "chapter_01"
	unlocked_regions.clear()
	reputation_snapshot.clear()
	_save_local_state()
	player_info_changed.emit()
	chapter_changed.emit()
