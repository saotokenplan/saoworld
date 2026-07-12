extends Control
## 投票讨论区面板脚本

signal back_pressed
signal view_content_pressed(content_package_id: String)

@onready var back_button: Button = $TopBar/BackButton
@onready var title_label: Label = $TopBar/TitleLabel
@onready var sort_tabs: TabContainer = $TopBar/SortTabs
@onready var discussions_scroll: ScrollContainer = $Content/DiscussionsScroll
@onready var discussions_container: VBoxContainer = $Content/DiscussionsScroll/DiscussionsContainer
@onready var new_discussion_input: TextEdit = $Content/NewDiscussionPanel/Input
@onready var submit_discussion_button: Button = $Content/NewDiscussionPanel/SubmitButton
@onready var status_label: Label = $Content/StatusLabel
@onready var reply_panel: Control = $ReplyPanel
@onready var reply_back_button: Button = $ReplyPanel/TopBar/BackButton
@onready var reply_discussion_title: Label = $ReplyPanel/TopBar/DiscussionTitle
@onready var replies_scroll: ScrollContainer = $ReplyPanel/Content/RepliesScroll
@onready var replies_container: VBoxContainer = $ReplyPanel/Content/RepliesScroll/RepliesContainer
@onready var new_reply_input: TextEdit = $ReplyPanel/NewReplyPanel/Input
@onready var submit_reply_button: Button = $ReplyPanel/NewReplyPanel/SubmitButton
@onready var reply_status_label: Label = $ReplyPanel/Content/StatusLabel

var vote_cycle_id: String = ""
var current_sort: String = "time"
var discussion_items: Array[Control] = []
var reply_items: Array[Control] = []
var current_discussion_id: String = ""
var is_loading: bool = false

func _ready() -> void:
	back_button.pressed.connect(_on_back_pressed)
	reply_back_button.pressed.connect(_on_reply_back_pressed)
	submit_discussion_button.pressed.connect(_on_submit_discussion)
	submit_reply_button.pressed.connect(_on_submit_reply)
	sort_tabs.tab_changed.connect(_on_sort_tab_changed)
	
	VoteManager.discussions_loaded.connect(_on_discussions_loaded)
	VoteManager.discussion_created.connect(_on_discussion_created)
	VoteManager.replies_loaded.connect(_on_replies_loaded)
	VoteManager.reply_created.connect(_on_reply_created)
	VoteManager.discussion_like_changed.connect(_on_discussion_like_changed)
	VoteManager.vote_error.connect(_on_vote_error)
	VoteManager.loading_changed.connect(_on_loading_changed)
	
	back_button.text = "返回"
	submit_discussion_button.text = "发布讨论"
	submit_reply_button.text = "发布回复"
	status_label.text = "加载中..."
	reply_status_label.text = "加载中..."
	reply_panel.visible = false

func set_vote_cycle(cycle_id: String, cycle_title: String = "") -> void:
	vote_cycle_id = cycle_id
	title_label.text = "讨论区 - %s" % cycle_title if cycle_title != "" else "讨论区"
	refresh_discussions()

func refresh_discussions() -> void:
	if vote_cycle_id == "":
		return
	status_label.text = "加载中..."
	VoteManager.fetch_discussions(vote_cycle_id, current_sort)

func _on_sort_tab_changed(tab_index: int) -> void:
	match tab_index:
		0: current_sort = "time"
		1: current_sort = "hot"
	refresh_discussions()

func _clear_discussions() -> void:
	for item in discussion_items:
		if is_instance_valid(item):
			item.queue_free()
	discussion_items.clear()

func _on_discussions_loaded(discussions: Array, meta: Dictionary) -> void:
	_clear_discussions()
	if discussions.size() == 0:
		status_label.text = "暂无讨论，快来发表第一条讨论吧！"
		return
	status_label.text = ""
	for discussion in discussions:
		_add_discussion_item(discussion)

func _add_discussion_item(discussion: Dictionary) -> void:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(0, 80)
	
	var vbox := VBoxContainer.new()
	vbox.theme_override_constants.separation = 5
	vbox.add_theme_constant_override("separation", 5)
	
	var header := HBoxContainer.new()
	header.theme_override_constants.separation = 10
	
	var player_label := Label.new()
	player_label.text = "玩家 %s" % discussion.get("player_id", "unknown")[0:8]
	player_label.theme_override_font_sizes.font_size = 12
	player_label.modulate = Color(0.7, 0.7, 0.8)
	
	var time_label := Label.new()
	time_label.text = discussion.get("created_at", "")
	time_label.theme_override_font_sizes.font_size = 11
	time_label.modulate = Color(0.6, 0.6, 0.7)
	time_label.size_flags_horizontal = 3
	
	header.add_child(player_label)
	header.add_child(time_label)
	
	var content_label := Label.new()
	content_label.text = discussion.get("content", "")
	content_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content_label.theme_override_font_sizes.font_size = 14
	
	var footer := HBoxContainer.new()
	footer.theme_override_constants.separation = 15
	
	var like_button := Button.new()
	var discussion_id: String = discussion.get("discussion_id", "")
	var like_count: int = discussion.get("like_count", 0)
	like_button.text = "👍 %d" % like_count
	like_button.toggle_mode = true
	like_button.theme_override_font_sizes.font_size = 12
	like_button.pressed.connect(func(): _on_like_discussion(discussion_id, like_button))
	
	var reply_button := Button.new()
	reply_button.text = "💬 %d 回复" % discussion.get("reply_count", 0)
	reply_button.theme_override_font_sizes.font_size = 12
	reply_button.pressed.connect(func(): _on_view_replies(discussion))
	
	footer.add_child(like_button)
	footer.add_child(reply_button)
	
	vbox.add_child(header)
	vbox.add_child(content_label)
	vbox.add_child(footer)
	
	panel.add_child(vbox)
	discussions_container.add_child(panel)
	discussion_items.append(panel)

