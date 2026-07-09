extends "res://tests/test_base.gd"

func test_quest_tracker_signals() -> void:
	var tracker: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_tracker.gd")
	tracker.set_script(script)
	
	assert_true(tracker.has_signal("quest_clicked"))
	assert_true(tracker.has_signal("open_quest_panel"))

func test_quest_tracker_initial_state() -> void:
	var tracker: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_tracker.gd")
	tracker.set_script(script)
	
	assert_false(tracker.is_minimized)
	assert_eq(tracker.max_displayed, 3)

func test_quest_tracker_toggle_minimize() -> void:
	var tracker: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_tracker.gd")
	tracker.set_script(script)
	
	assert_false(tracker.is_minimized)
	tracker._toggle_minimize()
	assert_true(tracker.is_minimized)
	tracker._toggle_minimize()
	assert_false(tracker.is_minimized)

func test_quest_tracker_set_max_displayed() -> void:
	var tracker: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_tracker.gd")
	tracker.set_script(script)
	
	assert_eq(tracker.max_displayed, 3)
	tracker.set_max_displayed(5)
	assert_eq(tracker.max_displayed, 5)

func test_quest_tracker_get_active_quest_count() -> void:
	var tracker: PanelContainer = PanelContainer.new()
	var script: GDScript = load("res://scripts/ui/quest_tracker.gd")
	tracker.set_script(script)
	
	var count: int = tracker.get_active_quest_count()
	assert_true(count >= 0, "活跃任务数应大于等于0")
