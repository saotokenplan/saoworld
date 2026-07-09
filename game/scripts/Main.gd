extends Node

const MAIN_MENU_SCENE: PackedScene = preload("res://scenes/ui/main_menu/MainMenu.tscn")
const WORLD_MAP_SCENE: PackedScene = preload("res://scenes/world/WorldMap.tscn")
const CORE_REGION_SCENE: PackedScene = preload("res://scenes/world/CoreRegion.tscn")
const VOTING_PANEL_SCENE: PackedScene = preload("res://scenes/ui/voting/VotingPanel.tscn")
const VOTE_RESULT_SCENE: PackedScene = preload("res://scenes/ui/voting/VoteResultPanel.tscn")
const VOTE_HISTORY_SCENE: PackedScene = preload("res://scenes/ui/voting/VoteHistoryPanel.tscn")
const NPC_PANEL_SCENE: PackedScene = preload("res://scenes/ui/npc/NPCPanel.tscn")
const QUEST_PANEL_SCENE: PackedScene = preload("res://scenes/ui/quests/QuestPanel.tscn")

var current_scene: Node = null

func _ready() -> void:
	_initialize_managers()
	_setup_global_signals()
	_setup_save_triggers()
	_show_main_menu()

func _initialize_managers() -> void:
	pass

func _setup_global_signals() -> void:
	pass

func _setup_save_triggers() -> void:
	# 连接自动保存触发信号
	PlayerManager.quest_accepted.connect(_on_quest_updated)
	PlayerManager.quest_completed.connect(_on_quest_updated)
	PlayerManager.quest_failed.connect(_on_quest_updated)
	PlayerManager.quest_progress_updated.connect(_on_quest_updated)
	
	# 连接 SaveManager 信号
	SaveManager.save_completed.connect(_on_save_completed)
	SaveManager.load_completed.connect(_on_load_completed)
	SaveManager.save_failed.connect(_on_save_failed)
	SaveManager.load_failed.connect(_on_load_failed)

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
	if scene_node.has_signal("npcs_pressed"):
		scene_node.npcs_pressed.connect(_on_npcs_pressed)
	if scene_node.has_signal("quests_pressed"):
		scene_node.quests_pressed.connect(_on_quests_pressed)
	if scene_node.has_signal("back_to_menu"):
		scene_node.back_to_menu.connect(_on_back_to_menu)
	if scene_node.has_signal("enter_region_requested"):
		scene_node.enter_region_requested.connect(_on_enter_region_requested)
	if scene_node.has_signal("back_to_world_map"):
		scene_node.back_to_world_map.connect(_on_world_map_pressed)

func _on_start_game_pressed() -> void:
	_switch_scene(WORLD_MAP_SCENE)

func _on_vote_pressed() -> void:
	_switch_scene(VOTING_PANEL_SCENE, true)
	VoteManager.fetch_current_vote()

func _on_world_map_pressed() -> void:
	_switch_scene(WORLD_MAP_SCENE)

func _on_enter_region_requested(region_id: String) -> void:
	var region_scene: Node = _switch_scene(CORE_REGION_SCENE, true)
	if region_scene and region_scene.has_method("set_region_data"):
		var region_data: Dictionary = _find_region_data(region_id)
		region_scene.set_region_data(region_data)

func _find_region_data(region_id: String) -> Dictionary:
	var file: FileAccess = FileAccess.open("res://data/regions/region_list.json", FileAccess.READ)
	if not file:
		return {}
	
	var content: String = file.get_as_text()
	file.close()
	
	var data: Dictionary = JSON.parse_string(content)
	if not data is Dictionary:
		return {}
	
	var regions: Array = data.get("regions", [])
	for region in regions:
		if region is Dictionary and region.get("region_id", "") == region_id:
			return region
	
	return {}

func _on_npcs_pressed() -> void:
	_switch_scene(NPC_PANEL_SCENE, true)

func _on_quests_pressed() -> void:
	_switch_scene(QUEST_PANEL_SCENE, true)

func _on_back_pressed() -> void:
	_show_main_menu()

func _on_back_to_menu() -> void:
	# 返回主菜单前自动保存
	SaveManager.save_game("auto")
	_show_main_menu()

func quit_game() -> void:
	# 退出前自动保存
	SaveManager.save_game("exit_backup")
	get_tree().quit()

# 存档系统回调
func _on_quest_updated(_quest_id: String) -> void:
	# 任务状态更新时自动保存
	SaveManager.save_game("auto")

func _on_save_completed(save_id: String) -> void:
	print("[Main] 存档完成: %s" % save_id)

func _on_load_completed(save_id: String) -> void:
	print("[Main] 存档加载完成: %s" % save_id)

func _on_save_failed(error_message: String) -> void:
	push_error("[Main] 存档失败: %s" % error_message)

func _on_load_failed(error_message: String) -> void:
	push_error("[Main] 加载失败: %s" % error_message)
