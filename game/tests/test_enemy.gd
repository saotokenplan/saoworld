extends GutTest
## Enemy 测试用例

var enemy: Area2D

func before_each() -> void:
	enemy = autofree(load("res://scenes/enemies/Enemy.tscn").instantiate())
	add_child(enemy)

func test_initial_state() -> void:
	assert_true(enemy.is_active, "敌人初始应激活")
	assert_eq(enemy.enemy_type, "wolf", "默认敌人类型应为 wolf")

func test_set_enemy_type() -> void:
	enemy.enemy_type = "bandit"
	assert_eq(enemy.enemy_type, "bandit", "敌人类型应可设置")

func test_trigger_combat_success() -> void:
	enemy.enemy_type = "wolf"
	enemy._ready()
	
	# 等待 CombatManager 加载
	await get_tree().process_frame
	
	var combat_started: bool = false
	enemy.combat_triggered.connect(func(_type: String): combat_started = true)
	enemy.trigger_combat()
	
	assert_true(combat_started, "触发战斗应发出信号")
	assert_false(enemy.is_active, "触发战斗后敌人应禁用")

func test_trigger_combat_disabled() -> void:
	enemy.is_active = false
	enemy.trigger_combat()
	
	assert_false(enemy.is_active, "禁用敌人无法触发战斗")

func test_disable_enable() -> void:
	enemy.disable()
	assert_false(enemy.is_active, "禁用后不激活")
	assert_false(enemy.visible, "禁用后不可见")
	
	enemy.enable()
	assert_true(enemy.is_active, "启用后激活")
	assert_true(enemy.visible, "启用后可见")

func test_reset() -> void:
	enemy.is_active = false
	enemy.reset()
	assert_true(enemy.is_active, "重置后应激活")

func test_get_enemy_name() -> void:
	enemy.enemy_type = "wolf"
	enemy._ready()
	await get_tree().process_frame
	
	var name: String = enemy.get_enemy_name()
	assert_eq(name, "野狼", "应返回敌人名称")

func test_get_enemy_level() -> void:
	enemy.enemy_type = "wolf"
	enemy._ready()
	await get_tree().process_frame
	
	var level: int = enemy.get_enemy_level()
	assert_eq(level, 1, "野狼等级应为1")