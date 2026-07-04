extends Node
## 主入口场景脚本
## 负责游戏初始化、场景切换、全局事件绑定

const MAIN_MENU_SCENE: PackedScene = preload("res://scenes/ui/main_menu/MainMenu.tscn")

var current_scene: Node = null

func _ready() -> void:
	_initialize_managers()
	_show_main_menu()

func _initialize_managers() -> void:
	pass

func _show_main_menu() -> void:
	_switch_scene(MAIN_MENU_SCENE)

func _switch_scene(new_scene: PackedScene) -> void:
	if current_scene and is_instance_valid(current_scene):
		current_scene.queue_free()
	
	current_scene = new_scene.instantiate()
	add_child(current_scene)

func quit_game() -> void:
	get_tree().quit()
