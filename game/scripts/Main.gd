extends Node
## 主入口场景脚本
## 负责游戏初始化、场景切换、全局事件绑定

const MAIN_MENU_SCENE: PackedScene = preload("res://scenes/ui/main_menu/MainMenu.tscn")
const WORLD_MAP_SCENE: PackedScene = preload("res://scenes/world/WorldMap.tscn")
const VOTING_PANEL_SCENE: PackedScene = preload("res://scenes/ui/voting/VotingPanel.tscn")
const VOTE_RESULT_SCENE: PackedScene = preload("res://scenes/ui/voting/VoteResultPanel.tscn")
const VOTE_HISTORY_SCENE: PackedScene = preload("res://scenes/ui/voting/VoteHistoryPanel.tscn")

var current_scene: Node = null

func _ready() -> void:
	_initialize_managers()
	_setup_global_signals()
	_show_main_menu()

func _initialize_managers() -> void:
	pass

func _setup_global_signals() -> void:
	pass

func _show_main_menu() -> void:
	_switch_scene(MAIN_MENU_SCENE, true)

func _switch_scene(new_scene: PackedScene, connect_signals: bool = false) -> Node:
	if current_scene and is_instance_valid(current_scene):
		current_scene.queue_free()
	
	var scene_node: Node = new_scene.instantiate()
	current_scene = scene_node
	add_child(scene_node)
	
	if connect_signals:
		_connect_scene_signals(scene_node)
	
	return scene_node

func _connect_scene_signals(scene_node: Node) -> void:
	if scene_node.has_signal("start_game_pressed"):
		scene_node.start_game_pressed.connect(_on_start_game_pressed)
	if scene_node.has_signal("vote_pressed"):
		scene_node.vote_pressed.connect(_on_vote_pressed)
	if scene_node.has_signal("world_map_pressed"):
		scene_node.world_map_pressed.connect(_on_world_map_pressed)
	if scene_node.has_signal("back_pressed"):
		scene_node.back_pressed.connect(_on_back_pressed)
	if scene_node.has_signal("quit_pressed"):
		scene_node.quit_pressed.connect(quit_game)

func _on_start_game_pressed() -> void:
	_switch_scene(WORLD_MAP_SCENE)

func _on_vote_pressed() -> void:
	_switch_scene(VOTING_PANEL_SCENE, true)
	VoteManager.fetch_current_vote()

func _on_world_map_pressed() -> void:
	_switch_scene(WORLD_MAP_SCENE)

func _on_back_pressed() -> void:
	_show_main_menu()

func quit_game() -> void:
	get_tree().quit()
