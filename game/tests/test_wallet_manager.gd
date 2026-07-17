extends Node

func test_signals_declared() -> void:
	assert(WalletManager.has_signal("wallet_loaded"))
	assert(WalletManager.has_signal("transactions_loaded"))
	assert(WalletManager.has_signal("wallet_error"))

func test_initial_state() -> void:
	assert(WalletManager._wallet_data == {})
	assert(WalletManager._transactions == [])
	assert(WalletManager._is_loading == false)

func test_is_loading() -> void:
	assert(WalletManager.is_loading() == false)

func test_get_wallet() -> void:
	var result: Dictionary = WalletManager.get_wallet()
	assert(typeof(result) == TYPE_DICTIONARY)

func test_get_gold_coins() -> void:
	assert(WalletManager.get_gold_coins() == 0)

func test_get_transactions() -> void:
	var result: Array = WalletManager.get_transactions()
	assert(typeof(result) == TYPE_ARRAY)

func test_reset() -> void:
	WalletManager._wallet_data = {"gold_coins": 100}
	WalletManager._transactions = [{"id": "t1"}]
	WalletManager._is_loading = true

	WalletManager.reset()

	assert(WalletManager._wallet_data == {})
	assert(WalletManager._transactions == [])
	assert(WalletManager._is_loading == false)

func test_getters_return_duplicates() -> void:
	WalletManager._wallet_data = {"gold_coins": 100}
	WalletManager._transactions = [{"id": "t1"}]

	var wallet: Dictionary = WalletManager.get_wallet()
	var transactions: Array = WalletManager.get_transactions()

	wallet["gold_coins"] = 999
	transactions[0]["id"] = "modified"

	assert(WalletManager._wallet_data.get("gold_coins", 0) == 100, "get_wallet 应返回副本")
	assert(WalletManager._transactions[0].get("id", "") == "t1", "get_transactions 应返回副本")

	WalletManager.reset()