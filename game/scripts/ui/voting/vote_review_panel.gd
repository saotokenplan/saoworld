extends Control
## 投票复盘报告面板

signal back_pressed
signal view_content_package(package_id: String)

@onready var back_button: Button = $TopBar/BackButton
@onready var title_label: Label = $TopBar/TitleLabel
@onready var scroll_container: ScrollContainer = $Content/ScrollContainer
@onready var content_box: VBoxContainer = $Content/ScrollContainer/ContentBox
@onready var status_label: Label = $Content/StatusLabel

var review_data: Dictionary = {}

func _ready() -> void:
	back_button.pressed.connect(_on_back_pressed)
	back_button.text = "返回"
	title_label.text = "投票复盘报告"
	status_label.text = ""
	visible = false

func show_review(data: Dictionary) -> void:
	review_data = data
	_update_ui()
	visible = true

func hide() -> void:
	visible = false
	review_data.clear()

func _update_ui() -> void:
	_clear_content()
	
	if review_data.is_empty():
		status_label.text = "暂无复盘数据"
		return
	
	status_label.text = ""
	
	# 周期标题
	var cycle_title: String = _get_cycle_title()
	_add_section_title(cycle_title)
	
	# 周期基本信息
	_add_info_label("章节", review_data.get("chapter_id", "未知"))
	_add_info_label("状态", _get_status_text(review_data.get("status", "")))
	_add_info_label("时间范围", _format_time_range())
	
	_add_separator()
	
	# 投票统计
	_add_section_title("投票统计")
	_add_info_label("总票数", str(review_data.get("total_votes", 0)))
	_add_info_label("加权总票数", "%.2f" % review_data.get("total_weighted_votes", 0.0))
	_add_info_label("参与率", "%.2f%%" % review_data.get("participation_rate", 0.0))
	
	var winning_candidate: Dictionary = review_data.get("winning_candidate", {})
	if not winning_candidate.is_empty():
		_add_info_label("获胜候选", winning_candidate.get("title", "未知"))
	
	_add_separator()
	
	# 候选结果列表
	_add_section_title("候选结果")
	var candidates: Array = review_data.get("candidates", [])
	if candidates.is_empty():
		_add_empty_label("暂无候选结果数据")
	else:
		for candidate in candidates:
			_add_candidate_item(candidate)
	
	_add_separator()
	
	# 生成参数与影响范围
	var generated_params: Dictionary = review_data.get("generated_params", {})
	var region_scope: Array = review_data.get("region_scope", [])
	if not generated_params.is_empty() or not region_scope.is_empty():
		_add_section_title("生成参数")
		if not region_scope.is_empty():
			_add_info_label("影响范围", ", ".join(region_scope))
		if not generated_params.is_empty():
			_add_info_label("参数", _format_generated_params(generated_params))
		_add_separator()
	
	# 落地内容包
	_add_section_title("落地内容")
	var content_package: Dictionary = review_data.get("content_package", {})
	if content_package.is_empty():
		_add_empty_label("该投票周期尚未产生落地内容")
	else:
		_add_content_package_item(content_package)

func _get_cycle_title() -> String:
	var cycle_id: String = review_data.get("vote_cycle_id", "")
	var title: String = review_data.get("title", "")
	if title != "":
		return title
	if cycle_id != "":
		return "投票周期 %s" % cycle_id
	return "投票复盘报告"

func _format_time_range() -> String:
	var starts_at: String = review_data.get("starts_at", "")
	var ends_at: String = review_data.get("ends_at", "")
	if starts_at == "" or ends_at == "":
		return "未知"
	return "%s 至 %s" % [starts_at, ends_at]

func _get_status_text(status: String) -> String:
	match status:
		"draft":
			return "草稿"
		"scheduled":
			return "已计划"
		"open":
			return "进行中"
		"closed":
			return "已关闭"
		"finalized":
			return "已结算"
		_:
			return status

func _format_generated_params(params: Dictionary) -> String:
	var parts: Array[String] = []
	for key in params.keys():
		parts.append("%s: %s" % [key, str(params[key])])
	return ", ".join(parts)

func _add_section_title(text: String) -> void:
	var label: Label = Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 18)
	label.bold = true
	label.add_theme_color_override("font_color", Color(1.0, 0.9, 0.6))
	content_box.add_child(label)

func _add_info_label(key: String, value: String) -> void:
	var label: Label = Label.new()
	label.text = "%s：%s" % [key, value]
	label.add_theme_font_size_override("font_size", 14)
	content_box.add_child(label)

func _add_empty_label(text: String) -> void:
	var label: Label = Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 13)
	label.add_theme_color_override("font_color", Color(0.5, 0.5, 0.5))
	content_box.add_child(label)

