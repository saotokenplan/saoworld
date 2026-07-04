extends Control
## 投票界面脚本

signal vote_submitted(candidate_id: String)
signal back_pressed

@onready var back_button: Button = $TopBar/BackButton
@onready var cycle_title: Label = $Content/VBox/CycleTitle
@onready var cycle_description: Label = $Content/VBox/CycleDescription
@onready var candidates_container: VBoxContainer = $Content/VBox/CandidatesContainer
@onready var submit_button: Button = $Content/VBox/SubmitButton
@onready var status_label: Label = $Content/VBox/StatusLabel

var selected_candidate_id: String = ""
var candidate_buttons: Array[Button] = []

func _ready() -> void:
	back_button.pressed.connect(_on_back_pressed)
	submit_button.pressed.connect(_on_submit_pressed)
	back_button.text = "返回"
	submit_button.text = "提交投票"
	status_label.text = "请选择一个候选项"

func set_cycle_data(cycle_data: Dictionary, candidate_list: Array[Dictionary]) -> void:
	cycle_title.text = cycle_data.get("title", "投票周期")
	cycle_description.text = cycle_data.get("description", "")
	_clear_candidates()
	_add_candidates(candidate_list)

func _clear_candidates() -> void:
	for btn in candidate_buttons:
		if is_instance_valid(btn):
			btn.queue_free()
	candidate_buttons.clear()
	selected_candidate_id = ""
	_update_submit_button()

func _add_candidates(candidate_list: Array[Dictionary]) -> void:
	for candidate in candidate_list:
		var btn := Button.new()
		btn.text = "%s\n%s" % [candidate.get("title", ""), candidate.get("description", "")]
		btn.toggle_mode = true
		btn.custom_minimum_size = Vector2(400, 80)
		var cid: String = candidate.get("candidate_id", "")
		btn.pressed.connect(func(): _on_candidate_selected(cid, btn))
		candidates_container.add_child(btn)
		candidate_buttons.append(btn)

func _on_candidate_selected(candidate_id: String, button: Button) -> void:
	selected_candidate_id = candidate_id
	for btn in candidate_buttons:
		if btn != button:
			btn.button_pressed = false
	_update_submit_button()

func _update_submit_button() -> void:
	submit_button.disabled = selected_candidate_id == ""

func _on_submit_pressed() -> void:
	if selected_candidate_id != "":
		vote_submitted.emit(selected_candidate_id)
		status_label.text = "正在提交投票..."

func _on_back_pressed() -> void:
	back_pressed.emit()

func show_status(message: String) -> void:
	status_label.text = message

func show_error(error_msg: String) -> void:
	status_label.text = "错误：%s" % error_msg
