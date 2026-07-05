extends Control

signal start_game_pressed
signal settings_pressed
signal quit_pressed
signal vote_pressed
signal world_map_pressed
signal npcs_pressed
signal quests_pressed

@onready var start_button: Button = $CenterContainer/VBoxContainer/StartButton
@onready var settings_button: Button = $CenterContainer/VBoxContainer/SettingsButton
@onready var quit_button: Button = $CenterContainer/VBoxContainer/QuitButton
@onready var vote_button: Button = $CenterContainer/VBoxContainer/VoteButton
@onready var world_map_button: Button = $CenterContainer/VBoxContainer/WorldMapButton
@onready var npc_button: Button = $CenterContainer/VBoxContainer/NPCButton
@onready var quest_button: Button = $CenterContainer/VBoxContainer/QuestButton
@onready var title_label: Label = $CenterContainer/VBoxContainer/TitleLabel

func _ready() -> void:
	start_button.pressed.connect(_on_start_pressed)
	settings_button.pressed.connect(_on_settings_pressed)
	quit_button.pressed.connect(_on_quit_pressed)
	vote_button.pressed.connect(_on_vote_pressed)
	world_map_button.pressed.connect(_on_world_map_pressed)
	npc_button.pressed.connect(_on_npcs_pressed)
	quest_button.pressed.connect(_on_quests_pressed)
	title_label.text = "开放世界投票游戏"
	start_button.text = "开始游戏"
	settings_button.text = "设置"
	quit_button.text = "退出游戏"
	vote_button.text = "参与投票"
	world_map_button.text = "世界地图"
	npc_button.text = "NPC 列表"
	quest_button.text = "任务列表"

func _on_start_pressed() -> void:
	start_game_pressed.emit()

func _on_settings_pressed() -> void:
	settings_pressed.emit()

func _on_quit_pressed() -> void:
	quit_pressed.emit()
	get_tree().quit()

func _on_vote_pressed() -> void:
	vote_pressed.emit()

func _on_world_map_pressed() -> void:
	world_map_pressed.emit()

func _on_npcs_pressed() -> void:
	npcs_pressed.emit()

func _on_quests_pressed() -> void:
	quests_pressed.emit()
