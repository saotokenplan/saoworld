extends Node

const AUCTION_PANEL_SCENE := "res://scenes/ui/economy/AuctionPanel.tscn"

func test_signals_declared() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	assert(panel.has_signal("close_pressed"))
	assert(panel.has_signal("listing_selected"))
	panel.queue_free()

func test_auction_status_names_constant() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	assert(panel.AUCTION_STATUS_NAMES.size() == 3)
	assert(panel.AUCTION_STATUS_NAMES.get("active", "") == "进行中")
	assert(panel.AUCTION_STATUS_NAMES.get("closed", "") == "已结束")
	assert(panel.AUCTION_STATUS_NAMES.get("cancelled", "") == "已取消")
	panel.queue_free()

func test_initial_state() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	assert(panel._auctions == [])
	assert(panel._selected_listing == {})
	assert(panel._current_category == "")
	panel.queue_free()

func test_refresh_auctions_display_empty() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	panel._auctions = []
	panel._refresh_auctions_display()
	assert(panel._auctions_list.get_item_count() == 0)
	assert(panel._empty_label.visible == true)
	assert(panel._loading_label.visible == false)
	assert(panel._auction_detail.visible == false)
	panel.queue_free()

func test_refresh_auctions_display_with_data() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	panel._auctions = [
		{
			"listing_id": "listing_001",
			"item_name": "铁剑",
			"item_key": "item_iron_sword",
			"quantity": 1,
			"starting_price": 100,
			"current_bid": 150,
			"buyout_price": 300,
			"status": "active",
			"seller_name": "player_A"
		},
		{
			"listing_id": "listing_002",
			"item_name": "",
			"item_key": "item_potion",
			"quantity": 5,
			"starting_price": 50,
			"current_bid": 60,
			"buyout_price": 100,
			"status": "closed",
			"seller_name": "player_B"
		}
	]
	panel._refresh_auctions_display()
	assert(panel._auctions_list.get_item_count() == 2)
	assert(panel._empty_label.visible == false)
	assert(panel._loading_label.visible == false)
	panel.queue_free()

func test_refresh_auctions_display_uses_item_key_when_name_empty() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	panel._auctions = [
		{
			"listing_id": "listing_001",
			"item_name": "",
			"item_key": "item_potion",
			"quantity": 1,
			"starting_price": 10,
			"current_bid": 15,
			"buyout_price": 30,
			"status": "active",
			"seller_name": "player_A"
		}
	]
	panel._refresh_auctions_display()
	assert(panel._auctions_list.get_item_count() == 1)
	var item_text: String = panel._auctions_list.get_item_text(0)
	assert(item_text.find("item_potion") != -1)
	panel.queue_free()

func test_refresh_auction_detail_active() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	panel._selected_listing = {
		"item_name": "铁剑",
		"item_key": "item_iron_sword",
		"quantity": 1,
		"starting_price": 100,
		"current_bid": 150,
		"buyout_price": 300,
		"status": "active",
		"seller_name": "player_A",
		"end_time": "2026-07-20"
	}
	panel._refresh_auction_detail()
	assert(panel._auction_detail.visible == true)
	assert(panel._bid_button.visible == true)
	assert(panel._buyout_button.visible == true)
	panel.queue_free()

func test_refresh_auction_detail_active_no_buyout() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	panel._selected_listing = {
		"item_name": "铁剑",
		"item_key": "item_iron_sword",
		"quantity": 1,
		"starting_price": 100,
		"current_bid": 150,
		"buyout_price": 0,
		"status": "active",
		"seller_name": "player_A",
		"end_time": ""
	}
	panel._refresh_auction_detail()
	assert(panel._auction_detail.visible == true)
	assert(panel._bid_button.visible == true)
	# buyout_price 为 0 时一口价按钮应隐藏
	assert(panel._buyout_button.visible == false)
	panel.queue_free()

func test_refresh_auction_detail_closed() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	panel._selected_listing = {
		"item_name": "铁剑",
		"item_key": "item_iron_sword",
		"quantity": 1,
		"starting_price": 100,
		"current_bid": 300,
		"buyout_price": 300,
		"status": "closed",
		"seller_name": "player_A",
		"end_time": "2026-07-18"
	}
	panel._refresh_auction_detail()
	assert(panel._auction_detail.visible == true)
	# 已结束的拍卖不应显示竞价和一口价按钮
	assert(panel._bid_button.visible == false)
	assert(panel._buyout_button.visible == false)
	panel.queue_free()

func test_refresh_auction_detail_status_text() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	panel._selected_listing = {
		"item_name": "铁剑",
		"item_key": "item_iron_sword",
		"quantity": 2,
		"starting_price": 100,
		"current_bid": 150,
		"buyout_price": 300,
		"status": "active",
		"seller_name": "player_A",
		"end_time": "2026-07-20"
	}
	panel._refresh_auction_detail()
	var detail_text: String = panel._detail_label.text
	assert(detail_text.find("状态: 进行中") != -1)
	assert(detail_text.find("物品: 铁剑") != -1)
	assert(detail_text.find("数量: 2") != -1)
	assert(detail_text.find("起拍价: 100") != -1)
	assert(detail_text.find("当前价: 150") != -1)
	assert(detail_text.find("一口价: 300") != -1)
	assert(detail_text.find("卖家: player_A") != -1)
	assert(detail_text.find("结束时间: 2026-07-20") != -1)
	panel.queue_free()

func test_on_auction_error() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	panel._on_auction_error("AUCTION_NOT_FOUND", "拍卖未找到")
	assert(panel._loading_label.visible == false)
	assert(panel._empty_label.visible == true)
	assert(panel._empty_label.text == "加载失败: 拍卖未找到")
	panel.queue_free()

func test_clear() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	panel._auctions = [{"listing_id": "l1"}]
	panel._selected_listing = {"listing_id": "l2"}
	panel._current_category = "weapon"

	panel.clear()

	assert(panel._auctions == [])
	assert(panel._selected_listing == {})
	assert(panel._auctions_list.get_item_count() == 0)
	assert(panel._auction_detail.visible == false)
	assert(panel._empty_label.visible == false)
	assert(panel._loading_label.visible == true)
	panel.queue_free()

func test_close_pressed_signal_emission() -> void:
	var panel = load(AUCTION_PANEL_SCENE).instantiate()
	var signal_emitted: bool = false
	var conn = panel.close_pressed.connect(func():
		signal_emitted = true
	)
	panel._on_close_pressed()
	conn.disconnect()
	assert(signal_emitted == true)
	panel.queue_free()
