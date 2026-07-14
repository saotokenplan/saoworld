extends Node
## CombatHUD GUT 测试
## 覆盖战斗 HUD 信号、状态管理、胜利/失败/隐藏方法

var combat_hud_script: GDScript

func before_all() -> void:
	combat_hud_script = load("res://scripts/ui/combat_hud.gd")

func test_signals_declared() -> void:
	assert_true(combat_hud_script.has_signal("attack_pressed"), "should have attack_pressed signal")
	assert_true(combat_hud_script.has_signal("flee_pressed"), "should have flee_pressed signal")

func test_is_in_combat_initial_false() -> void:
	var instance: Control = combat_hud_script.new()
	assert_false(instance.is_in_combat, "is_in_combat should be false initially")
	instance.queue_free()

func test_is_in_combat_set_true() -> void:
	var instance: Control = combat_hud_script.new()
	instance.is_in_combat = true
	assert_true(instance.is_in_combat, "is_in_combat should be true after setting")
	instance.queue_free()

func test_hide_hud() -> void:
	var instance: Control = combat_hud_script.new()
	instance.hide_hud()
	assert_false(instance.visible, "HUD should be hidden after hide_hud")
	instance.queue_free()

func test_show_victory_method_exists() -> void:
	# 验证 show_victory 方法定义存在
	var instance: Control = combat_hud_script.new()
	assert_true(instance.has_method("show_victory"), "should have show_victory method")
	instance.queue_free()

func test_show_defeat_method_exists() -> void:
	var instance: Control = combat_hud_script.new()
	assert_true(instance.has_method("show_defeat"), "should have show_defeat method")
	instance.queue_free()

func test_hide_hud_method_exists() -> void:
	var instance: Control = combat_hud_script.new()
	assert_true(instance.has_method("hide_hud"), "should have hide_hud method")
	instance.queue_free()


## ==================== Boss 战相关测试 ====================

func test_boss_phase_display_methods_exist() -> void:
	# Boss 阶段显示方法
	var instance: Control = combat_hud_script.new()
	assert_true(instance.has_method("update_phase_display"), "should have update_phase_display method")
	instance.queue_free()

func test_boss_enrage_display_methods_exist() -> void:
	# 狂暴状态显示方法
	var instance: Control = combat_hud_script.new()
	assert_true(instance.has_method("show_enrage_indicator"), "should have show_enrage_indicator method")
	assert_true(instance.has_method("hide_enrage_indicator"), "should have hide_enrage_indicator method")
	instance.queue_free()

func test_boss_skill_display_methods_exist() -> void:
	# Boss 技能提示方法
	var instance: Control = combat_hud_script.new()
	assert_true(instance.has_method("show_boss_skill_alert"), "should have show_boss_skill_alert method")
	instance.queue_free()

func test_boss_phase_info_storage() -> void:
	# Boss 阶段信息存储
	var instance: Control = combat_hud_script.new()
	if instance.has_method("set_boss_phase_info"):
		instance.set_boss_phase_info(2, 3, "狂暴阶段")
		assert_eq(instance.current_phase, 2, "current_phase should be 2")
		assert_eq(instance.total_phases, 3, "total_phases should be 3")
	instance.queue_free()
