extends Control

signal closed

@onready var close_button: Button = $DetailPanel/VBox/TopBar/CloseButton
@onready var title_label: Label = $DetailPanel/VBox/TopBar/TitleLabel
@onready var package_version_label: Label = $DetailPanel/VBox/ScrollContainer/ContentBox/PackageVersionLabel
@onready var status_label: Label = $DetailPanel/VBox/ScrollContainer/ContentBox/StatusLabel
@onready var released_at_label: Label = $DetailPanel/VBox/ScrollContainer/ContentBox/ReleasedAtLabel
@onready var chapter_label: Label = $DetailPanel/VBox/ScrollContainer/ContentBox/ChapterLabel
@onready var summary_label: Label = $DetailPanel/VBox/ScrollContainer/ContentBox/SummaryLabel
@onready var regions_list: VBoxContainer = $DetailPanel/VBox/ScrollContainer/ContentBox/RegionsList
@onready var npcs_list: VBoxContainer = $DetailPanel/VBox/ScrollContainer/ContentBox/NPCsList
@onready var quests_list: VBoxContainer = $DetailPanel/VBox/ScrollContainer/ContentBox/QuestsList

var package_data: Dictionary = {}

func _ready() -> void:
	close_button.pressed.connect(_on_close_pressed)
	$ModalBackground.gui_input.connect(_on_background_clicked)
	visible = false

func show_package(package: Dictionary) -> void:
	package_data = package
	_update_ui()
	visible = true

func hide() -> void:
	visible = false
	package_data.clear()

func _update_ui() -> void:
	title_label.text = package_data.get("title", "内容包详情")
	package_version_label.text = "版本：%s" % package_data.get("package_version", "未知")
	
	var status: String = package_data.get("status", "")
	var status_text: String = _get_status_text(status)
	status_label.text = "状态：%s" % status_text
	status_label.add_theme_color_override("font_color", _get_status_color(status))
	
	released_at_label.text = "发布时间：%s" % package_data.get("released_at", "未发布")
	chapter_label.text = "章节：%s" % package_data.get("chapter_id", "未知")
	
	var summary: String = package_data.get("summary", "")
	summary_label.text = "描述：%s" % (summary if summary != "" else "暂无描述")
	
	_update_regions_list()
	_update_npcs_list()
	_update_quests_list()

func _get_status_text(status: String) -> String:
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

func _get_status_color(status: String) -> Color:
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

func _update_regions_list() -> void:
	_clear_list(regions_list)
	var payload: Dictionary = package_data.get("payload", {})
	var regions: Array = payload.get("regions", [])
	
	if regions.is_empty():
		var empty_label: Label = Label.new()
		empty_label.text = "无区域"
		empty_label.add_theme_font_size_override("font_size", 12)
		empty_label.add_theme_color_override("font_color", Color(0.5, 0.5, 0.5))
		regions_list.add_child(empty_label)
		return
	
	for region in regions:
		var label: Label = Label.new()
		if typeof(region) == TYPE_DICTIONARY:
			var region_name: String = region.get("name", region.get("region_id", "未知区域"))
			var region_type: String = region.get("region_type", "")
			if region_type != "":
				label.text = "%s (%s)" % [region_name, region_type]
			else:
				label.text = region_name
		else:
			label.text = str(region)
		label.add_theme_font_size_override("font_size", 13)
		regions_list.add_child(label)

func _update_npcs_list() -> void:
	_clear_list(npcs_list)
	var payload: Dictionary = package_data.get("payload", {})
	var npcs: Array = payload.get("npcs", [])
	
	if npcs.is_empty():
		var empty_label: Label = Label.new()
		empty_label.text = "无新增NPC"
		empty_label.add_theme_font_size_override("font_size", 12)
		empty_label.add_theme_color_override("font_color", Color(0.5, 0.5, 0.5))
		npcs_list.add_child(empty_label)
		return
	
	for npc in npcs:
		var label: Label = Label.new()
		if typeof(npc) == TYPE_DICTIONARY:
			var npc_name: String = npc.get("name", npc.get("npc_key", "未知NPC"))
			var npc_role: String = npc.get("role", "")
			if npc_role != "":
				label.text = "%s - %s" % [npc_name, npc_role]
			else:
				label.text = npc_name
		else:
			label.text = str(npc)
		label.add_theme_font_size_override("font_size", 13)
		npcs_list.add_child(label)

func _update_quests_list() -> void:
	_clear_list(quests_list)
	var payload: Dictionary = package_data.get("payload", {})
	var quests: Array = payload.get("quests", [])
	
	if quests.is_empty():
		var empty_label: Label = Label.new()
		empty_label.text = "无新增任务"
		empty_label.add_theme_font_size_override("font_size", 12)
		empty_label.add_theme_color_override("font_color", Color(0.5, 0.5, 0.5))
		quests_list.add_child(empty_label)
		return
	
	for quest in quests:
		var label: Label = Label.new()
		if typeof(quest) == TYPE_DICTIONARY:
			var quest_title: String = quest.get("title", quest.get("quest_key", "未知任务"))
			var quest_type: String = quest.get("quest_type", "")
			if quest_type != "":
				label.text = "%s [%s]" % [quest_title, quest_type]
			else:
				label.text = quest_title
		else:
			label.text = str(quest)
		label.add_theme_font_size_override("font_size", 13)
		quests_list.add_child(label)

func _clear_list(container: VBoxContainer) -> void:
	for child in container.get_children():
		if is_instance_valid(child):
			child.queue_free()

func _on_close_pressed() -> void:
	hide()
	closed.emit()

func _on_background_clicked(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		hide()
		closed.emit()