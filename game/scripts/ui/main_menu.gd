extends Control
## 主菜单场景脚本

signal start_game_pressed
signal settings_pressed
signal quit_pressed

@onready var start_button: Button = $CenterContainer/VBoxContainer/StartButton
@onready var settings_button: Button = $CenterContainer/VBoxContainer/SettingsButton
@onready var quit_button: Button = $CenterContainer/VBoxContainer/QuitButton
@onready var title_label: Label = $CenterContainer/VBoxContainer/TitleLabel

func _ready() -> void:
	start_button.pressed.connect(_on_start_pressed)
	settings_button.pressed.connect(_on_settings_pressed)
	quit_button.pressed.connect(_on_quit_pressed)
	title_label.text = "开放世界投票游戏"
	start_button.text = "开始游戏"
	settings_button.text = "设置"
	quit_button.text = "退出游戏"

func _on_start_pressed() -> void:
	start_game_pressed.emit()

func _on_settings_pressed() -> void:
	settings_pressed.emit()

func _on_quit_pressed() -> void:
	quit_pressed.emit()
	get_tree().quit()
