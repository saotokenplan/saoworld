extends Control
## 图表绘制控件

var chart_data: Dictionary = {}
var chart_type: String = "pie"
var parent_panel: Control = null

func _ready() -> void:
	parent_panel = get_parent().get_parent().get_parent()

func set_chart_data(data: Dictionary) -> void:
	chart_data = data
	chart_type = data.get("chart_type", "pie")
	queue_redraw()

func _draw() -> void:
	if chart_data.is_empty():
		return

	if chart_type == "pie":
		_draw_pie_chart()
	elif chart_type == "bar":
		_draw_bar_chart()

func _draw_pie_chart() -> void:
	if chart_data.is_empty():
		return

	var items: Array = chart_data.get("items", [])
	if items.is_empty():
		return

	var center: Vector2 = Vector2(size.x / 2, size.y / 2)
	var radius: float = min(size.x, size.y) / 3.0
	var start_angle: float = -PI / 2  # 从顶部开始

	# 绘制背景圆
	draw_circle(center, radius, Color(0.1, 0.1, 0.15))

	# 绘制扇形
	for item in items:
		var percentage: float = item.get("percentage", 0.0) / 100.0
		var angle: float = percentage * 2 * PI
		var color_str: String = item.get("color", "#FF6B6B")
		var color: Color = Color(color_str)

		# 绘制扇形（使用 draw_polygon）
		var points: Array = []
		var segments: int = max(int(percentage * 32), 4)  # 根据百分比调整精度
		for i in range(segments + 1):
			var a: float = start_angle + (angle * i / segments)
			var point: Vector2 = center + Vector2(cos(a), sin(a)) * radius
			points.append(point)

		# 添加中心点形成完整的扇形
		points.append(center)

		var colors: Array = []
		for _i in range(points.size()):
			colors.append(color)

		draw_polygon(points, colors)

		start_angle += angle

	_draw_pie_labels(center, radius)

func _draw_pie_labels(center: Vector2, radius: float) -> void:
	var items: Array = chart_data.get("items", [])
	var start_angle: float = -PI / 2

	for item in items:
		var percentage: float = item.get("percentage", 0.0) / 100.0
		var angle: float = percentage * 2 * PI
		var mid_angle: float = start_angle + angle / 2

		var label_distance: float = radius + 50.0
		var label_pos: Vector2 = center + Vector2(cos(mid_angle), sin(mid_angle)) * label_distance

		var candidate_name: String = item.get("candidate_name", "未知")
		var percent_text: String = "%.1f%%" % item.get("percentage", 0.0)
		var label_text: String = "%s\n%s" % [candidate_name, percent_text]

		draw_string(
			ThemeDB.fallback_font,
			label_pos,
			label_text,
			HORIZONTAL_ALIGNMENT_CENTER,
			-1,
			16,
			Color.WHITE
		)

		start_angle += angle

func _draw_bar_chart() -> void:
	if chart_data.is_empty():
		return

	var items: Array = chart_data.get("items", [])
	if items.is_empty():
		return

	var chart_width: float = size.x - 40.0
	var chart_height: float = size.y - 40.0
	var bar_spacing: float = 20.0

	# 计算柱子宽度
	var num_bars: int = items.size()
	var bar_width: float = (chart_width - (num_bars + 1) * bar_spacing) / num_bars
	bar_width = min(bar_width, 80.0)

	# 找到最大票数
	var max_bar_votes: int = 0
	for item in items:
		var votes: int = item.get("votes", 0)
		if votes > max_bar_votes:
			max_bar_votes = votes

	if max_bar_votes == 0:
		max_bar_votes = 1

	# 绘制柱子
	var x_offset: float = 20.0
	for item in items:
		var votes: int = item.get("votes", 0)
		var color_str: String = item.get("color", "#FF6B6B")
		var color: Color = Color(color_str)

		var bar_height: float = float(votes) / float(max_bar_votes) * (chart_height - 100.0)
		var bar_rect: Rect2 = Rect2(
			Vector2(x_offset, chart_height - bar_height - 20.0),
			Vector2(bar_width, bar_height)
		)

		draw_rect(bar_rect, color)

		_draw_bar_labels(x_offset, bar_width, chart_height, item)

		x_offset += bar_width + bar_spacing

func _draw_bar_labels(x_offset: float, bar_width: float, chart_height: float, item: Dictionary) -> void:
	# 绘制候选项名称（底部）
	var candidate_name: String = item.get("candidate_name", "未知")
	var name_pos: Vector2 = Vector2(x_offset + bar_width / 2, chart_height + 10.0)
	draw_string(
		ThemeDB.fallback_font,
		name_pos,
		candidate_name,
		HORIZONTAL_ALIGNMENT_CENTER,
		-1,
		14,
		Color.WHITE
	)

	# 绘制票数（顶部）
	var votes: int = item.get("votes", 0)
	var votes_text: String = str(votes)
	var votes_pos: Vector2 = Vector2(x_offset + bar_width / 2, chart_height - 30.0)
	draw_string(
		ThemeDB.fallback_font,
		votes_pos,
		votes_text,
		HORIZONTAL_ALIGNMENT_CENTER,
		-1,
		16,
		Color.WHITE
	)