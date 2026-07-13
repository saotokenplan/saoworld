extends Control
## 投票界面脚本

signal vote_submitted(candidate_id: String)
signal back_pressed
signal open_discussion_pressed

@onready var back_button: Button = $TopBar/BackButton
@onready var cycle_title: Label = $Content/VBox/CycleTitle
@onready var cycle_description: Label = $Content/VBox/CycleDescription
@onready var candidates_container: VBoxContainer = $Content/VBox/CandidatesContainer
@onready var submit_button: Button = $Content/VBox/SubmitButton
@onready var status_label: Label = $Content/VBox/StatusLabel
@onready var discussion_button: Button = $Content/VBox/DiscussionButton
@onready var progress_label: Label = $Content/VBox/ProgressLabel
@onready var leading_label: Label = $Content/VBox/LeadingLabel

var selected_candidate_id: String = ""
var candidate_buttons: Array[Button] = []
var is_loading: bool = false
var has_voted: bool = false
var candidate_id_to_button: Dictionary = {}

func _ready() -> void:
	back_button.pressed.connect(_on_back_pressed)
	submit_button.pressed.connect(_on_submit_pressed)
	discussion_button.pressed.connect(_on_discussion_pressed)
	back_button.text = "返回"
	submit_button.text = "提交投票"
	discussion_button.text = "进入讨论区"
	status_label.text = "请选择一个候选项"
	progress_label.text = ""
	leading_label.text = ""
	
	VoteManager.current_vote_loaded.connect(_on_current_vote_loaded)
	VoteManager.vote_submitted.connect(_on_vote_submitted)
	VoteManager.vote_error.connect(_on_vote_error)
	VoteManager.loading_changed.connect(_on_loading_changed)
	VoteManager.vote_progress_updated.connect(_on_vote_progress_updated)
	
	if VoteManager.current_cycle.is_empty():
		refresh()
	else:
		show_vote_from_manager()

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
	candidate_id_to_button.clear()
	selected_candidate_id = ""
	_update_submit_button()

func _add_candidates(candidate_list: Array[Dictionary]) -> void:
	for candidate in candidate_list:
		var btn := Button.new()
		var vote_count: int = candidate.get("vote_count", 0)
		var percentage: float = candidate.get("percentage", 0.0)
		if has_voted and vote_count > 0:
			btn.text = "%s\n%s\n票数：%d (%.1f%%)" % [
				candidate.get("title", ""),
				candidate.get("description", ""),
				vote_count,
				percentage
			]
		else:
			btn.text = "%s\n%s" % [candidate.get("title", ""), candidate.get("description", "")]
		btn.toggle_mode = true
		btn.custom_minimum_size = Vector2(400, 80)
		var cid: String = candidate.get("candidate_id", "")
		btn.pressed.connect(func(): _on_candidate_selected(cid, btn))
		candidates_container.add_child(btn)
		candidate_buttons.append(btn)
		candidate_id_to_button[cid] = btn

func _on_candidate_selected(candidate_id: String, button: Button) -> void:
	if has_voted or is_loading:
		return
	selected_candidate_id = candidate_id
	for btn in candidate_buttons:
		if btn != button:
			btn.button_pressed = false
	_update_submit_button()

func _update_submit_button() -> void:
	if has_voted:
		submit_button.disabled = true
		submit_button.text = "您已投票"
	elif is_loading:
		submit_button.disabled = true
	else:
		submit_button.disabled = selected_candidate_id == ""

func _on_submit_pressed() -> void:
	if selected_candidate_id == "" or has_voted or is_loading:
		return
	VoteManager.submit_vote(selected_candidate_id)

func _on_back_pressed() -> void:
	back_pressed.emit()

func _on_discussion_pressed() -> void:
	open_discussion_pressed.emit()

func show_status(message: String) -> void:
	status_label.text = message

func show_error(error_msg: String) -> void:
	status_label.text = "错误：%s" % error_msg

func _on_current_vote_loaded() -> void:
	show_vote_from_manager()

func _on_vote_submitted() -> void:
	has_voted = true
	show_vote_from_manager()
	status_label.text = "投票成功！感谢您的参与"

func _on_vote_error(error_code: String, message: String) -> void:
	status_label.text = "错误：%s - %s" % [error_code, message]
	_update_submit_button()

func _on_loading_changed(loading: bool) -> void:
	is_loading = loading
	if loading:
		submit_button.disabled = true
		status_label.text = "加载中..."
	else:
		_update_submit_button()
		if not has_voted and selected_candidate_id == "":
			status_label.text = "请选择一个候选项"

func refresh() -> void:
	VoteManager.fetch_current_vote()

func show_vote_from_manager() -> void:
	has_voted = VoteManager.has_voted
	set_cycle_data(VoteManager.current_cycle, VoteManager.candidates)
	if has_voted:
		status_label.text = "您已投票，以下是当前投票结果预览"
		submit_button.disabled = true
		submit_button.text = "您已投票"
		VoteManager.start_progress_polling()
	else:
		status_label.text = "请选择一个候选项"
		_update_submit_button()

func _on_vote_progress_updated(progress: Dictionary) -> void:
	var total_votes: int = progress.get("total_votes", 0)
	progress_label.text = "当前总票数：%d" % total_votes
	
	var leading_id: String = str(progress.get("leading_candidate_id", ""))
	var leading_title: String = ""
	for candidate in progress.get("candidates", []):
		if str(candidate.get("candidate_id", "")) == leading_id:
			leading_title = candidate.get("title", "")
			break
	
	if leading_title != "":
		leading_label.text = "领先候选：%s" % leading_title
	else:
		leading_label.text = ""
	
	if has_voted:
		for candidate in progress.get("candidates", []):
			var cid: String = str(candidate.get("candidate_id", ""))
			if cid in candidate_id_to_button:
				var btn: Button = candidate_id_to_button[cid]
				var vote_count: int = candidate.get("vote_count", 0)
				var percentage: float = candidate.get("percentage", 0.0)
				btn.text = "%s\n%s\n票数：%d (%.1f%%)" % [
					candidate.get("title", ""),
					candidate.get("description", ""),
					vote_count,
					percentage
				]

func _enter_tree() -> void:
	VoteManager.fetch_vote_progress()
	if has_voted or VoteManager.has_voted:
		VoteManager.start_progress_polling()

func _exit_tree() -> void:
	VoteManager.stop_progress_polling()
