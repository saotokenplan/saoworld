extends Node

const WALLET_PANEL_SCENE := "res://scenes/ui/economy/WalletPanel.tscn"

func test_signals_declared() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	assert(panel.has_signal("close_pressed"))
	panel.queue_free()

func test_transaction_type_names_constant() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	assert(panel.TRANSACTION_TYPE_NAMES.size() == 6)
	assert(panel.TRANSACTION_TYPE_NAMES.get("earn", "") == "获得")
	assert(panel.TRANSACTION_TYPE_NAMES.get("spend", "") == "消耗")
	assert(panel.TRANSACTION_TYPE_NAMES.get("trade", "") == "交易")
	assert(panel.TRANSACTION_TYPE_NAMES.get("auction", "") == "拍卖")
	assert(panel.TRANSACTION_TYPE_NAMES.get("quest_reward", "") == "任务奖励")
	assert(panel.TRANSACTION_TYPE_NAMES.get("gift", "") == "赠送")
	panel.queue_free()

func test_initial_state() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	assert(panel._wallet_data == {})
	assert(panel._transactions == [])
	panel.queue_free()

func test_refresh_wallet_display_with_balance() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	panel._wallet_data = {"gold_coins": 500}
	panel._refresh_wallet_display()
	assert(panel._gold_label.text == "金币余额: 500")
	panel.queue_free()

func test_refresh_wallet_display_zero() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	panel._wallet_data = {}
	panel._refresh_wallet_display()
	assert(panel._gold_label.text == "金币余额: 0")
	panel.queue_free()

func test_refresh_transactions_display_empty() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	panel._transactions = []
	panel._refresh_transactions_display()
	assert(panel._transactions_list.get_item_count() == 0)
	assert(panel._empty_label.visible == true)
	assert(panel._loading_label.visible == false)
	panel.queue_free()

func test_refresh_transactions_display_with_data() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	panel._transactions = [
		{"transaction_type": "earn", "amount": 100, "description": "任务奖励", "created_at": "2026-07-18"},
		{"transaction_type": "spend", "amount": -50, "description": "购买物品", "created_at": ""}
	]
	panel._refresh_transactions_display()
	assert(panel._transactions_list.get_item_count() == 2)
	assert(panel._empty_label.visible == false)
	assert(panel._loading_label.visible == false)
	panel.queue_free()

func test_refresh_transactions_display_unknown_type() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	panel._transactions = [
		{"transaction_type": "unknown_type", "amount": 30, "description": "未知类型", "created_at": ""}
	]
	panel._refresh_transactions_display()
	assert(panel._transactions_list.get_item_count() == 1)
	# 未知类型应原样保留
	var item_text: String = panel._transactions_list.get_item_text(0)
	assert(item_text.find("unknown_type") != -1)
	panel.queue_free()

func test_on_wallet_error() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	panel._on_wallet_error("WALLET_NOT_FOUND", "钱包未找到")
	assert(panel._loading_label.visible == false)
	assert(panel._empty_label.visible == true)
	assert(panel._empty_label.text == "加载失败: 钱包未找到")
	panel.queue_free()

func test_clear() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	panel._wallet_data = {"gold_coins": 100}
	panel._transactions = [{"id": "t1"}]

	panel.clear()

	assert(panel._wallet_data == {})
	assert(panel._transactions == [])
	assert(panel._transactions_list.get_item_count() == 0)
	assert(panel._gold_label.text == "金币余额: 0")
	assert(panel._empty_label.visible == false)
	assert(panel._loading_label.visible == true)
	panel.queue_free()

func test_close_pressed_signal_emission() -> void:
	var panel = load(WALLET_PANEL_SCENE).instantiate()
	var signal_emitted: bool = false
	var conn = panel.close_pressed.connect(func():
		signal_emitted = true
	)
	panel._on_close_pressed()
	conn.disconnect()
	assert(signal_emitted == true)
	panel.queue_free()
