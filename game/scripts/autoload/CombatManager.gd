extends Node
## 战斗管理单例
## 负责管理战斗流程、伤害计算、胜负判定
## 支持Boss战阶段管理、特殊技能、狂暴状态

signal combat_started(enemy_type: String)
signal combat_ended(result: String, exp_gained: int)
signal turn_completed(attacker: String, target: String, damage: int)
signal health_updated(entity_type: String, current_health: int, max_health: int)
signal damage_dealt(target: String, damage: int)
signal enemy_defeated(enemy_type: String)
signal phase_changed(current_phase: int, total_phases: int, phase_name: String)
signal enrage_activated()
signal boss_skill_used(skill_name: String, skill_description: String)

enum CombatState { IDLE, IN_COMBAT, VICTORY, DEFEAT }

var current_state: CombatState = CombatState.IDLE
var current_enemy: Dictionary = {}
var enemy_health: int = 0
var enemy_max_health: int = 0
var current_phase: int = 1
var total_phases: int = 1
var enraged: bool = false
var enrage_activated: bool = false
var phase_health_thresholds: Array = []
var current_special_skills: Array = []
var boss_skill_cooldowns: Dictionary = {}
var is_boss_combat: bool = false

const ENEMY_DATA_PATH: String = "res://data/enemies/enemy_list.json"
const MONSTER_DATA_PATH: String = "res://data/monsters/monster_list.json"
var enemy_data: Dictionary = {}
var monster_data: Dictionary = {}

func _ready() -> void:
	_load_enemy_data()
	_load_monster_data()

func _load_enemy_data() -> void:
	var file: FileAccess = FileAccess.open(ENEMY_DATA_PATH, FileAccess.READ)
	if not file:
		return
	
	var content: String = file.get_as_text()
	file.close()
	
	var data: Dictionary = JSON.parse_string(content)
	if data is Dictionary:
		enemy_data = data

func _load_monster_data() -> void:
	var file: FileAccess = FileAccess.open(MONSTER_DATA_PATH, FileAccess.READ)
	if not file:
		return
	
	var content: String = file.get_as_text()
	file.close()
	
	var data: Dictionary = JSON.parse_string(content)
	if data is Dictionary:
		monster_data = data

func get_enemy_data(enemy_type: String) -> Dictionary:
	if enemy_data.has("enemies"):
		for enemy in enemy_data["enemies"]:
			if enemy.get("enemy_type", "") == enemy_type:
				return enemy
	return {}

func get_monster_data(monster_key: String) -> Dictionary:
	if monster_data.has("monsters"):
		for monster in monster_data["monsters"]:
			if monster.get("monster_key", "") == monster_key:
				return monster
	return {}

func start_boss_combat(monster_key: String) -> bool:
	if current_state != CombatState.IDLE:
		return false
	
	current_enemy = get_monster_data(monster_key)
	if current_enemy.is_empty() or not current_enemy.get("is_boss", false):
		return false
	
	is_boss_combat = true
	enemy_health = current_enemy.get("hp", 500)
	enemy_max_health = enemy_health
	total_phases = current_enemy.get("phase_count", 1)
	current_phase = 1
	enraged = false
	enrage_activated = false
	boss_skill_cooldowns.clear()
	
	_calculate_phase_thresholds()
	_update_current_special_skills()
	
	current_state = CombatState.IN_COMBAT
	combat_started.emit(monster_key)
	health_updated.emit("enemy", enemy_health, enemy_max_health)
	health_updated.emit("player", GameState.player_health, GameState.player_max_health)
	
	return true

func _calculate_phase_thresholds() -> void:
	phase_health_thresholds.clear()
	if total_phases <= 1:
		return
	
	var step: float = 1.0 / float(total_phases)
	for i in range(1, total_phases):
		phase_health_thresholds.append(1.0 - (step * float(i)))

func _update_current_special_skills() -> void:
	var all_skills: Array = current_enemy.get("special_skills", [])
	current_special_skills = []
	
	if all_skills.is_empty():
		return
	
	if total_phases == 1:
		current_special_skills = all_skills.duplicate()
	else:
		var skills_per_phase: int = maxi(1, all_skills.size() / total_phases)
		var start_idx: int = (current_phase - 1) * skills_per_phase
		var end_idx: int = start_idx + skills_per_phase
		
		for i in range(start_idx, min(end_idx, all_skills.size())):
			current_special_skills.append(all_skills[i])
	
	for skill in current_special_skills:
		if not boss_skill_cooldowns.has(skill.get("skill_key", "")):
			boss_skill_cooldowns[skill.get("skill_key", "")] = 0

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
	
	if is_boss_combat:
		_check_phase_transition()
		_check_enrage()
		_update_skill_cooldowns()
		return _boss_turn()
	else:
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
		"enemy_damage": GameState.player_max_health - GameState.player_health,
		"player_health": GameState.player_health,
		"enemy_health": enemy_health,
		"is_boss": is_boss_combat,
		"current_phase": current_phase,
		"total_phases": total_phases,
		"enraged": enraged
	}

func _calculate_enemy_damage() -> int:
	var enemy_attack: int = current_enemy.get("attack", 5)
	return maxi(enemy_attack - GameState.player_defense, 1)

func _check_phase_transition() -> void:
	if total_phases <= 1:
		return
	
	var health_percent: float = get_enemy_health_percent()
	
	for i in range(phase_health_thresholds.size()):
		var threshold: float = phase_health_thresholds[i]
		var new_phase: int = i + 2
		
		if health_percent <= threshold and current_phase < new_phase:
			current_phase = new_phase
			_update_current_special_skills()
			var phase_name: String = current_enemy.get("phase_names", []).get(current_phase - 1, "Phase %d" % current_phase)
			phase_changed.emit(current_phase, total_phases, phase_name)
			break

