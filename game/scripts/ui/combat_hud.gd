extends Control
## 战斗 HUD
## 显示玩家和敌人血条、战斗状态、伤害数字
## 支持Boss战阶段进度、技能提示、狂暴状态

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
@onready var phase_panel: Panel = $PhasePanel
@onready var phase_progress: ProgressBar = $PhasePanel/PhaseProgress
@onready var phase_label: Label = $PhasePanel/PhaseLabel
@onready var skill_alert_label: Label = $SkillAlertLabel
@onready var enrage_indicator: TextureRect = $EnrageIndicator
@onready var boss_banner: Panel = $BossBanner
@onready var boss_title_label: Label = $BossBanner/BossTitleLabel

var is_in_combat: bool = false
var current_phase: int = 1
var total_phases: int = 1

func _ready() -> void:
	visible = false
	_setup_signals()
	_setup_buttons()
	_hide_boss_elements()

func _setup_signals() -> void:
	CombatManager.combat_started.connect(_on_combat_started)
	CombatManager.combat_ended.connect(_on_combat_ended)
	CombatManager.health_updated.connect(_on_health_updated)
	CombatManager.turn_completed.connect(_on_turn_completed)
	CombatManager.phase_changed.connect(_on_phase_changed)
	CombatManager.enrage_activated.connect(_on_enrage_activated)
	CombatManager.boss_skill_used.connect(_on_boss_skill_used)

func _hide_boss_elements() -> void:
	if phase_panel:
		phase_panel.visible = false
	if skill_alert_label:
		skill_alert_label.visible = false
	if enrage_indicator:
		enrage_indicator.visible = false
	if boss_banner:
		boss_banner.visible = false

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
	
	if CombatManager.is_boss_combat:
		_show_boss_elements()
		_update_phase_display(1, CombatManager.total_phases, "第一阶段")
	else:
		_hide_boss_elements()
	
	_show_combat_status("战斗开始！")
	_set_buttons_enabled(true)
	
	if result_panel:
		result_panel.visible = false

func _show_boss_elements() -> void:
	if phase_panel:
		phase_panel.visible = true
	if boss_banner:
		boss_banner.visible = true
	
	if boss_title_label:
		var boss_rank: String = CombatManager.current_enemy.get("boss_rank", "legendary")
		var rank_text: String = match boss_rank:
			"legendary": "传说级 Boss"
			"mythic": "神话级 Boss"
			_: "Boss"
		boss_title_label.text = rank_text
	
	if flee_button:
		flee_button.disabled = true
		flee_button.visible = false

func _on_combat_ended(result: String, exp_gained: int) -> void:
	is_in_combat = false
	_set_buttons_enabled(false)
	_hide_boss_elements()
	
	if result_panel and result_label and exp_label:
		result_panel.visible = true
		
		match result:
			"victory":
				if CombatManager.is_boss_combat:
					result_label.text = "Boss战胜利！"
				else:
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

func _on_phase_changed(current_phase: int, total_phases: int, phase_name: String) -> void:
	_update_phase_display(current_phase, total_phases, phase_name)
	_show_combat_status("阶段变化！进入 %s" % phase_name)
	
	if combat_status_label:
		combat_status_label.add_theme_color_override("font_color", Color.ORANGE)
		await get_tree().create_timer(1.0).timeout
		combat_status_label.remove_theme_color_override("font_color")

func _on_enrage_activated() -> void:
	if enrage_indicator:
		enrage_indicator.visible = true
	
	_show_combat_status("警告！Boss进入狂暴状态！")
	
	if combat_status_label:
		combat_status_label.add_theme_color_override("font_color", Color.RED)
		await get_tree().create_timer(2.0).timeout
		combat_status_label.remove_theme_color_override("font_color")

func _on_boss_skill_used(skill_name: String, skill_description: String) -> void:
	if skill_alert_label:
		skill_alert_label.visible = true
		skill_alert_label.text = "Boss使用技能: %s" % skill_name
	
	_show_combat_status("Boss使用技能: %s" % skill_name)
	
	await get_tree().create_timer(1.5).timeout
	
	if skill_alert_label:
		skill_alert_label.visible = false

func _update_phase_display(current_phase: int, total_phases: int, phase_name: String) -> void:
	if phase_progress:
		phase_progress.max_value = total_phases
		phase_progress.value = current_phase
	
	if phase_label:
		phase_label.text = "%s (%d/%d)" % [phase_name, current_phase, total_phases]

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


## ==================== Boss 战辅助方法 ====================

func show_enrage_indicator() -> void:
	"""显示狂暴状态指示器"""
	if enrage_indicator:
		enrage_indicator.visible = true

func hide_enrage_indicator() -> void:
	"""隐藏狂暴状态指示器"""
	if enrage_indicator:
		enrage_indicator.visible = false

func show_boss_skill_alert(skill_name: String) -> void:
	"""显示 Boss 技能提示"""
	if skill_alert_label:
		skill_alert_label.visible = true
		skill_alert_label.text = "Boss使用技能: %s" % skill_name

		await get_tree().create_timer(1.5).timeout

		if skill_alert_label:
			skill_alert_label.visible = false

func set_boss_phase_info(current_phase: int, total_phases: int, phase_name: String) -> void:
	"""设置 Boss 阶段信息（用于测试）"""
	current_phase = current_phase
	total_phases = total_phases
	_update_phase_display(current_phase, total_phases, phase_name)