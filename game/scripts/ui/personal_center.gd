extends Control

signal closed

@onready var player_name_label: Label = $MarginContainer/VBoxContainer/PlayerInfoPanel/InfoVBox/PlayerNameLabel
@onready var chapter_label: Label = $MarginContainer/VBoxContainer/PlayerInfoPanel/InfoVBox/ChapterLabel
@onready var contribution_label: Label = $MarginContainer/VBoxContainer/PlayerInfoPanel/InfoVBox/ContributionLabel
@onready var achievements_label: Label = $MarginContainer/VBoxContainer/PlayerInfoPanel/InfoVBox/AchievementsLabel
@onready var refresh_button: Button = $MarginContainer/VBoxContainer/RefreshButton
@onready var close_button: Button = $MarginContainer/VBoxContainer/Header/CloseButton
@onready var tab_container: TabContainer = $MarginContainer/VBoxContainer/TabContainer

# 投票记录标签页
@onready var vote_history_list: ItemList = $MarginContainer/VBoxContainer/TabContainer/投票记录/VoteHistoryList

# 贡献度标签页
@onready var contribution_points_label: Label = $MarginContainer/VBoxContainer/TabContainer/贡献度/ContributionPointsLabel
@onready var contribution_log_list: ItemList = $MarginContainer/VBoxContainer/TabContainer/贡献度/ContributionLogList

# 声望标签页
@onready var reputation_list: ItemList = $MarginContainer/VBoxContainer/TabContainer/声望/ReputationList

# 成就标签页
@onready var achievements_grid: GridContainer = $MarginContainer/VBoxContainer/TabContainer/成就/AchievementsGrid

func _ready() -> void:
	# 连接信号
	refresh_button.pressed.connect(_on_refresh_pressed)
	close_button.pressed.connect(_on_close_pressed)
	
	# 连接 PlayerManager 信号
	PlayerManager.profile_loaded.connect(_on_profile_loaded)
	PlayerManager.contribution_loaded.connect(_on_contribution_loaded)
	PlayerManager.player_reputation_loaded.connect(_on_reputation_loaded)
	PlayerManager.achievements_loaded.connect(_on_achievements_loaded)
	PlayerManager.loading_changed.connect(_on_loading_changed)
	
	# 连接 VoteManager 信号
	VoteManager.vote_history_loaded.connect(_on_vote_history_loaded)
	
	# 初始加载数据
	_load_all_data()

func _load_all_data() -> void:
	"""加载个人中心全部数据"""
	PlayerManager.refresh_profile()
	VoteManager.fetch_vote_history()

func _on_refresh_pressed() -> void:
	"""刷新按钮点击"""
	_load_all_data()

func _on_close_pressed() -> void:
	"""关闭按钮点击"""
	closed.emit()
	hide()

func _on_profile_loaded() -> void:
	"""玩家聚合信息加载完成"""
	var profile: Dictionary = PlayerManager.profile_data
	
	player_name_label.text = "玩家名称：%s" % profile.get("display_name", "未知")
	chapter_label.text = "当前章节：%s" % profile.get("chapter_id", "未知")
	contribution_label.text = "贡献度：%d" % profile.get("contribution_points", 0)
	
	var unlocked: int = profile.get("achievements_unlocked", 0)
	var total: int = profile.get("achievements_total", 0)
	achievements_label.text = "成就：%d / %d" % [unlocked, total]

func _on_contribution_loaded() -> void:
	"""贡献度数据加载完成"""
	var contribution: Dictionary = PlayerManager.contribution_data
	
	contribution_points_label.text = "当前贡献度：%d" % contribution.get("total_points", 0)
	
	# 显示贡献度流水
	contribution_log_list.clear()
	var logs: Array = contribution.get("logs", [])
	for log in logs:
		var source: String = log.get("source", "未知")
		var amount: int = log.get("amount", 0)
		var timestamp: String = log.get("created_at", "")
		contribution_log_list.add_item("%s | +%d | %s" % [source, amount, timestamp])

func _on_reputation_loaded() -> void:
	"""声望数据加载完成"""
	reputation_list.clear()
	var reputations: Array[Dictionary] = PlayerManager.get_reputation_summary()
	
	for rep in reputations:
		var region_id: String = rep.get("region_id", "未知")
		var reputation: int = rep.get("reputation", 0)
		var level: String = rep.get("reputation_level", "neutral")
		var level_info: Dictionary = PlayerManager.get_reputation_level_info(level)
		var level_name: String = level_info.get("name", level)
		
		reputation_list.add_item("%s | %d | %s" % [region_id, reputation, level_name])

func _on_achievements_loaded() -> void:
	"""成就数据加载完成"""
	# 清空现有成就节点
	for child in achievements_grid.get_children():
		child.queue_free()
	
	var achievements: Array[Dictionary] = PlayerManager.achievements_data
	
	for achievement in achievements:
		var achievement_panel: PanelContainer = PanelContainer.new()
		var vbox: VBoxContainer = VBoxContainer.new()
		
		var name_label: Label = Label.new()
		name_label.text = achievement.get("name", "未知成就")
		name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		
		var rarity_label: Label = Label.new()
		var rarity: String = achievement.get("rarity", "common")
		rarity_label.text = "稀有度：%s" % rarity
		
		var unlocked_label: Label = Label.new()
		var unlocked_at: String = achievement.get("unlocked_at", "")
		if unlocked_at != "":
			unlocked_label.text = "解锁时间：%s" % unlocked_at
		else:
			unlocked_label.text = "未解锁"
		
		vbox.add_child(name_label)
		vbox.add_child(rarity_label)
		vbox.add_child(unlocked_label)
		
		achievement_panel.add_child(vbox)
		achievements_grid.add_child(achievement_panel)

func _on_vote_history_loaded() -> void:
	"""投票历史加载完成"""
	vote_history_list.clear()
	var history: Array[Dictionary] = VoteManager.vote_history
	
	for record in history:
		var cycle_id: String = record.get("vote_cycle_id", "未知周期")
		var candidate_id: String = record.get("candidate_id", "未知候选")
		var weight: float = record.get("weight", 1.0)
		var created_at: String = record.get("created_at", "")
		
		vote_history_list.add_item("%s | %s | 权重 %.1f | %s" % [cycle_id, candidate_id, weight, created_at])

func _on_loading_changed(is_loading: bool) -> void:
	"""加载状态变化"""
	refresh_button.disabled = is_loading
	if is_loading:
		refresh_button.text = "加载中..."
	else:
		refresh_button.text = "刷新数据"

func show_personal_center() -> void:
	"""显示个人中心"""
	show()
	_load_all_data()