extends Area2D
## 敌人实体
## 负责敌人显示、碰撞检测、战斗触发

signal enemy_interacted(enemy_type: String)
signal combat_triggered(enemy_type: String)

@export var enemy_type: String = "wolf"
@export var patrol_range: float = 100.0

var enemy_data: Dictionary = {}
var is_active: bool = true

@onready var sprite: ColorRect = $Sprite
@onready var collision_shape: CollisionShape2D = $CollisionShape2D
@onready var interaction_label: Label = $InteractionLabel

func _ready() -> void:
	_load_enemy_data()
	_setup_visual()
	_setup_signals()
	
	if interaction_label:
		interaction_label.visible = false

func _load_enemy_data() -> void:
	var file: FileAccess = FileAccess.open("res://data/enemies/enemy_list.json", FileAccess.READ)
	if not file:
		return
	
	var content: String = file.get_as_text()
	file.close()
	
	var data: Dictionary = JSON.parse_string(content)
	if not data is Dictionary:
		return
	
	if data.has("enemies"):
		for enemy in data["enemies"]:
			if enemy.get("enemy_type", "") == enemy_type:
				enemy_data = enemy
				break

func _setup_visual() -> void:
	if not is_instance_valid(sprite):
		return
	
	if enemy_data.is_empty():
		sprite.color = Color.RED
		return
	
	var color_str: String = enemy_data.get("color", "#FF0000")
	sprite.color = Color(color_str)

func _setup_signals() -> void:
	body_entered.connect(_on_body_entered)
	body_exited.connect(_on_body_exited)

func _on_body_entered(body: Node2D) -> void:
	if not is_active:
		return
	
	if body.is_in_group("player"):
		if interaction_label:
			interaction_label.visible = true
		enemy_interacted.emit(enemy_type)

func _on_body_exited(body: Node2D) -> void:
	if body.is_in_group("player"):
		if interaction_label:
			interaction_label.visible = false

func trigger_combat() -> void:
	if not is_active:
		return
	
	is_active = false
	
	if CombatManager.start_combat(enemy_type):
		combat_triggered.emit(enemy_type)

func get_enemy_name() -> String:
	return enemy_data.get("name", "未知敌人")

func get_enemy_level() -> int:
	return enemy_data.get("level", 1)

func reset() -> void:
	is_active = true

func disable() -> void:
	is_active = false
	visible = false

func enable() -> void:
	is_active = true
	visible = true