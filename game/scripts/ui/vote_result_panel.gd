extends Control
## 投票结果面板脚本（支持图表可视化）

signal back_pressed
signal view_details_pressed(candidate_id: String)

@onready var back_button: Button = $TopBar/BackButton
@onready var cycle_title: Label = $Content/VBox/CycleTitle
@onready var total_votes_label: Label = $Content/VBox/StatsHBox/TotalVotesLabel
@onready var candidates_container: VBoxContainer = $Content/VBox/CandidatesContainer
@onready var winner_label: Label = $Content/VBox/WinnerBanner/WinnerLabel
@onready var impact_region_label: Label = $Content/VBox/ImpactSection/ImpactRegionLabel
@onready var expected_launch_label: Label = $Content/VBox/ImpactSection/ExpectedLaunchLabel
@onready var chart_draw: Control = $Content/VBox/ChartDraw
@onready var pie_chart_button: Button = $Content/VBox/ChartToggleButtons/PieChartButton
@onready var bar_chart_button: Button = $Content/VBox/ChartToggleButtons/BarChartButton

var candidate_rows: Array[Control] = []
var current_chart_type: String = "pie"
var chart_data: Dictionary = {}
var vote_cycle_id: String = ""

func _ready() -> void:
	back_button.pressed.connect(_on_back_pressed)
	back_button.text = "返回"
	pie_chart_button.pressed.connect(_on_pie_chart_button_pressed)
	bar_chart_button.pressed.connect(_on_bar_chart_button_pressed)
	VoteManager.chart_data_loaded.connect(_on_chart_data_loaded)

func set_result_data(cycle_data: Dictionary, candidate_list: Array[Dictionary]) -> void:
	cycle_title.text = cycle_data.get("title", "投票周期")
	vote_cycle_id = str(cycle_data.get("vote_cycle_id", cycle_data.get("cycle_id", "")))

	var total_votes: int = _calculate_total_votes(candidate_list)
	total_votes_label.text = "总票数：%d" % total_votes

	var winner: Dictionary = _find_winner(candidate_list)
	if not winner.is_empty():
		winner_label.text = "获胜方案：%s" % winner.get("title", "未知")
	else:
		winner_label.text = "获胜方案：暂无"

	impact_region_label.text = "预计影响区域：%s" % cycle_data.get("impact_region", "待定")
	expected_launch_label.text = "预计上线周期：%s" % cycle_data.get("expected_launch", "待定")

	_clear_candidates()
	for candidate in candidate_list:
		var is_winner: bool = candidate.get("candidate_id", "") == winner.get("candidate_id", "")
		_add_candidate_result(candidate, total_votes, is_winner)

	# 获取图表数据
	if vote_cycle_id != "":
		VoteManager.fetch_vote_result_chart_data(vote_cycle_id, current_chart_type)

func _clear_candidates() -> void:
	for row in candidate_rows:
		if is_instance_valid(row):
			row.queue_free()
	candidate_rows.clear()

func _add_candidate_result(candidate: Dictionary, total_votes: int, is_winner: bool) -> void:
	var row := HBoxContainer.new()
	row.custom_minimum_size = Vector2(0, 60)
	row.add_theme_constant_override("separation", 10)

	var name_label := Label.new()
	name_label.text = candidate.get("title", "未知候选项")
	name_label.custom_minimum_size = Vector2(200, 0)
	if is_winner:
		name_label.text = "🏆 %s" % name_label.text
		name_label.add_theme_color_override("font_color", Color(1, 0.84, 0))
	row.add_child(name_label)

	var votes_label := Label.new()
	votes_label.text = "%d 票" % candidate.get("vote_count", 0)
	votes_label.custom_minimum_size = Vector2(80, 0)
	row.add_child(votes_label)

	var progress_bar := ProgressBar.new()
	progress_bar.value = _calculate_percentage(candidate.get("vote_count", 0), total_votes)
	progress_bar.custom_minimum_size = Vector2(200, 20)
	if is_winner:
		progress_bar.add_theme_color_override("progress_color", Color(1, 0.84, 0))
	row.add_child(progress_bar)

	var percent_label := Label.new()
	percent_label.text = "%.1f%%" % _calculate_percentage(candidate.get("vote_count", 0), total_votes)
	percent_label.custom_minimum_size = Vector2(60, 0)
	row.add_child(percent_label)

	var details_button := Button.new()
	details_button.text = "详情"
	details_button.custom_minimum_size = Vector2(60, 30)
	var cid: String = candidate.get("candidate_id", "")
	details_button.pressed.connect(func(): _on_view_details_pressed(cid))
	row.add_child(details_button)

	candidates_container.add_child(row)
	candidate_rows.append(row)

func _calculate_percentage(votes: int, total: int) -> float:
	if total == 0:
		return 0.0
	return float(votes) / float(total) * 100.0

func _find_winner(candidate_list: Array[Dictionary]) -> Dictionary:
	var max_votes: int = 0
	var winner: Dictionary = {}
	for candidate in candidate_list:
		var votes: int = candidate.get("vote_count", 0)
		if votes > max_votes:
			max_votes = votes
			winner = candidate
	return winner

func _calculate_total_votes(candidate_list: Array[Dictionary]) -> int:
	var total: int = 0
	for candidate in candidate_list:
		total += candidate.get("vote_count", 0)
	return total

func _on_back_pressed() -> void:
	back_pressed.emit()

func _on_view_details_pressed(candidate_id: String) -> void:
	view_details_pressed.emit(candidate_id)

func _on_pie_chart_button_pressed() -> void:
	current_chart_type = "pie"
	if vote_cycle_id != "":
		VoteManager.fetch_vote_result_chart_data(vote_cycle_id, "pie")

func _on_bar_chart_button_pressed() -> void:
	current_chart_type = "bar"
	if vote_cycle_id != "":
		VoteManager.fetch_vote_result_chart_data(vote_cycle_id, "bar")

func _on_chart_data_loaded(data: Dictionary) -> void:
	chart_data = data
	if chart_data.get("chart_type", "") == current_chart_type:
		# 将数据传递给 ChartDraw 控件
		if chart_draw and chart_draw.has_method("set_chart_data"):
			chart_draw.set_chart_data(chart_data)