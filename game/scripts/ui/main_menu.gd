extends Control

signal start_game_pressed
signal continue_game_pressed
signal new_game_pressed
signal save_pressed
signal load_pressed
signal settings_pressed
signal quit_pressed
signal vote_pressed
signal world_map_pressed
signal npcs_pressed
signal quests_pressed

@onready var start_button: Button = $CenterContainer/VBoxContainer/StartButton
@onready var continue_button: Button = $CenterContainer/VBoxContainer/ContinueButton
@onready var new_game_button: Button = $CenterContainer/VBoxContainer/NewGameButton
@onready var save_button: Button = $CenterContainer/VBoxContainer/SaveButton
@onready var load_button: Button = $CenterContainer/VBoxContainer/LoadButton
@onready var settings_button: Button = $CenterContainer/VBoxContainer/SettingsButton
@onready var quit_button: Button = $CenterContainer/VBoxContainer/QuitButton
@onready var vote_button: Button = $CenterContainer/VBoxContainer/VoteButton
@onready var world_map_button: Button = $CenterContainer/VBoxContainer/WorldMapButton
@onready var npc_button: Button = $CenterContainer/VBoxContainer/NPCButton
@onready var quest_button: Button = $CenterContainer/VBoxContainer/QuestButton
@onready var title_label: Label = $CenterContainer/VBoxContainer/TitleLabel

func _ready() -> void:
	start_button.pressed.connect(_on_start_pressed)
	continue_button.pressed.connect(_on_continue_pressed)
	new_game_button.pressed.connect(_on_new_game_pressed)
	save_button.pressed.connect(_on_save_pressed)
	load_button.pressed.connect(_on_load_pressed)
	settings_button.pressed.connect(_on_settings_pressed)
	quit_button.pressed.connect(_on_quit_pressed)
	vote_button.pressed.connect(_on_vote_pressed)
	world_map_button.pressed.connect(_on_world_map_pressed)
	npc_button.pressed.connect(_on_npcs_pressed)
	quest_button.pressed.connect(_on_quests_pressed)
	
	title_label.text = "开放世界投票游戏"
	continue_button.text = "继续游戏"
	new_game_button.text = "新游戏"
	save_button.text = "保存"
	load_button.text = "加载"
	settings_button.text = "设置"
	quit_button.text = "退出游戏"
	vote_button.text = "参与投票"
	world_map_button.text = "世界地图"
	npc_button.text = "NPC 列表"
	quest_button.text = "任务列表"

func set_save_state(has_save: bool) -> void:
	start_button.visible = false
	continue_button.visible = has_save
	new_game_button.visible = true
	save_button.visible = has_save
	load_button.visible = has_save

func _on_start_pressed() -> void:
	start_game_pressed.emit()

func _on_continue_pressed() -> void:
	continue_game_pressed.emit()

func _on_new_game_pressed() -> void:
	new_game_pressed.emit()

func _on_save_pressed() -> void:
	save_pressed.emit()

func _on_load_pressed() -> void:
	load_pressed.emit()

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
