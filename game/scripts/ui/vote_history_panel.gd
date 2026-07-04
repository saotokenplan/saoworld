extends Control
## 投票历史记录面板

signal back_pressed
signal item_selected(cycle_id: String)
signal load_more_pressed

@onready var back_button: Button = $TopBar/BackButton
@onready var title_label: Label = $TopBar/TitleLabel
@onready var history_list: VBoxContainer = $Content/ScrollContainer/HistoryList
@onready var load_more_button: Button = $Content/LoadMoreButton
@onready var status_label: Label = $Content/StatusLabel

var history_items: Array[Dictionary] = []
var current_offset: int = 0
var has_more: bool = true
var is_loading: bool = false

func _ready() -> void:
	back_button.pressed.connect(_on_back_pressed)
	load_more_button.pressed.connect(_on_load_more_pressed)
	back_button.text = "返回"
	title_label.text = "投票历史"
	load_more_button.text = "加载更多"
	status_label.text = ""

func set_history_data(items: Array[Dictionary], total: int) -> void:
	clear_history()
	history_items = items
	current_offset = items.size()
	has_more = current_offset < total
	for item in items:
		var item_control: Control = _create_history_item(item)
		history_list.add_child(item_control)
	_update_load_more_button()
	if items.is_empty():
		status_label.text = "暂无投票历史记录"
	else:
		status_label.text = ""

func add_history_items(items: Array[Dictionary]) -> void:
	for item in items:
		history_items.append(item)
		var item_control: Control = _create_history_item(item)
		history_list.add_child(item_control)
	current_offset += items.size()
	_update_load_more_button()

func _create_history_item(item: Dictionary) -> Control:
	var panel: PanelContainer = PanelContainer.new()
	var vbox: VBoxContainer = VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 4)
	
	var title_label_item: Label = Label.new()
	title_label_item.text = item.get("title", "未知周期")
	title_label_item.add_theme_font_size_override("font_size", 16)
	title_label_item.bold = true
	vbox.add_child(title_label_item)
	
	var time_label: Label = Label.new()
	var vote_time: String = item.get("vote_time", item.get("created_at", ""))
	time_label.text = "时间：%s" % vote_time
	time_label.add_theme_font_size_override("font_size", 12)
	vbox.add_child(time_label)
	
	var winner_label: Label = Label.new()
	var winner_name: String = item.get("winner_name", item.get("winning_candidate_title", "待定"))
	winner_label.text = "获胜：%s" % winner_name
	winner_label.add_theme_font_size_override("font_size", 12)
	winner_label.add_theme_color_override("font_color", Color(0.2, 0.8, 0.2))
	vbox.add_child(winner_label)
	
	var votes_label: Label = Label.new()
	var total_votes: int = item.get("total_votes", 0)
	votes_label.text = "总票数：%d" % total_votes
	votes_label.add_theme_font_size_override("font_size", 12)
	vbox.add_child(votes_label)
	
	var status_label_item: Label = Label.new()
	var status: String = item.get("status", "")
	var status_text: String = ""
	if status == "finalized" or status == "closed":
		status_text = "已结算"
		status_label_item.add_theme_color_override("font_color", Color(0.2, 0.6, 1.0))
	elif status == "open":
		status_text = "进行中"
		status_label_item.add_theme_color_override("font_color", Color(1.0, 0.8, 0.2))
	else:
		status_text = status
	status_label_item.add_theme_font_size_override("font_size", 12)
	status_label_item.text = "状态：%s" % status_text
	vbox.add_child(status_label_item)
	
	panel.add_child(vbox)
	panel.custom_minimum_size = Vector2(0, 100)
	
	var cycle_id: String = item.get("vote_cycle_id", item.get("cycle_id", ""))
	panel.gui_input.connect(func(event: InputEvent):
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			_on_item_clicked(cycle_id)
	)
	
	return panel

func _on_back_pressed() -> void:
	back_pressed.emit()

func _on_load_more_pressed() -> void:
	if not is_loading and has_more:
		load_more_pressed.emit()

func _on_item_clicked(cycle_id: String) -> void:
	item_selected.emit(cycle_id)

func show_loading(loading: bool) -> void:
	is_loading = loading
	if loading:
		status_label.text = "加载中..."
	else:
		if history_items.is_empty():
			status_label.text = "暂无投票历史记录"
		else:
			status_label.text = ""
	_update_load_more_button()

func clear_history() -> void:
	for child in history_list.get_children():
		if is_instance_valid(child):
			child.queue_free()
	history_items.clear()
	current_offset = 0
	has_more = true

func _update_load_more_button() -> void:
	load_more_button.visible = has_more and not history_items.is_empty()
	load_more_button.disabled = is_loading or not has_more
