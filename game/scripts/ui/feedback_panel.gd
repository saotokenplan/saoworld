extends Control

## 反馈面板 - 玩家提交反馈的UI界面

const MAX_TITLE_LENGTH: int = 256
const MAX_CONTENT_LENGTH: int = 5000

@onready var feedback_type_option: OptionButton = $VBoxContainer/FeedbackTypeOption
@onready var priority_option: OptionButton = $VBoxContainer/PriorityOption
@onready var title_input: LineEdit = $VBoxContainer/TitleInput
@onready var content_input: TextEdit = $VBoxContainer/ContentInput
@onready var region_input: LineEdit = $VBoxContainer/RegionInput
@onready var chapter_input: LineEdit = $VBoxContainer/ChapterInput
@onready var submit_button: Button = $VBoxContainer/SubmitButton
@onready var cancel_button: Button = $VBoxContainer/CancelButton
@onready var message_label: Label = $VBoxContainer/MessageLabel
@onready var loading_indicator: Control = $VBoxContainer/LoadingIndicator

var _feedback_manager: Node = null


func _ready() -> void:
	_feedback_manager = get_node_or_null("/root/FeedbackManager")
	if _feedback_manager == null:
		push_error("FeedbackPanel: FeedbackManager not found")
		return
	
	_feedback_manager.feedback_submitted.connect(_on_feedback_submitted)
	_feedback_manager.feedback_failed.connect(_on_feedback_failed)
	
	_setup_options()
	_connect_signals()
	_hide_message()


func _setup_options() -> void:
	# 设置反馈类型选项
	if feedback_type_option:
		feedback_type_option.clear()
		var feedback_types = _feedback_manager.get_all_feedback_types()
		for type_key in feedback_types.keys():
			feedback_type_option.add_item(feedback_types[type_key], feedback_type_option.get_item_count())
			feedback_type_option.set_item_metadata(feedback_type_option.get_item_count() - 1, type_key)
		feedback_type_option.select(0)
	
	# 设置优先级选项
	if priority_option:
		priority_option.clear()
		var priorities = _feedback_manager.get_all_priorities()
		for priority_key in priorities.keys():
			priority_option.add_item(priorities[priority_key], priority_option.get_item_count())
			priority_option.set_item_metadata(priority_option.get_item_count() - 1, priority_key)
		priority_option.select(1)  # 默认选择"中"


func _connect_signals() -> void:
	if submit_button:
		submit_button.pressed.connect(_on_submit_pressed)
	if cancel_button:
		cancel_button.pressed.connect(_on_cancel_pressed)
	if title_input:
		title_input.text_changed.connect(_on_title_changed)
	if content_input:
		content_input.text_changed.connect(_on_content_changed)


func _on_submit_pressed() -> void:
	# 验证输入
	if not _validate_input():
		return
	
	# 获取输入值
	var feedback_type = _get_selected_feedback_type()
	var priority = _get_selected_priority()
	var title = title_input.text.strip_edges()
	var content = content_input.text.strip_edges()
	var region_id = region_input.text.strip_edges() if region_input else ""
	var chapter_id = chapter_input.text.strip_edges() if chapter_input else ""
	
	# 显示加载状态
	_set_loading(true)
	_show_message("正在提交反馈...", Color(1, 1, 0))
	
	# 提交反馈
	_feedback_manager.submit_feedback(
		feedback_type,
		title,
		content,
		priority,
		region_id,
		chapter_id
	)


func _on_cancel_pressed() -> void:
	_clear_form()
	hide()


func _on_title_changed(new_text: String) -> void:
	if new_text.length() > MAX_TITLE_LENGTH:
		title_input.text = new_text.substr(0, MAX_TITLE_LENGTH)
		title_input.caret_column = MAX_TITLE_LENGTH


func _on_content_changed() -> void:
	if content_input and content_input.text.length() > MAX_CONTENT_LENGTH:
		content_input.text = content_input.text.substr(0, MAX_CONTENT_LENGTH)
		content_input.caret_column = MAX_CONTENT_LENGTH


func _validate_input() -> bool:
	# 检查标题
	if not title_input or title_input.text.strip_edges() == "":
		_show_message("请输入标题", Color(1, 0, 0))
		return false
	
	# 检查内容
	if not content_input or content_input.text.strip_edges() == "":
		_show_message("请输入反馈内容", Color(1, 0, 0))
		return false
	
	return true


func _get_selected_feedback_type() -> String:
	if not feedback_type_option:
		return "other"
	var index = feedback_type_option.selected
	if index < 0:
		return "other"
	return feedback_type_option.get_item_metadata(index)


func _get_selected_priority() -> String:
	if not priority_option:
		return "medium"
	var index = priority_option.selected
	if index < 0:
		return "medium"
	return priority_option.get_item_metadata(index)


func _on_feedback_submitted(feedback_id: String) -> void:
	_set_loading(false)
	_show_message("反馈提交成功！感谢您的反馈。", Color(0, 1, 0))
	
	# 延迟关闭面板
	await get_tree().create_timer(2.0).timeout
	_clear_form()
	hide()


func _on_feedback_failed(error: Dictionary) -> void:
	_set_loading(false)
	var message = "提交失败: "
	if error.has("message"):
		message += error["message"]
	else:
		message += "未知错误"
	_show_message(message, Color(1, 0, 0))


func _show_message(text: String, color: Color = Color.WHITE) -> void:
	if message_label:
		message_label.text = text
		message_label.add_theme_color_override("font_color", color)
		message_label.show()


func _hide_message() -> void:
	if message_label:
		message_label.hide()


func _set_loading(is_loading: bool) -> void:
	if loading_indicator:
		loading_indicator.visible = is_loading
	if submit_button:
		submit_button.disabled = is_loading


func _clear_form() -> void:
	if title_input:
		title_input.text = ""
	if content_input:
		content_input.text = ""
	if region_input:
		region_input.text = ""
	if chapter_input:
		chapter_input.text = ""
	if feedback_type_option:
		feedback_type_option.select(0)
	if priority_option:
		priority_option.select(1)
	_hide_message()


func show_panel() -> void:
	_clear_form()
	show()