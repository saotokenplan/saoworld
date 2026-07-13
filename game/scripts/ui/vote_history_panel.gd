extends Control
## 投票历史记录面板

signal back_pressed
signal item_selected(cycle_id: String)
signal load_more_pressed
signal view_content_package(cycle_id: String)
signal view_review(cycle_id: String)

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
	
	var hbox_main: HBoxContainer = HBoxContainer.new()
	hbox_main.add_theme_constant_override("separation", 8)
	
	var vbox: VBoxContainer = VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 4)
	
	var title_hbox: HBoxContainer = HBoxContainer.new()
	title_hbox.add_theme_constant_override("separation", 8)
	
	var title_label_item: Label = Label.new()
	title_label_item.text = item.get("title", "未知周期")
	title_label_item.add_theme_font_size_override("font_size", 16)
	title_label_item.bold = true
	title_hbox.add_child(title_label_item)
	
	var is_landed: bool = item.get("is_landed", false) or not item.get("content_package", {}).is_empty()
	if is_landed:
		var landed_badge: Label = Label.new()
		landed_badge.text = "✓ 已落地"
		landed_badge.add_theme_font_size_override("font_size", 12)
		landed_badge.add_theme_color_override("font_color", Color(0.2, 0.8, 0.2))
		landed_badge.add_theme_constant_override("outline_size", 1)
		title_hbox.add_child(landed_badge)
		panel.add_theme_color_override("panel_bg_color", Color(0.15, 0.25, 0.15))
	else:
		panel.add_theme_color_override("panel_bg_color", Color(0.15, 0.15, 0.2))
	
	vbox.add_child(title_hbox)
	
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
	
	var landed_at: String = item.get("landed_at", "")
	if is_landed and landed_at != "":
		var landed_label: Label = Label.new()
		landed_label.text = "落地时间：%s" % landed_at
		landed_label.add_theme_font_size_override("font_size", 11)
		landed_label.add_theme_color_override("font_color", Color(0.6, 0.9, 0.6))
		vbox.add_child(landed_label)
	
	var affected_regions: Array = item.get("affected_regions", [])
	if is_landed and not affected_regions.is_empty():
		var regions_label: Label = Label.new()
		regions_label.text = "影响区域：%s" % ", ".join(affected_regions)
		regions_label.add_theme_font_size_override("font_size", 11)
		regions_label.add_theme_color_override("font_color", Color(0.7, 0.8, 1.0))
		vbox.add_child(regions_label)
	
	hbox_main.add_child(vbox)
	
	if is_landed:
		var cycle_id: String = item.get("vote_cycle_id", item.get("cycle_id", ""))
		
		var review_button: Button = Button.new()
		review_button.text = "复盘"
		review_button.add_theme_font_size_override("font_size", 12)
		review_button.custom_minimum_size = Vector2(60, 24)
		review_button.pressed.connect(func():
			view_review.emit(cycle_id)
		)
		hbox_main.add_child(review_button)
		
		var view_button: Button = Button.new()
		view_button.text = "查看内容"
		view_button.add_theme_font_size_override("font_size", 12)
		view_button.custom_minimum_size = Vector2(80, 24)
		view_button.pressed.connect(func():
			view_content_package.emit(cycle_id)
		)
		hbox_main.add_child(view_button)
	
	panel.add_child(hbox_main)
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
