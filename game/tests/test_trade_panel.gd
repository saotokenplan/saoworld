extends Node

const TRADE_PANEL_SCENE := "res://scenes/ui/economy/TradePanel.tscn"

func test_signals_declared() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	assert(panel.has_signal("close_pressed"))
	assert(panel.has_signal("trade_selected"))
	panel.queue_free()

func test_status_names_constant() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	assert(panel.STATUS_NAMES.size() == 5)
	assert(panel.STATUS_NAMES.get("all", "") == "全部")
	assert(panel.STATUS_NAMES.get("pending", "") == "待处理")
	assert(panel.STATUS_NAMES.get("sent", "") == "已发出")
	assert(panel.STATUS_NAMES.get("completed", "") == "已完成")
	assert(panel.STATUS_NAMES.get("cancelled", "") == "已取消")
	panel.queue_free()

func test_trade_status_names_constant() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	assert(panel.TRADE_STATUS_NAMES.size() == 4)
	assert(panel.TRADE_STATUS_NAMES.get("pending", "") == "待处理")
	assert(panel.TRADE_STATUS_NAMES.get("sent", "") == "已发出")
	assert(panel.TRADE_STATUS_NAMES.get("completed", "") == "已完成")
	assert(panel.TRADE_STATUS_NAMES.get("cancelled", "") == "已取消")
	panel.queue_free()

func test_initial_state() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	assert(panel._trades == [])
	assert(panel._selected_trade == {})
	assert(panel._current_status == "all")
	panel.queue_free()

func test_refresh_trades_display_empty() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	panel._trades = []
	panel._refresh_trades_display()
	assert(panel._trades_list.get_item_count() == 0)
	assert(panel._empty_label.visible == true)
	assert(panel._loading_label.visible == false)
	assert(panel._trade_detail.visible == false)
	panel.queue_free()

func test_refresh_trades_display_with_data() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	panel._trades = [
		{
			"trade_id": "trade_001",
			"status": "pending",
			"offer_coins": 100,
			"offer_items": [{"item_key": "item_001"}],
			"recipient_name": "player_A",
			"sender_name": "player_B"
		},
		{
			"trade_id": "trade_002",
			"status": "completed",
			"offer_coins": 200,
			"offer_items": [],
			"recipient_name": "player_C",
			"sender_name": "player_D"
		}
	]
	panel._refresh_trades_display()
	assert(panel._trades_list.get_item_count() == 2)
	assert(panel._empty_label.visible == false)
	assert(panel._loading_label.visible == false)
	panel.queue_free()

func test_refresh_trade_detail_pending() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	panel._selected_trade = {
		"status": "pending",
		"offer_coins": 100,
		"request_coins": 50,
		"recipient_name": "player_A",
		"sender_name": "player_B",
		"created_at": "2026-07-18"
	}
	panel._refresh_trade_detail()
	assert(panel._trade_detail.visible == true)
	assert(panel._accept_button.visible == true)
	assert(panel._reject_button.visible == true)
	assert(panel._cancel_button.visible == false)
	panel.queue_free()

func test_refresh_trade_detail_sent() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	panel._selected_trade = {
		"status": "sent",
		"offer_coins": 100,
		"request_coins": 50,
		"recipient_name": "player_A",
		"sender_name": "player_B",
		"created_at": ""
	}
	panel._refresh_trade_detail()
	assert(panel._trade_detail.visible == true)
	assert(panel._accept_button.visible == false)
	assert(panel._reject_button.visible == false)
	assert(panel._cancel_button.visible == true)
	panel.queue_free()

func test_refresh_trade_detail_completed() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	panel._selected_trade = {
		"status": "completed",
		"offer_coins": 100,
		"request_coins": 50,
		"recipient_name": "player_A",
		"sender_name": "player_B",
		"created_at": ""
	}
	panel._refresh_trade_detail()
	assert(panel._trade_detail.visible == true)
	assert(panel._accept_button.visible == false)
	assert(panel._reject_button.visible == false)
	assert(panel._cancel_button.visible == false)
	panel.queue_free()

func test_refresh_trade_detail_cancelled() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	panel._selected_trade = {
		"status": "cancelled",
		"offer_coins": 100,
		"request_coins": 50,
		"recipient_name": "player_A",
		"sender_name": "player_B",
		"created_at": ""
	}
	panel._refresh_trade_detail()
	assert(panel._trade_detail.visible == true)
	assert(panel._accept_button.visible == false)
	assert(panel._reject_button.visible == false)
	assert(panel._cancel_button.visible == false)
	panel.queue_free()

func test_refresh_trade_detail_status_text() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	panel._selected_trade = {
		"status": "pending",
		"offer_coins": 100,
		"request_coins": 50,
		"recipient_name": "player_A",
		"sender_name": "player_B",
		"created_at": ""
	}
	panel._refresh_trade_detail()
	var detail_text: String = panel._detail_label.text
	assert(detail_text.find("状态: 待处理") != -1)
	assert(detail_text.find("发送者: player_B") != -1)
	assert(detail_text.find("接收者: player_A") != -1)
	assert(detail_text.find("提供金币: 100") != -1)
	assert(detail_text.find("请求金币: 50") != -1)
	panel.queue_free()

func test_on_trade_error() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	panel._on_trade_error("TRADE_NOT_FOUND", "交易未找到")
	assert(panel._loading_label.visible == false)
	assert(panel._empty_label.visible == true)
	assert(panel._empty_label.text == "加载失败: 交易未找到")
	panel.queue_free()

func test_clear() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	panel._trades = [{"trade_id": "t1"}]
	panel._selected_trade = {"trade_id": "t2"}
	panel._current_status = "pending"

	panel.clear()

	assert(panel._trades == [])
	assert(panel._selected_trade == {})
	assert(panel._trades_list.get_item_count() == 0)
	assert(panel._trade_detail.visible == false)
	assert(panel._empty_label.visible == false)
	assert(panel._loading_label.visible == true)
	panel.queue_free()

func test_close_pressed_signal_emission() -> void:
	var panel = load(TRADE_PANEL_SCENE).instantiate()
	var signal_emitted: bool = false
	var conn = panel.close_pressed.connect(func():
		signal_emitted = true
	)
	panel._on_close_pressed()
	conn.disconnect()
	assert(signal_emitted == true)
	panel.queue_free()
