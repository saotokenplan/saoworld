extends PanelContainer

signal npc_selected(npc_id: String)
signal back_to_menu()

var npcs: Array[Dictionary] = []

@onready var npc_list: VBoxContainer = $NPCList
@onready var back_button: Button = $BackButton

func _ready() -> void:
	back_button.pressed.connect(_on_back_button_pressed)
	load_npcs_from_data()

func load_npcs_from_data() -> void:
	var file: FileAccess = FileAccess.open("res://data/npcs/npc_list.json", FileAccess.READ)
	if file:
		var content: String = file.get_as_text()
		var data: Dictionary = JSON.parse_string(content)
		npcs = data.get("npcs", [])
		_render_npcs()
		file.close()

func load_npcs(npc_list: Array[Dictionary]) -> void:
	npcs = npc_list
	_render_npcs()

func _render_npcs() -> void:
	for child in npc_list.get_children():
		child.queue_free()
	
	for npc in npcs:
		var npc_item: Button = Button.new()
		npc_item.text = npc.get("name", "") + " - " + npc.get("role", "")
		npc_item.custom_minimum_size = Vector2(400, 40)
		npc_item.set_meta("npc_id", npc.get("npc_id", ""))
		
		var style_box: StyleBoxFlat = StyleBoxFlat.new()
		style_box.bg_color = Color(0.3, 0.5, 0.4)
		npc_item.add_theme_stylebox_override("normal", style_box)
		
		npc_item.pressed.connect(_on_npc_item_pressed)
		npc_list.add_child(npc_item)

func _on_npc_item_pressed() -> void:
	var item: Button = get_last_signal_receiver()
	var npc_id: String = item.get_meta("npc_id", "")
	if npc_id:
		npc_selected.emit(npc_id)

func _on_back_button_pressed() -> void:
	back_to_menu.emit()