func _on_submit_discussion() -> void:
	var content: String = new_discussion_input.text.strip_edges()
	if content == "":
		status_label.text = "请输入讨论内容"
		return
	if content.length() > 500:
		status_label.text = "讨论内容不能超过500字"
		return
	submit_discussion_button.disabled = true
	status_label.text = "发布中..."
	VoteManager.create_discussion(vote_cycle_id, content)

func _on_discussion_created(discussion: Dictionary) -> void:
	new_discussion_input.text = ""
	submit_discussion_button.disabled = false
	status_label.text = "发布成功！"
	refresh_discussions()

func _on_like_discussion(discussion_id: String, button: Button) -> void:
	if button.button_pressed:
		VoteManager.like_discussion(discussion_id)
	else:
		VoteManager.unlike_discussion(discussion_id)

func _on_discussion_like_changed(discussion_id: String, liked: bool, like_count: int) -> void:
	pass

func _on_view_replies(discussion: Dictionary) -> void:
	current_discussion_id = discussion.get("discussion_id", "")
	reply_discussion_title.text = discussion.get("content", "")[0:50] + "..." if discussion.get("content", "").length() > 50 else discussion.get("content", "")
	reply_panel.visible = true
	reply_status_label.text = "加载中..."
	VoteManager.fetch_replies(current_discussion_id)

func _on_reply_back_pressed() -> void:
	reply_panel.visible = false
	current_discussion_id = ""

func _clear_replies() -> void:
	for item in reply_items:
		if is_instance_valid(item):
			item.queue_free()
	reply_items.clear()

func _on_replies_loaded(discussion_id: String, replies: Array, meta: Dictionary) -> void:
	_clear_replies()
	if replies.size() == 0:
		reply_status_label.text = "暂无回复，快来发表第一条回复吧！"
		return
	reply_status_label.text = ""
	for reply in replies:
		_add_reply_item(reply)

func _add_reply_item(reply: Dictionary) -> void:
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(0, 60)
	
	var vbox := VBoxContainer.new()
	vbox.theme_override_constants.separation = 3
	vbox.add_theme_constant_override("separation", 3)
	
	var header := HBoxContainer.new()
	header.theme_override_constants.separation = 10
	
	var player_label := Label.new()
	player_label.text = "玩家 %s" % reply.get("player_id", "unknown")[0:8]
	player_label.theme_override_font_sizes.font_size = 11
	player_label.modulate = Color(0.7, 0.7, 0.8)
	
	var time_label := Label.new()
	time_label.text = reply.get("created_at", "")
	time_label.theme_override_font_sizes.font_size = 10
	time_label.modulate = Color(0.6, 0.6, 0.7)
	time_label.size_flags_horizontal = 3
	
	header.add_child(player_label)
	header.add_child(time_label)
	
	var content_label := Label.new()
	content_label.text = reply.get("content", "")
	content_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content_label.theme_override_font_sizes.font_size = 13
	
	var footer := HBoxContainer.new()
	footer.theme_override_constants.separation = 10
	
	var like_button := Button.new()
	var reply_id: String = reply.get("reply_id", "")
	var like_count: int = reply.get("like_count", 0)
	like_button.text = "👍 %d" % like_count
	like_button.toggle_mode = true
	like_button.theme_override_font_sizes.font_size = 11
	like_button.pressed.connect(func(): _on_like_reply(reply_id, like_button))
	
	footer.add_child(like_button)
	
	vbox.add_child(header)
	vbox.add_child(content_label)
	vbox.add_child(footer)
	
	panel.add_child(vbox)
	replies_container.add_child(panel)
	reply_items.append(panel)

func _on_submit_reply() -> void:
	var content: String = new_reply_input.text.strip_edges()
	if content == "":
		reply_status_label.text = "请输入回复内容"
		return
	if content.length() > 500:
		reply_status_label.text = "回复内容不能超过500字"
		return
	submit_reply_button.disabled = true
	reply_status_label.text = "发布中..."
	VoteManager.create_reply(current_discussion_id, content)

func _on_reply_created(reply: Dictionary) -> void:
	new_reply_input.text = ""
	submit_reply_button.disabled = false
	reply_status_label.text = "发布成功！"
	VoteManager.fetch_replies(current_discussion_id)

func _on_like_reply(reply_id: String, button: Button) -> void:
	if button.button_pressed:
		VoteManager.like_reply(reply_id)
	else:
		VoteManager.unlike_reply(reply_id)

func _on_vote_error(error_code: String, message: String) -> void:
	status_label.text = "错误：%s" % message
	submit_discussion_button.disabled = false
	submit_reply_button.disabled = false

func _on_loading_changed(loading: bool) -> void:
	is_loading = loading

func _on_back_pressed() -> void:
	back_pressed.emit()
