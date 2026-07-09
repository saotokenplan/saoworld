extends "res://addons/gut/test.gd"

func test_player_initial_state() -> void:
	var player: CharacterBody2D = load("res://scenes/player/Player.tscn").instantiate()
	assert_eq(player.current_state, "idle", "玩家初始状态应为 idle")
	assert_eq(player.velocity, Vector2.ZERO, "玩家初始速度应为零")
	assert_eq(player.facing_direction, Vector2.DOWN, "玩家初始朝向应为向下")
	player.queue_free()

func test_player_reset_state() -> void:
	var player: CharacterBody2D = load("res://scenes/player/Player.tscn").instantiate()
	player.velocity = Vector2(100, 100)
	player.current_state = "move"
	player.facing_direction = Vector2.RIGHT
	
	player.reset_state()
	
	assert_eq(player.current_state, "idle", "重置后状态应为 idle")
	assert_eq(player.velocity, Vector2.ZERO, "重置后速度应为零")
	assert_eq(player.facing_direction, Vector2.DOWN, "重置后朝向应为向下")
	player.queue_free()

func test_player_movement_state_signal() -> void:
	var player: CharacterBody2D = load("res://scenes/player/Player.tscn").instantiate()
	add_child_autofree(player)
	
	var signals_received: Array = []
	player.movement_state_changed.connect(func(state: String):
		signals_received.append(state)
	)
	
	player._set_state("move")
	assert_eq(signals_received.size(), 1, "状态变化时应发射信号")
	assert_eq(signals_received[0], "move", "信号参数应为新状态")
	
	player._set_state("move")
	assert_eq(signals_received.size(), 1, "相同状态不应重复发射信号")

func test_player_no_input_returns_zero_direction() -> void:
	var player: CharacterBody2D = load("res://scenes/player/Player.tscn").instantiate()
	add_child_autofree(player)
	
	var direction: Vector2 = player._get_input_direction()
	assert_eq(direction, Vector2.ZERO, "无输入时方向应为零向量")

func test_player_loads_config_values() -> void:
	var player: CharacterBody2D = load("res://scenes/player/Player.tscn").instantiate()
	add_child_autofree(player)
	
	assert_eq(player.speed, 200.0, "应从配置加载速度值 200.0")
	assert_eq(player.acceleration, 1200.0, "应从配置加载加速度值 1200.0")
	assert_eq(player.friction, 1200.0, "应从配置加载摩擦力值 1200.0")

# 战斗属性测试
func test_game_state_combat_attributes() -> void:
	GameState.reset_state()
	
	assert_eq(GameState.player_health, 100, "初始血量应为 100")
	assert_eq(GameState.player_max_health, 100, "最大血量应为 100")
	assert_eq(GameState.player_attack, 10, "初始攻击力应为 10")
	assert_eq(GameState.player_defense, 5, "初始防御力应为 5")
	assert_true(GameState.is_alive, "初始应存活")

func test_game_state_take_damage() -> void:
	GameState.reset_state()
	
	var damage: int = GameState.take_damage(10)
	assert_gt(damage, 0, "应造成伤害")
	assert_lt(GameState.player_health, 100, "血量应减少")

func test_game_state_take_damage_with_defense() -> void:
	GameState.reset_state()
	GameState.player_defense = 5
	
	var damage: int = GameState.take_damage(10)
	assert_eq(damage, 5, "伤害应减去防御值")
	assert_eq(GameState.player_health, 95, "血量应为 95")

func test_game_state_take_damage_minimum() -> void:
	GameState.reset_state()
	GameState.player_defense = 100
	
	var damage: int = GameState.take_damage(5)
	assert_eq(damage, 1, "最小伤害应为 1")

func test_game_state_heal() -> void:
	GameState.reset_state()
	GameState.player_health = 50
	
	GameState.heal(30)
	assert_eq(GameState.player_health, 80, "应恢复 30 点血量")

func test_game_state_heal_capped() -> void:
	GameState.reset_state()
	GameState.player_health = 90
	
	GameState.heal(30)
	assert_eq(GameState.player_health, 100, "血量不应超过最大值")

func test_game_state_reset_health() -> void:
	GameState.reset_state()
	GameState.player_health = 20
	GameState.is_alive = false
	
	GameState.reset_health()
	assert_eq(GameState.player_health, 100, "血量应恢复到最大值")
	assert_true(GameState.is_alive, "应复活")

func test_game_state_calculate_damage() -> void:
	GameState.reset_state()
	GameState.player_attack = 15
	
	var damage: int = GameState.calculate_damage(5)
	assert_eq(damage, 10, "伤害应为攻击力减去防御")

func test_game_state_calculate_damage_minimum() -> void:
	GameState.reset_state()
	GameState.player_attack = 3
	
	var damage: int = GameState.calculate_damage(10)
	assert_eq(damage, 1, "最小伤害应为 1")

func test_game_state_player_died_signal() -> void:
	GameState.reset_state()
	GameState.player_health = 5
	
	var died_signal: bool = false
	GameState.player_died.connect(func(): died_signal = true)
	
	GameState.take_damage(100)
	
	assert_true(died_signal, "死亡应发出 player_died 信号")
	assert_false(GameState.is_alive, "应标记为死亡")
