extends Node

func test_signals_declared() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	assert(panel.has_signal("close_pressed"))
	assert(panel.has_signal("quest_selected"))
	panel.queue_free()

func test_initial_state() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	assert(panel._current_quest_key == "")
	assert(panel._current_guild_id == "")
	assert(panel.action_button.disabled == true)
	panel.queue_free()

func test_clear() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	panel._current_quest_key = "q1"
	panel._current_guild_id = "g1"
	panel.action_button.disabled = false

	panel.clear()

	assert(panel._current_quest_key == "")
	assert(panel._current_guild_id == "")
	assert(panel.action_button.disabled == true)
	panel.queue_free()

func test_get_type_label() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	assert(panel._get_type_label("collect") == "采集")
	assert(panel._get_type_label("kill") == "击杀")
	assert(panel._get_type_label("deliver") == "运送")
	assert(panel._get_type_label("explore") == "探索")
	assert(panel._get_type_label("defend") == "防御")
	assert(panel._get_type_label("craft") == "制作")
	assert(panel._get_type_label("unknown") == "未知")
	panel.queue_free()

func test_get_status_label() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	assert(panel._get_status_label("active") == "进行中")
	assert(panel._get_status_label("completed") == "已完成")
	assert(panel._get_status_label("failed") == "失败")
	assert(panel._get_status_label("expired") == "已过期")
	assert(panel._get_status_label("unknown") == "未知")
	panel.queue_free()

func test_update_action_button_completed() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	panel._update_action_button("completed", {})
	assert(panel.action_button.text == "领取奖励")
	assert(panel.action_button.disabled == false)
	panel.queue_free()

func test_update_action_button_active_in_progress() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	panel._update_action_button("active", {"current": 50, "target_count": 100})
	assert(panel.action_button.text == "进行中...")
	assert(panel.action_button.disabled == true)
	panel.queue_free()

func test_update_action_button_active_completed() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	panel._update_action_button("active", {"current": 100, "target_count": 100})
	assert(panel.action_button.text == "完成任务")
	assert(panel.action_button.disabled == false)
	panel.queue_free()

func test_update_action_button_other() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	panel._update_action_button("pending", {})
	assert(panel.action_button.text == "未开始")
	assert(panel.action_button.disabled == true)
	panel.queue_free()

func test_update_reward_display() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	var rewards: Dictionary = {
		"experience_points": 100,
		"gold": 50,
		"contribution_points": 20
	}
	panel._update_reward_display(rewards)
	assert(panel.reward_label.text.find("经验 100") != -1)
	assert(panel.reward_label.text.find("金币 50") != -1)
	assert(panel.reward_label.text.find("贡献 20") != -1)
	panel.queue_free()

func test_update_progress_display() -> void:
	var panel = load("res://scenes/ui/social/GuildQuestPanel.tscn").instantiate()
	var progress: Dictionary = {"current": 50}
	var quest: Dictionary = {"target_count": 100}
	panel._update_progress_display(progress, quest)
	assert(panel.progress_bar.value == 50)
	assert(panel.progress_label.text == "进度: 50/100")
	panel.queue_free()