extends Node

const WAR_PANEL_SCENE := "res://scenes/ui/social/GuildWarPanel.tscn"

func test_signals_declared() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	assert(panel.has_signal("close_pressed"))
	assert(panel.has_signal("war_selected"))
	panel.queue_free()

func test_initial_state() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	assert(panel._current_war_id == "")
	assert(panel._current_guild_id == "")
	assert(panel._current_mode == panel.WarMode.ACTIVE)
	panel.queue_free()

func test_set_guild_id() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel.set_guild_id("guild_001")
	assert(panel._current_guild_id == "guild_001")
	panel.queue_free()

func test_clear() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._current_war_id = "war_001"
	panel._current_guild_id = "guild_001"
	panel._current_mode = panel.WarMode.HISTORY

	panel.clear()

	assert(panel._current_war_id == "")
	assert(panel._current_mode == panel.WarMode.ACTIVE)
	assert(panel.war_list.get_item_count() == 0)
	assert(panel.scoreboard_list.get_item_count() == 0)
	assert(panel.war_title.text == "选择战争查看详情")
	assert(panel.war_status.text == "状态: --")
	assert(panel.war_type.text == "类型: --")
	assert(panel.war_score.text == "比分: 0 : 0")
	assert(panel.war_reward.text == "奖励: --")
	panel.queue_free()

func test_get_status_label() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	assert(panel._get_status_label("declared") == "已宣战")
	assert(panel._get_status_label("accepted") == "已接受")
	assert(panel._get_status_label("in_progress") == "进行中")
	assert(panel._get_status_label("completed") == "已完成")
	assert(panel._get_status_label("cancelled") == "已取消")
	assert(panel._get_status_label("unknown") == "未知")
	panel.queue_free()

func test_get_type_label() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	assert(panel._get_type_label("territory") == "领土战")
	assert(panel._get_type_label("resource") == "资源战")
	assert(panel._get_type_label("honor") == "荣誉战")
	assert(panel._get_type_label("unknown") == "未知")
	panel.queue_free()

func test_format_reward_empty() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	assert(panel._format_reward({}) == "无")
	panel.queue_free()

func test_format_reward_with_values() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	var reward: Dictionary = {
		"experience_points": 100,
		"gold": 50,
		"contribution_points": 20,
		"reputation": 10
	}
	var result: String = panel._format_reward(reward)
	assert(result.find("经验 100") != -1)
	assert(result.find("金币 50") != -1)
	assert(result.find("贡献 20") != -1)
	assert(result.find("声望 10") != -1)
	panel.queue_free()

func test_format_reward_partial() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	var reward: Dictionary = {"gold": 50}
	var result: String = panel._format_reward(reward)
	assert(result == "金币 50")
	panel.queue_free()

func test_update_action_buttons_declared() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._update_action_buttons("declared")
	assert(panel.accept_button.disabled == false)
	assert(panel.cancel_button.disabled == false)
	assert(panel.join_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_action_buttons_accepted() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._update_action_buttons("accepted")
	assert(panel.accept_button.disabled == true)
	assert(panel.cancel_button.disabled == false)
	assert(panel.join_button.disabled == false)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_action_buttons_in_progress() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._update_action_buttons("in_progress")
	assert(panel.accept_button.disabled == true)
	assert(panel.cancel_button.disabled == true)
	assert(panel.join_button.disabled == false)
	assert(panel.complete_button.disabled == false)
	panel.queue_free()

func test_update_action_buttons_completed() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._update_action_buttons("completed")
	assert(panel.accept_button.disabled == true)
	assert(panel.cancel_button.disabled == true)
	assert(panel.join_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_action_buttons_cancelled() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._update_action_buttons("cancelled")
	assert(panel.accept_button.disabled == true)
	assert(panel.cancel_button.disabled == true)
	assert(panel.join_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_action_buttons_unknown_status() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._update_action_buttons("unknown_status")
	assert(panel.accept_button.disabled == true)
	assert(panel.cancel_button.disabled == true)
	assert(panel.join_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_war_detail_empty() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._update_war_detail({})
	assert(panel.war_title.text == "选择战争查看详情")
	assert(panel.war_status.text == "状态: --")
	assert(panel.war_type.text == "类型: --")
	assert(panel.war_score.text == "比分: 0 : 0")
	assert(panel.war_reward.text == "奖励: --")
	assert(panel.accept_button.disabled == true)
	assert(panel.cancel_button.disabled == true)
	assert(panel.join_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_war_detail_with_data() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	var war: Dictionary = {
		"challenger_guild_id": "guild_A",
		"defender_guild_id": "guild_B",
		"status": "in_progress",
		"war_type": "territory",
		"challenger_score": 3,
		"defender_score": 2,
		"reward": {"gold": 100}
	}
	panel._update_war_detail(war)
	assert(panel.war_title.text == "guild_A vs guild_B")
	assert(panel.war_status.text == "状态: 进行中")
	assert(panel.war_type.text == "类型: 领土战")
	assert(panel.war_score.text == "比分: 3 : 2")
	assert(panel.war_reward.text == "奖励: 金币 100")
	assert(panel.join_button.disabled == false)
	assert(panel.complete_button.disabled == false)
	panel.queue_free()

func test_update_war_list() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	var wars: Array = [
		{
			"challenger_guild_id": "guild_A",
			"defender_guild_id": "guild_B",
			"status": "declared",
			"war_type": "territory"
		},
		{
			"challenger_guild_id": "guild_C",
			"defender_guild_id": "guild_D",
			"status": "in_progress",
			"war_type": "resource"
		}
	]
	panel._update_war_list(wars)
	assert(panel.war_list.get_item_count() == 2)
	panel.queue_free()

func test_update_war_list_empty() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._update_war_list([])
	assert(panel.war_list.get_item_count() == 0)
	panel.queue_free()

func test_update_scoreboard_empty() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	panel._update_scoreboard({})
	# 即使空记分板，也应输出两个分组标题
	assert(panel.scoreboard_list.get_item_count() == 2)
	panel.queue_free()

func test_update_scoreboard_with_participants() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	var scoreboard: Dictionary = {
		"challenger_participants": [
			{"player_id": "p_001", "kills": 5, "deaths": 2, "contribution_score": 100}
		],
		"defender_participants": [
			{"player_id": "p_002", "kills": 3, "deaths": 4, "contribution_score": 80}
		]
	}
	panel._update_scoreboard(scoreboard)
	# 2 个分组标题 + 2 个成员
	assert(panel.scoreboard_list.get_item_count() == 4)
	panel.queue_free()

func test_warmode_enum_values() -> void:
	var panel = load(WAR_PANEL_SCENE).instantiate()
	assert(panel.WarMode.ACTIVE == 0)
	assert(panel.WarMode.HISTORY == 1)
	panel.queue_free()
