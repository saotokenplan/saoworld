extends Control
## 战斗 HUD
## 显示玩家和敌人血条、战斗状态、伤害数字

signal attack_pressed
signal flee_pressed

@onready var player_health_bar: ProgressBar = $PlayerHealthBar
@onready var player_health_label: Label = $PlayerHealthBar/HealthLabel
@onready var enemy_health_bar: ProgressBar = $ProgressBar
@onready var enemy_health_label: Label = $ProgressBar/EnemyHealthLabel
@onready var enemy_name_label: Label = $EnemyNameLabel
@onready var combat_status_label: Label = $CombatStatusLabel
@onready var attack_button: Button = $AttackButton
@onready var flee_button: Button = $FleeButton
@onready var result_panel: Panel = $ResultPanel
@onready var result_label: Label = $ResultPanel/ResultLabel
@onready var exp_label: Label = $ResultPanel/ExpLabel

var is_in_combat: bool = false

func _ready() -> void:
	visible = false
	_setup_signals()
	_setup_buttons()

func _setup_signals() -> void:
	CombatManager.combat_started.connect(_on_combat_started)
	CombatManager.combat_ended.connect(_on_combat_ended)
	CombatManager.health_updated.connect(_on_health_updated)
	CombatManager.turn_completed.connect(_on_turn_completed)

func _setup_buttons() -> void:
	if attack_button:
		attack_button.pressed.connect(_on_attack_button_pressed)
	if flee_button:
		flee_button.pressed.connect(_on_flee_button_pressed)

func _on_combat_started(enemy_type: String) -> void:
	is_in_combat = true
	visible = true
	
	var enemy_data: Dictionary = CombatManager.current_enemy
	if enemy_name_label and not enemy_data.is_empty():
		enemy_name_label.text = enemy_data.get("name", "未知敌人")
	
	_update_player_health(GameState.player_health, GameState.player_max_health)
	_update_enemy_health(CombatManager.enemy_health, CombatManager.enemy_max_health)
	
	_show_combat_status("战斗开始！")
	_set_buttons_enabled(true)
	
	if result_panel:
		result_panel.visible = false

func _on_combat_ended(result: String, exp_gained: int) -> void:
	is_in_combat = false
	_set_buttons_enabled(false)
	
	if result_panel and result_label and exp_label:
		result_panel.visible = true
		
		match result:
			"victory":
				result_label.text = "战斗胜利！"
				result_label.add_theme_color_override("font_color", Color.GREEN)
				exp_label.text = "获得经验: %d" % exp_gained
			"defeat":
				result_label.text = "战斗失败"
				result_label.add_theme_color_override("font_color", Color.RED)
				exp_label.text = "血量已恢复"
			"fled":
				result_label.text = "成功逃跑"
				result_label.add_theme_color_override("font_color", Color.YELLOW)
				exp_label.text = ""
		
		await get_tree().create_timer(2.0).timeout
		visible = false

func _on_health_updated(entity_type: String, current_health: int, max_health: int) -> void:
	match entity_type:
		"player":
			_update_player_health(current_health, max_health)
		"enemy":
			_update_enemy_health(current_health, max_health)

func _update_player_health(current: int, maximum: int) -> void:
	if player_health_bar:
		player_health_bar.max_value = maximum
		player_health_bar.value = current
	
	if player_health_label:
		player_health_label.text = "%d / %d" % [current, maximum]

func _update_enemy_health(current: int, maximum: int) -> void:
	if enemy_health_bar:
		enemy_health_bar.max_value = maximum
		enemy_health_bar.value = current
	
	if enemy_health_label:
		enemy_health_label.text = "%d / %d" % [current, maximum]

func _on_turn_completed(attacker: String, target: String, damage: int) -> void:
	var message: String = "%s 对 %s 造成 %d 点伤害" % [attacker, target, damage]
	_show_combat_status(message)

func _show_combat_status(message: String) -> void:
	if combat_status_label:
		combat_status_label.text = message

func _set_buttons_enabled(enabled: bool) -> void:
	if attack_button:
		attack_button.disabled = not enabled
	if flee_button:
		flee_button.disabled = not enabled

func _on_attack_button_pressed() -> void:
	if not is_in_combat:
		return
	
	attack_pressed.emit()
	
	var result: Dictionary = CombatManager.player_attack()
	if result.get("success", false) and result.has("message"):
		_show_combat_status(result.message)

func _on_flee_button_pressed() -> void:
	if not is_in_combat:
		return
	
	flee_pressed.emit()
	
	var result: Dictionary = CombatManager.attempt_flee()
	_show_combat_status(result.get("message", "逃跑失败"))

func show_victory(exp_gained: int) -> void:
	if result_panel and result_label and exp_label:
		result_panel.visible = true
		result_label.text = "战斗胜利！"
		result_label.add_theme_color_override("font_color", Color.GREEN)
		exp_label.text = "获得经验: %d" % exp_gained

func show_defeat() -> void:
	if result_panel and result_label and exp_label:
		result_panel.visible = true
		result_label.text = "战斗失败"
		result_label.add_theme_color_override("font_color", Color.RED)
		exp_label.text = "血量已恢复"

func hide_hud() -> void:
	visible = false