func _add_candidate_item(candidate: Dictionary) -> void:
	var panel: PanelContainer = PanelContainer.new()
	panel.add_theme_color_override("panel_bg_color", Color(0.15, 0.15, 0.2))
	panel.custom_minimum_size = Vector2(0, 60)
	
	var vbox: VBoxContainer = VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 4)
	
	var title_hbox: HBoxContainer = HBoxContainer.new()
	title_hbox.add_theme_constant_override("separation", 8)
	
	var name_label: Label = Label.new()
	name_label.text = candidate.get("title", "未知候选")
	name_label.add_theme_font_size_override("font_size", 15)
	name_label.bold = true
	title_hbox.add_child(name_label)
	
	if candidate.get("status", "") == "selected":
		var winner_badge: Label = Label.new()
		winner_badge.text = "★ 获胜"
		winner_badge.add_theme_font_size_override("font_size", 12)
		winner_badge.add_theme_color_override("font_color", Color(1.0, 0.8, 0.2))
		title_hbox.add_child(winner_badge)
	
	vbox.add_child(title_hbox)
	
	var stats_label: Label = Label.new()
	var vote_count: int = candidate.get("vote_count", 0)
	var percentage: float = candidate.get("percentage", 0.0)
	stats_label.text = "票数：%d（%.2f%%）" % [vote_count, percentage]
	stats_label.add_theme_font_size_override("font_size", 13)
	vbox.add_child(stats_label)
	
	panel.add_child(vbox)
	content_box.add_child(panel)

func _add_content_package_item(package: Dictionary) -> void:
	var panel: PanelContainer = PanelContainer.new()
	panel.add_theme_color_override("panel_bg_color", Color(0.15, 0.25, 0.15))
	panel.custom_minimum_size = Vector2(0, 80)
	
	var vbox: VBoxContainer = VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 4)
	
	var title_label_item: Label = Label.new()
	title_label_item.text = package.get("title", "未知内容包")
	title_label_item.add_theme_font_size_override("font_size", 16)
	title_label_item.bold = true
	vbox.add_child(title_label_item)
	
	var version_label: Label = Label.new()
	version_label.text = "版本：%s" % package.get("package_version", "未知")
	version_label.add_theme_font_size_override("font_size", 13)
	vbox.add_child(version_label)
	
	var status_label_item: Label = Label.new()
	var status: String = package.get("status", "")
	status_label_item.text = "状态：%s" % _get_package_status_text(status)
	status_label_item.add_theme_font_size_override("font_size", 13)
	status_label_item.add_theme_color_override("font_color", _get_package_status_color(status))
	vbox.add_child(status_label_item)
	
	var landed_at: String = package.get("landed_at", "")
	if landed_at != "":
		var landed_label: Label = Label.new()
		landed_label.text = "落地时间：%s" % landed_at
		landed_label.add_theme_font_size_override("font_size", 12)
		landed_label.add_theme_color_override("font_color", Color(0.6, 0.9, 0.6))
		vbox.add_child(landed_label)
	
	var affected_regions: Array = package.get("affected_regions", [])
	if not affected_regions.is_empty():
		var regions_label: Label = Label.new()
		regions_label.text = "影响区域：%s" % ", ".join(affected_regions)
		regions_label.add_theme_font_size_override("font_size", 12)
		regions_label.add_theme_color_override("font_color", Color(0.7, 0.8, 1.0))
		vbox.add_child(regions_label)
	
	var payload: Dictionary = package.get("payload", {})
	_add_payload_summary(vbox, payload)
	
	var package_id: String = package.get("content_package_id", "")
	if package_id != "":
		var view_button: Button = Button.new()
		view_button.text = "查看详情"
		view_button.add_theme_font_size_override("font_size", 12)
		view_button.custom_minimum_size = Vector2(80, 24)
		view_button.pressed.connect(func():
			view_content_package.emit(package_id)
		)
		vbox.add_child(view_button)
	
	panel.add_child(vbox)
	content_box.add_child(panel)

func _add_payload_summary(parent: VBoxContainer, payload: Dictionary) -> void:
	var npcs: Array = payload.get("npcs", [])
	var quests: Array = payload.get("quests", [])
	var regions: Array = payload.get("regions", [])
	
	if not npcs.is_empty():
		var npcs_label: Label = Label.new()
		npcs_label.text = "新增 NPC：%d" % npcs.size()
		npcs_label.add_theme_font_size_override("font_size", 12)
		parent.add_child(npcs_label)
	
	if not quests.is_empty():
		var quests_label: Label = Label.new()
		quests_label.text = "新增任务：%d" % quests.size()
		quests_label.add_theme_font_size_override("font_size", 12)
		parent.add_child(quests_label)
	
	if not regions.is_empty():
		var regions_label: Label = Label.new()
		regions_label.text = "新增/影响区域：%d" % regions.size()
		regions_label.add_theme_font_size_override("font_size", 12)
		parent.add_child(regions_label)

func _get_package_status_text(status: String) -> String:
	match status:
		"packaged":
			return "已打包"
		"gray":
			return "灰度中"
		"live":
			return "已上线"
		"archived":
			return "已归档"
		"rolled_back":
			return "已回滚"
		_:
			return status

func _get_package_status_color(status: String) -> Color:
	match status:
		"packaged":
			return Color(0.8, 0.8, 0.8)
		"gray":
			return Color(1.0, 0.8, 0.2)
		"live":
			return Color(0.2, 0.8, 0.2)
		"archived":
			return Color(0.6, 0.6, 0.6)
		"rolled_back":
			return Color(1.0, 0.4, 0.4)
		_:
			return Color(0.8, 0.8, 0.8)

func _add_separator() -> void:
	var separator: Control = Control.new()
	separator.custom_minimum_size = Vector2(0, 12)
	content_box.add_child(separator)

func _clear_content() -> void:
	for child in content_box.get_children():
		if is_instance_valid(child):
			child.queue_free()

func _on_back_pressed() -> void:
	hide()
	back_pressed.emit()

func show_loading(loading: bool) -> void:
	if loading:
		status_label.text = "加载中..."
	else:
		status_label.text = ""
