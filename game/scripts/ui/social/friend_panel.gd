extends Control

signal close_pressed
signal friend_selected(friend_id: String)

@onready var friend_list: ItemList = $TabContainer/FriendsTab/VBoxContainer/FriendList
@onready var pending_list: ItemList = $TabContainer/FriendsTab/VBoxContainer/PendingList
@onready var friend_id_input: LineEdit = $TabContainer/FriendsTab/VBoxContainer/AddFriendBar/FriendIdInput
@onready var add_friend_button: Button = $TabContainer/FriendsTab/VBoxContainer/AddFriendBar/AddFriendButton
@onready var close_button: Button = $TabContainer/FriendsTab/VBoxContainer/CloseButton
@onready var collab_quest_panel: Control = $TabContainer/CollabTab/FriendCollabQuestPanel

func _ready() -> void:
	add_friend_button.pressed.connect(_on_add_friend_pressed)
	close_button.pressed.connect(_on_close_pressed)
	friend_list.item_selected.connect(_on_friend_item_selected)
	pending_list.item_selected.connect(_on_request_item_selected)
	FriendManager.friends_loaded.connect(_on_friends_loaded)
	FriendManager.friend_status_loaded.connect(_on_pending_loaded)

func _on_friends_loaded() -> void:
	update_friends_list(FriendManager._friends)

func _on_pending_loaded() -> void:
	update_pending_list(FriendManager._pending_requests)

func _on_add_friend_pressed() -> void:
	var friend_id: String = friend_id_input.text.strip_edges()
	if friend_id == "":
		return
	FriendManager.send_friend_request(friend_id)
	friend_id_input.clear()

func _on_close_pressed() -> void:
	close_pressed.emit()

func _on_friend_item_selected(index: int) -> void:
	var items: Array = FriendManager._friends
	if index >= 0 and index < items.size():
		var friend_id: String = items[index].get("player_id", "")
		friend_selected.emit(friend_id)

func _on_request_item_selected(index: int) -> void:
	var items: Array = FriendManager._pending_requests
	if index >= 0 and index < items.size():
		var player_id: String = items[index].get("player_id", "")
		FriendManager.accept_friend_request(player_id)

func update_friends_list(friends: Array) -> void:
	friend_list.clear()
	for friend in friends:
		var display_name: String = friend.get("display_name", friend.get("player_id", ""))
		var status: String = FriendManager.get_friend_status(friend.get("player_id", ""))
		var label: String = "%s [%s]" % [display_name, status]
		friend_list.add_item(label)

func update_pending_list(requests: Array) -> void:
	pending_list.clear()
	for request in requests:
		var display_name: String = request.get("display_name", request.get("player_id", ""))
		pending_list.add_item(display_name)

func refresh() -> void:
	FriendManager.fetch_friends()
	FriendManager.fetch_pending_requests()
	if collab_quest_panel:
		collab_quest_panel.refresh()