func _check_enrage() -> void:
	var enrage_threshold: float = current_enemy.get("enrage_threshold", 0.3)
	if get_enemy_health_percent() <= enrage_threshold and not enrage_activated:
		enraged = true
		enrage_activated = true
		enrage_activated.emit()

func _update_skill_cooldowns() -> void:
	for skill_key in boss_skill_cooldowns:
		if boss_skill_cooldowns[skill_key] > 0:
			boss_skill_cooldowns[skill_key] -= 1

func _boss_turn() -> Dictionary:
	var result: Dictionary = {}
	var total_damage: int = 0
	
	var use_special_skill: bool = randf() < 0.3 or enraged
	
	if use_special_skill and current_special_skills.size() > 0:
		var available_skills: Array = []
		for skill in current_special_skills:
			var skill_key: String = skill.get("skill_key", "")
			if boss_skill_cooldowns.get(skill_key, 0) <= 0:
				available_skills.append(skill)
		
		if available_skills.size() > 0:
			var selected_skill: Dictionary = available_skills[randi() % available_skills.size()]
			var skill_key: String = selected_skill.get("skill_key", "")
			boss_skill_cooldowns[skill_key] = selected_skill.get("cooldown", 5)
			
			var skill_damage: int = _calculate_boss_skill_damage(selected_skill)
			var actual_damage: int = GameState.take_damage(skill_damage)
			total_damage += actual_damage
			
			boss_skill_used.emit(selected_skill.get("name", ""), selected_skill.get("description", ""))
			turn_completed.emit("enemy", "player", actual_damage)
			damage_dealt.emit("player", actual_damage)
			health_updated.emit("player", GameState.player_health, GameState.player_max_health)
			
			if not GameState.is_alive:
				return _handle_defeat()
	
	var normal_damage: int = _calculate_boss_damage()
	var actual_normal_damage: int = GameState.take_damage(normal_damage)
	total_damage += actual_normal_damage
	
	turn_completed.emit("enemy", "player", actual_normal_damage)
	damage_dealt.emit("player", actual_normal_damage)
	health_updated.emit("player", GameState.player_health, GameState.player_max_health)
	
	if not GameState.is_alive:
		return _handle_defeat()
	
	return {
		"success": true,
		"player_damage": GameState.player_max_health - GameState.player_health,
		"enemy_damage": total_damage,
		"player_health": GameState.player_health,
		"enemy_health": enemy_health,
		"is_boss": true,
		"current_phase": current_phase,
		"total_phases": total_phases,
		"enraged": enraged
	}

func _calculate_boss_damage() -> int:
	var enemy_attack: int = current_enemy.get("attack", 30)
	var damage: int = maxi(enemy_attack - GameState.player_defense, 1)
	
	if enraged:
		damage = int(damage * 1.5)
	
	return damage

func _calculate_boss_skill_damage(skill: Dictionary) -> int:
	var base_damage: int = current_enemy.get("attack", 30)
	var multiplier: float = skill.get("damage_multiplier", 1.5)
	var damage: int = int(base_damage * multiplier)
	
	if enraged:
		damage = int(damage * 1.3)
	
	return damage

func _handle_victory() -> Dictionary:
	current_state = CombatState.VICTORY
	
	var exp_reward: int = current_enemy.get("exp_reward", 10)
	if is_boss_combat:
		var boss_reward: Dictionary = current_enemy.get("reward", {})
		exp_reward = boss_reward.get("experience", exp_reward)
		
		var reward_items: Array = boss_reward.get("items", [])
		for item in reward_items:
			var item_key: String = item.get("item_key", "")
			var quantity: int = item.get("quantity", 1)
			InventoryManager.add_item(item_key, quantity)
	
	GameState.add_exp(exp_reward)
	
	var enemy_key: String = current_enemy.get("enemy_type", current_enemy.get("monster_key", "unknown"))
	enemy_defeated.emit(enemy_key)
	combat_ended.emit("victory", exp_reward)
	
	var message: String = "战斗胜利！获得 %d 经验值" % exp_reward
	if is_boss_combat:
		message = "Boss战胜利！获得 %d 经验值和丰厚奖励！" % exp_reward
	
	var result: Dictionary = {
		"success": true,
		"result": "victory",
		"exp_gained": exp_reward,
		"message": message,
		"is_boss": is_boss_combat
	}
	
	_reset_combat_state()
	
	return result

func _handle_defeat() -> Dictionary:
	current_state = CombatState.DEFEAT
	
	GameState.reset_health()
	
	combat_ended.emit("defeat", 0)
	
	var result: Dictionary = {
		"success": true,
		"result": "defeat",
		"exp_gained": 0,
		"message": "战斗失败，血量已恢复",
		"is_boss": is_boss_combat
	}
	
	_reset_combat_state()
	
	return result

func _reset_combat_state() -> void:
	current_enemy.clear()
	enemy_health = 0
	enemy_max_health = 0
	current_phase = 1
	total_phases = 1
	enraged = false
	enrage_activated = false
	is_boss_combat = false
	phase_health_thresholds.clear()
	current_special_skills.clear()
	boss_skill_cooldowns.clear()

func can_flee() -> bool:
	return current_state == CombatState.IN_COMBAT

func attempt_flee() -> Dictionary:
	if not can_flee():
		return {"success": false, "message": "无法逃跑"}
	
	if is_boss_combat:
		return {"success": false, "message": "Boss战中无法逃跑"}
	
	var flee_success: bool = randf() > 0.5
	
	if flee_success:
		current_state = CombatState.IDLE
		_reset_combat_state()
		combat_ended.emit("fled", 0)
		return {"success": true, "message": "成功逃跑"}
	else:
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
	_reset_combat_state()

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