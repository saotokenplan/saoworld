extends Node2D

signal back_to_world_map()
signal region_entered(region_id: String)
signal npc_interaction_started(npc_data: Dictionary)
signal combat_started(enemy_type: String)

const PLAYER_SCENE: PackedScene = preload("res://scenes/player/Player.tscn")
const ENEMY_SCENE: PackedScene = preload("res://scenes/npc/Enemy.tscn")

@export var region_id: String = "region_core_ironward"
@export var region_name: String = "铁卫城周边"
@export var player_start_position: Vector2 = Vector2(640, 360)

var player: CharacterBody2D = null
var npc_interactables: Array[Area2D] = []
var nearby_npc: Area2D = null
var interact_prompt: Label = null
var npc_dialog: PanelContainer = null
var quest_tracker: PanelContainer = null
var quest_panel: Control = null
var combat_hud: Control = null
var nearby_enemy: Area2D = null
var enemy_interact_prompt: Label = null

@onready var ground: ColorRect = $Ground
@onready var obstacles: Node2D = $Obstacles
@onready var boundaries: StaticBody2D = $Boundaries
@onready var back_button: Button = $BackButton
@onready var title_label: Label = $TitleLabel
@onready var npcs_node: Node2D = $NPCs

func _ready() -> void:
	_setup_ui()
	_spawn_player()
	_setup_interact_prompt()
	_load_region_npcs()
	_setup_quest_tracker()
	_setup_enemies()
	_setup_combat_signals()
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

func _setup_interact_prompt() -> void:
	interact_prompt = Label.new()
	interact_prompt.text = "按 E 对话"
	interact_prompt.visible = false
	interact_prompt.position = Vector2(0, -30)
	interact_prompt.z_index = 100
	var style_box: StyleBoxFlat = StyleBoxFlat.new()
	style_box.bg_color = Color(0.0, 0.0, 0.0, 0.7)
	style_box.set_content_margin_all(8)
	interact_prompt.add_theme_stylebox_override("normal", style_box)
	add_child(interact_prompt)

func _load_region_npcs() -> void:
	WorldManager.load_npcs_from_local()
	var region_npcs: Array[Dictionary] = WorldManager.get_npcs_by_region(_get_location_id())
	
	if region_npcs.size() == 0:
		region_npcs = WorldManager.npc_list
	
	var positions: Array[Vector2] = [
		Vector2(300, 200),
		Vector2(500, 250),
		Vector2(700, 300),
		Vector2(400, 400),
		Vector2(600, 450),
		Vector2(250, 350)
	]
	
	for i in range(mini(region_npcs.size(), positions.size())):
		var npc_data: Dictionary = region_npcs[i]
		_create_npc_interactable(npc_data, positions[i])

func _get_location_id() -> String:
	match region_id:
		"region_core_ironward":
			return "loc_ironward_city"
		"region_expansion_grayvalley":
			return "loc_grayvalley_center"
		_:
			return ""

func _create_npc_interactable(npc_data: Dictionary, pos: Vector2) -> void:
	var area: Area2D = Area2D.new()
	area.position = pos
	area.set_meta("npc_data", npc_data)
	
	var collision: CollisionShape2D = CollisionShape2D.new()
	var shape: CircleShape2D = CircleShape2D.new()
	shape.radius = 50.0
	collision.shape = shape
	area.add_child(collision)
	
	var npc_marker: ColorRect = ColorRect.new()
	npc_marker.size = Vector2(32, 32)
	npc_marker.position = Vector2(-16, -16)
	npc_marker.color = Color(0.3, 0.7, 1.0, 0.8)
	area.add_child(npc_marker)
	
	var npc_name_label: Label = Label.new()
	npc_name_label.text = npc_data.get("name", "???")
	npc_name_label.position = Vector2(-30, -40)
	npc_name_label.add_theme_font_size_override("font_size", 14)
	area.add_child(npc_name_label)
	
	area.body_entered.connect(_on_npc_area_body_entered.bind(area))
	area.body_exited.connect(_on_npc_area_body_exited.bind(area))
	
	if is_instance_valid(npcs_node):
		npcs_node.add_child(area)
	else:
		add_child(area)
	
	npc_interactables.append(area)

func _on_npc_area_body_entered(area: Area2D) -> void:
	nearby_npc = area
	interact_prompt.visible = true
	_update_interact_prompt_position()

func _on_npc_area_body_exited(area: Area2D) -> void:
	if nearby_npc == area:
		nearby_npc = null
		interact_prompt.visible = false

func _update_interact_prompt_position() -> void:
	if not is_instance_valid(nearby_npc) or not is_instance_valid(interact_prompt):
		return
	interact_prompt.global_position = nearby_npc.global_position + Vector2(-30, -70)

func _unhandled_input(event: InputEvent) -> void:
	# 处理 NPC 对话
	if event.is_action_pressed("interact") and is_instance_valid(nearby_npc):
		var npc_data: Dictionary = nearby_npc.get_meta("npc_data", {})
		if npc_data.size() > 0:
			_open_npc_dialog(npc_data)
			return
	
	# 处理敌人战斗
	if event.is_action_pressed("interact") and is_instance_valid(nearby_enemy):
		if nearby_enemy.has_method("trigger_combat"):
			nearby_enemy.trigger_combat()
			return

func _open_npc_dialog(npc_data: Dictionary) -> void:
	if npc_dialog != null and is_instance_valid(npc_dialog):
		npc_dialog.queue_free()
	
	var dialog_scene: PackedScene = load("res://scenes/ui/npc/NPCDialog.tscn")
	if dialog_scene:
		npc_dialog = dialog_scene.instantiate()
		add_child(npc_dialog)
		npc_dialog.accept_quest.connect(_on_quest_accepted)
		npc_dialog.dialog_closed.connect(_on_dialog_closed)
		npc_dialog.open_dialog(npc_data)

