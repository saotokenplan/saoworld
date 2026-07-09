extends PanelContainer

signal quest_clicked(quest_id: String)
signal open_quest_panel()

var is_minimized: bool = false
var max_displayed: int = 3

@onready var title_bar: Control = $TitleBar
@onready var title_label: Label = $TitleBar/TitleLabel
@onready var toggle_button: Button = $TitleBar/ToggleButton
@onready var quest_list: VBoxContainer = $QuestList
@onready var open_panel_button: Button = $OpenPanelButton

func _ready() -> void:
	title_bar.gui_input.connect(_on_title_bar_gui_input)
	toggle_button.pressed.connect(_on_toggle_button_pressed)
	open_panel_button.pressed.connect(_on_open_panel_button_pressed)
	PlayerManager.player_quests_loaded.connect(_on_player_quests_loaded)
	PlayerManager.quest_accepted.connect(_on_quest_updated)
	PlayerManager.quest_completed.connect(_on_quest_updated)
	PlayerManager.quest_progress_updated.connect(_on_quest_updated)
	_refresh_quests()

func _on_title_bar_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_toggle_minimize()

func _on_toggle_button_pressed() -> void:
	_toggle_minimize()

func _on_open_panel_button_pressed() -> void:
	open_quest_panel.emit()

func _toggle_minimize() -> void:
	is_minimized = not is_minimized
	quest_list.visible = not is_minimized
	open_panel_button.visible = not is_minimized
	toggle_button.text = "展开" if is_minimized else "收起"

func _on_player_quests_loaded() -> void:
	_refresh_quests()

func _on_quest_updated(_quest_id: String) -> void:
	_refresh_quests()

func _refresh_quests() -> void:
	for child in quest_list.get_children():
		child.queue_free()
	
	var active_quests: Array[Dictionary] = PlayerManager.get_active_quests()
	title_label.text = "进行中任务 (%d)" % active_quests.size()
	
	if active_quests.size() == 0:
		var empty_label: Label = Label.new()
		empty_label.text = "暂无进行中任务"
		empty_label.add_theme_font_size_override("font_size", 12)
		empty_label.modulate = Color(0.7, 0.7, 0.7)
		quest_list.add_child(empty_label)
		return
	
	var display_count: int = min(active_quests.size(), max_displayed)
	for i in range(display_count):
		var quest: Dictionary = active_quests[i]
		_add_quest_item(quest)
	
	if active_quests.size() > max_displayed:
		var more_label: Label = Label.new()
		more_label.text = "...还有 %d 个任务" % (active_quests.size() - max_displayed)
		more_label.add_theme_font_size_override("font_size", 11)
		more_label.modulate = Color(0.6, 0.6, 0.6)
		more_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		quest_list.add_child(more_label)

func _add_quest_item(quest: Dictionary) -> void:
	var quest_id: String = quest.get("quest_id", quest.get("player_quest_id", ""))
	var quest_button: Button = Button.new()
	quest_button.text = quest.get("title", quest_id)
	quest_button.custom_minimum_size = Vector2(250, 32)
	quest_button.set_meta("quest_id", quest_id)
	
	var style_box: StyleBoxFlat = StyleBoxFlat.new()
	style_box.bg_color = Color(0.15, 0.2, 0.25, 0.9)
	style_box.border_color = Color(0.3, 0.4, 0.5)
	style_box.border_width_left = 2
	quest_button.add_theme_stylebox_override("normal", style_box)
	
	var hover_style: StyleBoxFlat = style_box.duplicate()
	hover_style.bg_color = Color(0.2, 0.3, 0.4, 0.95)
	quest_button.add_theme_stylebox_override("hover", hover_style)
	
	quest_button.pressed.connect(_on_quest_item_pressed.bind(quest_id))
	quest_list.add_child(quest_button)

func _on_quest_item_pressed(quest_id: String) -> void:
	quest_clicked.emit(quest_id)

func set_max_displayed(count: int) -> void:
	max_displayed = count
	_refresh_quests()

func get_active_quest_count() -> int:
	return PlayerManager.get_active_quests().size()
