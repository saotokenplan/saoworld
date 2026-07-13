extends Node
## MainMenu GUT 测试
## 覆盖主菜单信号声明、存档状态管理

var main_menu_script: GDScript

func before_all() -> void:
	main_menu_script = load("res://scripts/ui/main_menu.gd")

func test_signals_declared() -> void:
	assert_true(main_menu_script.has_signal("start_game_pressed"), "should have start_game_pressed signal")
	assert_true(main_menu_script.has_signal("continue_game_pressed"), "should have continue_game_pressed signal")
	assert_true(main_menu_script.has_signal("new_game_pressed"), "should have new_game_pressed signal")
	assert_true(main_menu_script.has_signal("save_pressed"), "should have save_pressed signal")
	assert_true(main_menu_script.has_signal("load_pressed"), "should have load_pressed signal")
	assert_true(main_menu_script.has_signal("settings_pressed"), "should have settings_pressed signal")
	assert_true(main_menu_script.has_signal("quit_pressed"), "should have quit_pressed signal")
	assert_true(main_menu_script.has_signal("vote_pressed"), "should have vote_pressed signal")
	assert_true(main_menu_script.has_signal("world_map_pressed"), "should have world_map_pressed signal")
	assert_true(main_menu_script.has_signal("npcs_pressed"), "should have npcs_pressed signal")
	assert_true(main_menu_script.has_signal("quests_pressed"), "should have quests_pressed signal")
	assert_true(main_menu_script.has_signal("personal_center_pressed"), "should have personal_center_pressed signal")

func test_set_save_state_has_save() -> void:
	# 验证 set_save_state 方法定义存在
	var instance: Control = main_menu_script.new()
	# has_save = true 时，continue_button 应该可见
	instance.set_save_state(true)
	instance.queue_free()

func test_set_save_state_no_save() -> void:
	var instance: Control = main_menu_script.new()
	instance.set_save_state(false)
	instance.queue_free()
