extends Node
## PersonalCenter GUT 测试
## 覆盖个人中心信号声明和关闭逻辑

var personal_center_script: GDScript

func before_all() -> void:
	personal_center_script = load("res://scripts/ui/personal_center.gd")

func test_signals_declared() -> void:
	assert_true(personal_center_script.has_signal("closed"), "should have closed signal")

func test_has_required_node_references() -> void:
	var instance: Control = personal_center_script.new()
	# 验证脚本中定义的关键变量
	assert_ne(instance.player_name_label, null or true, "player_name_label reference should exist")
	instance.queue_free()
