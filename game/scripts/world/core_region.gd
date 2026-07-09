extends Node2D

signal back_to_world_map()
signal region_entered(region_id: String)

const PLAYER_SCENE: PackedScene = preload("res://scenes/player/Player.tscn")

@export var region_id: String = "region_core_ironward"
@export var region_name: String = "铁卫城周边"
@export var player_start_position: Vector2 = Vector2(640, 360)

var player: CharacterBody2D = null

@onready var ground: ColorRect = $Ground
@onready var obstacles: Node2D = $Obstacles
@onready var boundaries: StaticBody2D = $Boundaries
@onready var back_button: Button = $BackButton
@onready var title_label: Label = $TitleLabel

func _ready() -> void:
	_setup_ui()
	_spawn_player()
	region_entered.emit(region_id)

func _setup_ui() -> void:
	if is_instance_valid(title_label):
		title_label.text = region_name
	
	if is_instance_valid(back_button):
		back_button.pressed.connect(_on_back_button_pressed)

func _spawn_player() -> void:
	player = PLAYER_SCENE.instantiate()
	player.position = player_start_position
	add_child(player)

func _on_back_button_pressed() -> void:
	back_to_world_map.emit()

func get_player() -> CharacterBody2D:
	return player

func set_region_data(data: Dictionary) -> void:
	region_id = data.get("region_id", region_id)
	region_name = data.get("name", region_name)
	
	if is_instance_valid(title_label):
		title_label.text = region_name
