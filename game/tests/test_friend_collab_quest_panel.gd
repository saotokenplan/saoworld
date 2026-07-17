extends Node

const COLLAB_PANEL_SCENE := "res://scenes/ui/social/FriendCollabQuestPanel.tscn"

func test_signals_declared() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	assert(panel.has_signal("close_pressed"))
	assert(panel.has_signal("quest_selected"))
	panel.queue_free()

func test_initial_state() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	assert(panel._current_quest_id == "")
	assert(panel._current_mode == panel.QuestMode.ACTIVE)
	panel.queue_free()

func test_questmode_enum_values() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	assert(panel.QuestMode.ACTIVE == 0)
	assert(panel.QuestMode.PENDING == 1)
	assert(panel.QuestMode.HISTORY == 2)
	panel.queue_free()

func test_clear() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._current_quest_id = "quest_001"
	panel._current_mode = panel.QuestMode.HISTORY

	panel.clear()

	assert(panel._current_quest_id == "")
	assert(panel._current_mode == panel.QuestMode.ACTIVE)
	assert(panel.quest_list.get_item_count() == 0)
	assert(panel.quest_title.text == "选择任务查看详情")
	assert(panel.quest_type.text == "类型: --")
	assert(panel.quest_status.text == "状态: --")
	assert(panel.quest_description.text == "")
	assert(panel.quest_progress.text == "进度: --")
	assert(panel.quest_rewards.text == "奖励: --")
	assert(panel.friend_id_input.text == "")
	assert(panel.title_input.text == "")
	assert(panel.type_input.text == "")
	assert(panel.desc_input.text == "")
	panel.queue_free()

func test_get_type_label() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	assert(panel._get_type_label("hunt") == "狩猎")
	assert(panel._get_type_label("explore") == "探索")
	assert(panel._get_type_label("collect") == "采集")
	assert(panel._get_type_label("escort") == "护送")
	assert(panel._get_type_label("challenge") == "挑战")
	assert(panel._get_type_label("unknown") == "未知")
	panel.queue_free()

func test_get_status_label() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	assert(panel._get_status_label("pending_invite") == "待接受")
	assert(panel._get_status_label("active") == "进行中")
	assert(panel._get_status_label("completed") == "已完成")
	assert(panel._get_status_label("failed") == "失败")
	assert(panel._get_status_label("expired") == "已过期")
	assert(panel._get_status_label("unknown") == "未知")
	panel.queue_free()

func test_format_progress_empty() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	assert(panel._format_progress({}) == "--")
	panel.queue_free()

func test_format_progress_with_values() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	var progress: Dictionary = {"current": 5, "target": 10}
	var result: String = panel._format_progress(progress)
	assert(result.find("current: 5") != -1)
	assert(result.find("target: 10") != -1)
	panel.queue_free()

func test_format_rewards_empty() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	assert(panel._format_rewards({}) == "无")
	panel.queue_free()

func test_format_rewards_with_values() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	var rewards: Dictionary = {
		"experience_points": 100,
		"gold": 50,
		"contribution_points": 20,
		"reputation": 10
	}
	var result: String = panel._format_rewards(rewards)
	assert(result.find("经验 100") != -1)
	assert(result.find("金币 50") != -1)
	assert(result.find("贡献 20") != -1)
	assert(result.find("声望 10") != -1)
	panel.queue_free()

func test_format_rewards_partial() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	var rewards: Dictionary = {"gold": 50}
	var result: String = panel._format_rewards(rewards)
	assert(result == "金币 50")
	panel.queue_free()

func test_update_action_buttons_pending_invite() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._update_action_buttons("pending_invite")
	assert(panel.accept_button.disabled == false)
	assert(panel.reject_button.disabled == false)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_action_buttons_active() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._update_action_buttons("active")
	assert(panel.accept_button.disabled == true)
	assert(panel.reject_button.disabled == true)
	assert(panel.complete_button.disabled == false)
	panel.queue_free()

func test_update_action_buttons_completed() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._update_action_buttons("completed")
	assert(panel.accept_button.disabled == true)
	assert(panel.reject_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_action_buttons_failed() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._update_action_buttons("failed")
	assert(panel.accept_button.disabled == true)
	assert(panel.reject_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_action_buttons_expired() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._update_action_buttons("expired")
	assert(panel.accept_button.disabled == true)
	assert(panel.reject_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_action_buttons_unknown_status() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._update_action_buttons("unknown_status")
	assert(panel.accept_button.disabled == true)
	assert(panel.reject_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_quest_detail_empty() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._update_quest_detail({})
	assert(panel.quest_title.text == "选择任务查看详情")
	assert(panel.quest_type.text == "类型: --")
	assert(panel.quest_status.text == "状态: --")
	assert(panel.quest_description.text == "")
	assert(panel.quest_progress.text == "进度: --")
	assert(panel.quest_rewards.text == "奖励: --")
	assert(panel.accept_button.disabled == true)
	assert(panel.reject_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()

func test_update_quest_detail_with_data() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	var quest: Dictionary = {
		"title": "狩猎巨龙",
		"quest_type": "hunt",
		"status": "active",
		"description": "与好友一起击败巨龙",
		"progress": {"current": 5, "target": 10},
		"rewards": {"gold": 100, "experience_points": 200}
	}
	panel._update_quest_detail(quest)
	assert(panel.quest_title.text == "狩猎巨龙")
	assert(panel.quest_type.text == "类型: 狩猎")
	assert(panel.quest_status.text == "状态: 进行中")
	assert(panel.quest_description.text == "与好友一起击败巨龙")
	assert(panel.quest_progress.text.find("current: 5") != -1)
	assert(panel.quest_rewards.text.find("金币 100") != -1)
	assert(panel.quest_rewards.text.find("经验 200") != -1)
	assert(panel.complete_button.disabled == false)
	panel.queue_free()

func test_update_quest_list() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	var quests: Array = [
		{"title": "任务A", "quest_type": "hunt", "status": "active"},
		{"title": "任务B", "quest_type": "explore", "status": "pending_invite"},
		{"title": "任务C", "quest_type": "collect", "status": "completed"}
	]
	panel._update_quest_list(quests)
	assert(panel.quest_list.get_item_count() == 3)
	panel.queue_free()

func test_update_quest_list_empty() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._update_quest_list([])
	assert(panel.quest_list.get_item_count() == 0)
	panel.queue_free()

func test_clear_detail_helper() -> void:
	var panel = load(COLLAB_PANEL_SCENE).instantiate()
	panel._clear_detail()
	assert(panel.quest_title.text == "选择任务查看详情")
	assert(panel.quest_type.text == "类型: --")
	assert(panel.quest_status.text == "状态: --")
	assert(panel.quest_description.text == "")
	assert(panel.quest_progress.text == "进度: --")
	assert(panel.quest_rewards.text == "奖励: --")
	assert(panel.accept_button.disabled == true)
	assert(panel.reject_button.disabled == true)
	assert(panel.complete_button.disabled == true)
	panel.queue_free()