func _on_quest_accepted(quest_id: String) -> void:
	PlayerManager.accept_quest(quest_id)

func _on_dialog_closed() -> void:
	npc_dialog = null

func _setup_quest_tracker() -> void:
	var tracker_scene: PackedScene = load("res://scenes/ui/quests/QuestTracker.tscn")
	if tracker_scene:
		quest_tracker = tracker_scene.instantiate()
		add_child(quest_tracker)
		quest_tracker.quest_clicked.connect(_on_quest_tracker_quest_clicked)
		quest_tracker.open_quest_panel.connect(_on_open_quest_panel)

func _on_quest_tracker_quest_clicked(quest_id: String) -> void:
	_open_quest_panel()
	if quest_panel:
		var quest_script: Script = quest_panel.get_script()
		if quest_script and quest_panel.has_method("select_quest"):
			quest_panel.select_quest(quest_id)

func _on_open_quest_panel() -> void:
	if quest_panel != null and is_instance_valid(quest_panel):
		quest_panel.queue_free()
	
	var panel_scene: PackedScene = load("res://scenes/ui/quests/QuestPanel.tscn")
	if panel_scene:
		quest_panel = panel_scene.instantiate()
		add_child(quest_panel)
		quest_panel.back_to_menu.connect(_on_quest_panel_closed)

func _on_quest_panel_closed() -> void:
	if quest_panel != null and is_instance_valid(quest_panel):
		quest_panel.queue_free()
		quest_panel = null

func _setup_enemies() -> void:
	# 在区域中生成敌人
	var enemy_positions: Array[Vector2] = [
		Vector2(200, 300),
		Vector2(800, 400)
	]
	
	var enemy_types: Array[String] = ["wolf", "bandit"]
	
	for i in range(mini(enemy_positions.size(), enemy_types.size())):
		_spawn_enemy(enemy_types[i], enemy_positions[i])
	
	_setup_enemy_interact_prompt()

func _spawn_enemy(enemy_type: String, pos: Vector2) -> void:
	var enemy: Area2D = ENEMY_SCENE.instantiate()
	enemy.position = pos
	enemy.enemy_type = enemy_type
	enemy.combat_triggered.connect(_on_enemy_combat_triggered)
	enemy.enemy_interacted.connect(_on_enemy_interacted)
	add_child(enemy)

func _setup_enemy_interact_prompt() -> void:
	enemy_interact_prompt = Label.new()
	enemy_interact_prompt.text = "按 E 触发战斗"
	enemy_interact_prompt.visible = false
	enemy_interact_prompt.z_index = 100
	var style_box: StyleBoxFlat = StyleBoxFlat.new()
	style_box.bg_color = Color(0.5, 0.0, 0.0, 0.7)
	style_box.set_content_margin_all(8)
	enemy_interact_prompt.add_theme_stylebox_override("normal", style_box)
	add_child(enemy_interact_prompt)

func _on_enemy_interacted(enemy_type: String) -> void:
	interact_prompt.visible = false
	if enemy_interact_prompt:
		enemy_interact_prompt.visible = true
		# 更新位置需要根据具体敌人位置
		for child in get_children():
			if child is Area2D and child.has_method("trigger_combat"):
				if child.enemy_type == enemy_type:
					nearby_enemy = child
					enemy_interact_prompt.global_position = child.global_position + Vector2(-50, -70)
					break

func _on_enemy_combat_triggered(enemy_type: String) -> void:
	if enemy_interact_prompt:
		enemy_interact_prompt.visible = false
	_open_combat_hud()

func _setup_combat_signals() -> void:
	CombatManager.combat_ended.connect(_on_combat_ended)

func _open_combat_hud() -> void:
	if combat_hud != null and is_instance_valid(combat_hud):
		combat_hud.queue_free()
	
	var hud_scene: PackedScene = load("res://scenes/ui/combat/CombatHUD.tscn")
	if hud_scene:
		combat_hud = hud_scene.instantiate()
		add_child(combat_hud)
		combat_hud.attack_pressed.connect(_on_attack_pressed)
		combat_hud.flee_pressed.connect(_on_flee_pressed)
		combat_started.emit(CombatManager.current_enemy.get("enemy_type", "unknown"))

func _on_attack_pressed() -> void:
	# 攻击逻辑在 CombatManager 中处理
	pass

func _on_flee_pressed() -> void:
	# 逃跑逻辑在 CombatManager 中处理
	pass

func _on_combat_ended(result: String, exp_gained: int) -> void:
	# 战斗结束后关闭 HUD
	if combat_hud != null and is_instance_valid(combat_hud):
		await get_tree().create_timer(2.5).timeout
		combat_hud.queue_free()
		combat_hud = null
	
	# 如果战斗胜利，移除敌人
	if result == "victory" and is_instance_valid(nearby_enemy):
		nearby_enemy.queue_free()
		nearby_enemy = null

func _process(_delta: float) -> void:
	if is_instance_valid(nearby_npc) and is_instance_valid(interact_prompt):
		_update_interact_prompt_position()

func _on_back_button_pressed() -> void:
	back_to_world_map.emit()

func get_player() -> CharacterBody2D:
	return player

func set_region_data(data: Dictionary) -> void:
	region_id = data.get("region_id", region_id)
	region_name = data.get("name", region_name)
	
	if is_instance_valid(title_label):
		title_label.text = region_name
