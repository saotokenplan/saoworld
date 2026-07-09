extends Node
## 战斗管理单例
## 负责管理战斗流程、伤害计算、胜负判定

signal combat_started(enemy_type: String)
signal combat_ended(result: String, exp_gained: int)
signal turn_completed(attacker: String, target: String, damage: int)
signal health_updated(entity_type: String, current_health: int, max_health: int)
signal damage_dealt(target: String, damage: int)
signal enemy_defeated(enemy_type: String)

enum CombatState { IDLE, IN_COMBAT, VICTORY, DEFEAT }

var current_state: CombatState = CombatState.IDLE
var current_enemy: Dictionary = {}
var enemy_health: int = 0
var enemy_max_health: int = 0

const ENEMY_DATA_PATH: String = "res://data/enemies/enemy_list.json"
var enemy_data: Dictionary = {}

func _ready() -> void:
	_load_enemy_data()

func _load_enemy_data() -> void:
	var file: FileAccess = FileAccess.open(ENEMY_DATA_PATH, FileAccess.READ)
	if not file:
		return
	
	var content: String = file.get_as_text()
	file.close()
	
	var data: Dictionary = JSON.parse_string(content)
	if data is Dictionary:
		enemy_data = data

func get_enemy_data(enemy_type: String) -> Dictionary:
	if enemy_data.has("enemies"):
		for enemy in enemy_data["enemies"]:
			if enemy.get("enemy_type", "") == enemy_type:
				return enemy
	return {}

func start_combat(enemy_type: String) -> bool:
	if current_state != CombatState.IDLE:
		return false
	
	current_enemy = get_enemy_data(enemy_type)
	if current_enemy.is_empty():
		return false
	
	enemy_health = current_enemy.get("health", 50)
	enemy_max_health = enemy_health
	
	current_state = CombatState.IN_COMBAT
	combat_started.emit(enemy_type)
	health_updated.emit("enemy", enemy_health, enemy_max_health)
	health_updated.emit("player", GameState.player_health, GameState.player_max_health)
	
	return true

func player_attack() -> Dictionary:
	if current_state != CombatState.IN_COMBAT:
		return {"success": false, "message": "不在战斗中"}
	
	var damage: int = GameState.calculate_damage(current_enemy.get("defense", 0))
	enemy_health = maxi(enemy_health - damage, 0)
	
	turn_completed.emit("player", "enemy", damage)
	damage_dealt.emit("enemy", damage)
	health_updated.emit("enemy", enemy_health, enemy_max_health)
	
	if enemy_health <= 0:
		return _handle_victory()
	
	# 敌人反击
	var enemy_damage: int = _calculate_enemy_damage()
	var actual_damage: int = GameState.take_damage(enemy_damage)
	
	turn_completed.emit("enemy", "player", actual_damage)
	damage_dealt.emit("player", actual_damage)
	health_updated.emit("player", GameState.player_health, GameState.player_max_health)
	
	if not GameState.is_alive:
		return _handle_defeat()
	
	return {
		"success": true,
		"player_damage": damage,
		"enemy_damage": actual_damage,
		"player_health": GameState.player_health,
		"enemy_health": enemy_health
	}

func _calculate_enemy_damage() -> int:
	var enemy_attack: int = current_enemy.get("attack", 5)
	return maxi(enemy_attack - GameState.player_defense, 1)

func _handle_victory() -> Dictionary:
	current_state = CombatState.VICTORY
	
	var exp_reward: int = current_enemy.get("exp_reward", 10)
	GameState.add_exp(exp_reward)
	
	enemy_defeated.emit(current_enemy.get("enemy_type", "unknown"))
	combat_ended.emit("victory", exp_reward)
	
	var enemy_type: String = current_enemy.get("enemy_type", "unknown")
	current_enemy.clear()
	enemy_health = 0
	
	return {
		"success": true,
		"result": "victory",
		"exp_gained": exp_reward,
		"message": "战斗胜利！获得 %d 经验值" % exp_reward
	}

func _handle_defeat() -> Dictionary:
	current_state = CombatState.DEFEAT
	
	# 战斗失败，恢复血量
	GameState.reset_health()
	
	combat_ended.emit("defeat", 0)
	
	current_enemy.clear()
	enemy_health = 0
	
	return {
		"success": true,
		"result": "defeat",
		"exp_gained": 0,
		"message": "战斗失败，血量已恢复"
	}

func can_flee() -> bool:
	return current_state == CombatState.IN_COMBAT

func attempt_flee() -> Dictionary:
	if not can_flee():
		return {"success": false, "message": "无法逃跑"}
	
	# 逃跑成功率 50%
	var flee_success: bool = randf() > 0.5
	
	if flee_success:
		current_state = CombatState.IDLE
		current_enemy.clear()
		enemy_health = 0
		combat_ended.emit("fled", 0)
		return {"success": true, "message": "成功逃跑"}
	else:
		# 逃跑失败，敌人反击
		var enemy_damage: int = _calculate_enemy_damage()
		var actual_damage: int = GameState.take_damage(enemy_damage)
		
		damage_dealt.emit("player", actual_damage)
		health_updated.emit("player", GameState.player_health, GameState.player_max_health)
		
		if not GameState.is_alive:
			return _handle_defeat()
		
		return {
			"success": false,
			"message": "逃跑失败",
			"damage": actual_damage
		}

func end_combat() -> void:
	current_state = CombatState.IDLE
	current_enemy.clear()
	enemy_health = 0

func get_combat_state_name() -> String:
	match current_state:
		CombatState.IDLE:
			return "idle"
		CombatState.IN_COMBAT:
			return "in_combat"
		CombatState.VICTORY:
			return "victory"
		CombatState.DEFEAT:
			return "defeat"
	return "unknown"

func is_in_combat() -> bool:
	return current_state == CombatState.IN_COMBAT

func get_enemy_health_percent() -> float:
	if enemy_max_health <= 0:
		return 0.0
	return float(enemy_health) / float(enemy_max_health)

func get_enemy_name() -> String:
	return current_enemy.get("name", "未知敌人")

func get_enemy_level() -> int:
	return current_enemy.get("level", 1)