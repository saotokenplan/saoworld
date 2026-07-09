extends CharacterBody2D

signal movement_state_changed(state: String)

const DEFAULT_SPEED: float = 200.0
const DEFAULT_ACCELERATION: float = 1200.0
const DEFAULT_FRICTION: float = 1200.0
const CONFIG_PATH: String = "res://data/config/input_config.json"

@export var speed: float = DEFAULT_SPEED
@export var acceleration: float = DEFAULT_ACCELERATION
@export var friction: float = DEFAULT_FRICTION

var current_state: String = "idle"
var facing_direction: Vector2 = Vector2.DOWN

@onready var sprite: ColorRect = $Sprite
@onready var collision: CollisionShape2D = $CollisionShape2D

func _ready() -> void:
	_load_movement_config()

func _physics_process(delta: float) -> void:
	var input_direction: Vector2 = _get_input_direction()
	
	if input_direction.length_squared() > 0.01:
		velocity = velocity.move_toward(input_direction * speed, acceleration * delta)
		facing_direction = input_direction.normalized()
		_set_state("move")
	else:
		velocity = velocity.move_toward(Vector2.ZERO, friction * delta)
		_set_state("idle")
	
	move_and_slide()

func _get_input_direction() -> Vector2:
	var direction: Vector2 = Vector2.ZERO
	
	if Input.is_action_pressed("move_left"):
		direction.x -= 1.0
	if Input.is_action_pressed("move_right"):
		direction.x += 1.0
	if Input.is_action_pressed("move_up"):
		direction.y -= 1.0
	if Input.is_action_pressed("move_down"):
		direction.y += 1.0
	
	return direction.normalized()

func _set_state(new_state: String) -> void:
	if new_state == current_state:
		return
	
	current_state = new_state
	_update_sprite_visual()
	movement_state_changed.emit(current_state)

func _update_sprite_visual() -> void:
	if not is_instance_valid(sprite):
		return
	
	match current_state:
		"move":
			sprite.color = Color(0.3, 0.7, 1.0)
		"idle":
			sprite.color = Color(0.2, 0.5, 0.9)

func _load_movement_config() -> void:
	var file: FileAccess = FileAccess.open(CONFIG_PATH, FileAccess.READ)
	if not file:
		return
	
	var content: String = file.get_as_text()
	file.close()
	
	var data: Dictionary = JSON.parse_string(content)
	if not data is Dictionary:
		return
	
	var movement_config: Dictionary = data.get("player_movement", {})
	if movement_config.has("speed"):
		speed = float(movement_config.get("speed", DEFAULT_SPEED))
	if movement_config.has("acceleration"):
		acceleration = float(movement_config.get("acceleration", DEFAULT_ACCELERATION))
	if movement_config.has("friction"):
		friction = float(movement_config.get("friction", DEFAULT_FRICTION))

func reset_state() -> void:
	velocity = Vector2.ZERO
	current_state = "idle"
	facing_direction = Vector2.DOWN
	_update_sprite_visual()
