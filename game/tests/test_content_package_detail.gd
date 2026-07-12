extends "res://addons/gut/test.gd"
## ContentPackageDetail 单元测试
## 覆盖 S4-01 投票结果落地展示的内容包详情弹窗逻辑

const SCRIPT_PATH: String = "res://scripts/ui/content_package_detail.gd"

func _make_detail() -> Control:
	var node: Control = Control.new()
	var script: GDScript = load(SCRIPT_PATH)
	node.set_script(script)
	return node

func test_script_loads() -> void:
	var script: GDScript = load(SCRIPT_PATH)
	assert_true(script != null, "content_package_detail.gd 脚本应能加载")

func test_has_closed_signal() -> void:
	var detail: Control = _make_detail()
	assert_true(detail.has_signal("closed"), "应暴露 closed 信号")
	detail.queue_free()

func test_initial_package_data_empty() -> void:
	var detail: Control = _make_detail()
	assert_eq(detail.package_data, {}, "初始 package_data 应为空字典")
	detail.queue_free()

func test_get_status_text_all_statuses() -> void:
	var detail: Control = _make_detail()
	assert_eq(detail._get_status_text("packaged"), "已打包", "packaged 应映射为 已打包")
	assert_eq(detail._get_status_text("gray"), "灰度中", "gray 应映射为 灰度中")
	assert_eq(detail._get_status_text("live"), "已上线", "live 应映射为 已上线")
	assert_eq(detail._get_status_text("archived"), "已归档", "archived 应映射为 已归档")
	assert_eq(detail._get_status_text("rolled_back"), "已回滚", "rolled_back 应映射为 已回滚")
	detail.queue_free()

func test_get_status_text_unknown_status() -> void:
	var detail: Control = _make_detail()
	assert_eq(detail._get_status_text("unknown"), "unknown", "未知状态应原样返回")
	assert_eq(detail._get_status_text(""), "", "空字符串应原样返回")
	detail.queue_free()

func test_get_status_color_returns_color() -> void:
	var detail: Control = _make_detail()
	var expected_statuses: Array[String] = ["packaged", "gray", "live", "archived", "rolled_back"]
	for status in expected_statuses:
		var color: Color = detail._get_status_color(status)
		assert_true(typeof(color) == TYPE_COLOR, "状态 %s 应返回 Color 类型" % status)
	detail.queue_free()

func test_get_status_color_distinct_for_live_and_rolled_back() -> void:
	var detail: Control = _make_detail()
	var live_color: Color = detail._get_status_color("live")
	var rolled_back_color: Color = detail._get_status_color("rolled_back")
	assert_neq(live_color, rolled_back_color, "live 与 rolled_back 颜色应不同")
	detail.queue_free()

func test_get_status_color_unknown_returns_default() -> void:
	var detail: Control = _make_detail()
	var unknown_color: Color = detail._get_status_color("unknown")
	var default_color: Color = Color(0.8, 0.8, 0.8)
	assert_eq(unknown_color, default_color, "未知状态应返回默认灰色")
	detail.queue_free()

func test_hide_clears_package_data() -> void:
	var detail: Control = _make_detail()
	detail.package_data = {"package_version": "pkg_test_001"}
	detail.hide()
	assert_eq(detail.package_data, {}, "hide 后 package_data 应被清空")
	detail.queue_free()
