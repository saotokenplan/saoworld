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
