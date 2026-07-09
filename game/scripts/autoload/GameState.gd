extends Node
## 游戏全局状态管理
## 负责管理玩家信息、当前章节、区域状态等全局状态

signal player_info_changed
signal chapter_changed
signal region_unlocked(region_id: String)
signal health_changed(current_health: int, max_health: int)
signal player_died
signal player_revived

var player_id: String = ""
var player_name: String = ""
var player_level: int = 1
var player_exp: int = 0
var chapter_id: String = "chapter_01"
var unlocked_regions: Array[String] = []
var reputation_snapshot: Dictionary = {}
var vote_participation: Array[String] = []
var last_vote_cycle_id: String = ""
var schema_version: int = 2

# 战斗属性
var player_health: int = 100
var player_max_health: int = 100
var player_attack: int = 10
var player_defense: int = 5
var is_alive: bool = true

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

func record_vote_participation(vote_cycle_id: String) -> void:
	if not vote_cycle_id in vote_participation:
		vote_participation.append(vote_cycle_id)
	last_vote_cycle_id = vote_cycle_id
	_save_local_state()

func has_voted_in_cycle(vote_cycle_id: String) -> bool:
	return vote_cycle_id in vote_participation

func add_exp(amount: int) -> void:
	player_exp += amount
	_save_local_state()
	player_info_changed.emit()

# 战斗相关方法
func take_damage(amount: int) -> int:
	if not is_alive:
		return 0
	
	var actual_damage: int = maxi(amount - player_defense, 1)
	player_health = maxi(player_health - actual_damage, 0)
	
	if player_health <= 0:
		is_alive = false
		player_died.emit()
	
	health_changed.emit(player_health, player_max_health)
	_save_local_state()
	return actual_damage

func heal(amount: int) -> void:
	if not is_alive:
		return
	
	player_health = mini(player_health + amount, player_max_health)
	health_changed.emit(player_health, player_max_health)
	_save_local_state()

func reset_health() -> void:
	player_health = player_max_health
	is_alive = true
	health_changed.emit(player_health, player_max_health)
	player_revived.emit()
	_save_local_state()

func get_health_percent() -> float:
	if player_max_health <= 0:
		return 0.0
	return float(player_health) / float(player_max_health)

func calculate_damage(target_defense: int) -> int:
	return maxi(player_attack - target_defense, 1)

func update_combat_stats() -> void:
	# 根据等级更新战斗属性
	player_max_health = 100 + (player_level - 1) * 20
	player_attack = 10 + (player_level - 1) * 2
	player_defense = 5 + (player_level - 1) * 1
	
	# 如果当前血量超过最大值，调整到最大值
	if player_health > player_max_health:
		player_health = player_max_health
	
	health_changed.emit(player_health, player_max_health)
	_save_local_state()

func _save_local_state() -> void:
	var save_data: Dictionary = {
		"schema_version": schema_version,
		"player_id": player_id,
		"player_name": player_name,
		"player_level": player_level,
		"player_exp": player_exp,
		"chapter_id": chapter_id,
		"unlocked_regions": unlocked_regions,
		"reputation_snapshot": reputation_snapshot,
		"vote_participation": vote_participation,
		"last_vote_cycle_id": last_vote_cycle_id,
		"player_health": player_health,
		"player_max_health": player_max_health,
		"player_attack": player_attack,
		"player_defense": player_defense,
		"is_alive": is_alive
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
			if data.has("player_level"):
				player_level = data["player_level"]
			if data.has("player_exp"):
				player_exp = data["player_exp"]
			if data.has("vote_participation"):
				vote_participation = data["vote_participation"]
			if data.has("last_vote_cycle_id"):
				last_vote_cycle_id = data["last_vote_cycle_id"]
			if data.has("player_health"):
				player_health = data["player_health"]
			if data.has("player_max_health"):
				player_max_health = data["player_max_health"]
			if data.has("player_attack"):
				player_attack = data["player_attack"]
			if data.has("player_defense"):
				player_defense = data["player_defense"]
			if data.has("is_alive"):
				is_alive = data["is_alive"]

func reset_state() -> void:
	player_id = ""
	player_name = ""
	player_level = 1
	player_exp = 0
	chapter_id = "chapter_01"
	unlocked_regions.clear()
	reputation_snapshot.clear()
	vote_participation.clear()
	last_vote_cycle_id = ""
	player_health = 100
	player_max_health = 100
	player_attack = 10
	player_defense = 5
	is_alive = true
	_save_local_state()
	player_info_changed.emit()
	chapter_changed.emit()
	health_changed.emit(player_health, player_max_health)

# 存档系统支持方法
func get_save_data() -> Dictionary:
	return {
		"player_id": player_id,
		"player_name": player_name,
		"player_level": player_level,
		"player_exp": player_exp,
		"chapter_id": chapter_id,
		"unlocked_regions": unlocked_regions,
		"reputation_snapshot": reputation_snapshot,
		"vote_participation": vote_participation,
		"last_vote_cycle_id": last_vote_cycle_id,
		"player_health": player_health,
		"player_max_health": player_max_health,
		"player_attack": player_attack,
		"player_defense": player_defense,
		"is_alive": is_alive
	}

func restore_from_save_data(data: Dictionary) -> void:
	if data.has("player_id"):
		player_id = data["player_id"]
	if data.has("player_name"):
		player_name = data["player_name"]
	if data.has("player_level"):
		player_level = data["player_level"]
	if data.has("player_exp"):
		player_exp = data["player_exp"]
	if data.has("chapter_id"):
		chapter_id = data["chapter_id"]
	if data.has("unlocked_regions"):
		unlocked_regions = data["unlocked_regions"]
	if data.has("reputation_snapshot"):
		reputation_snapshot = data["reputation_snapshot"]
	if data.has("vote_participation"):
		vote_participation = data["vote_participation"]
	if data.has("last_vote_cycle_id"):
		last_vote_cycle_id = data["last_vote_cycle_id"]
	if data.has("player_health"):
		player_health = data["player_health"]
	if data.has("player_max_health"):
		player_max_health = data["player_max_health"]
	if data.has("player_attack"):
		player_attack = data["player_attack"]
	if data.has("player_defense"):
		player_defense = data["player_defense"]
	if data.has("is_alive"):
		is_alive = data["is_alive"]
	
	_save_local_state()
	player_info_changed.emit()
	health_changed.emit(player_health, player_max_health)
