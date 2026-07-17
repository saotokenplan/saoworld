extends Node

func test_trade_signals_declared() -> void:
	assert(TradeManager.has_signal("trades_loaded"))
	assert(TradeManager.has_signal("trade_created"))
	assert(TradeManager.has_signal("trade_updated"))
	assert(TradeManager.has_signal("trade_error"))

func test_auction_signals_declared() -> void:
	assert(TradeManager.has_signal("auctions_loaded"))
	assert(TradeManager.has_signal("auction_created"))
	assert(TradeManager.has_signal("auction_updated"))
	assert(TradeManager.has_signal("auction_error"))

func test_initial_state() -> void:
	assert(TradeManager._trades == [])
	assert(TradeManager._trade_detail == {})
	assert(TradeManager._auctions == [])
	assert(TradeManager._my_auctions == [])
	assert(TradeManager._auction_detail == {})
	assert(TradeManager._is_loading == false)

func test_is_loading() -> void:
	assert(TradeManager.is_loading() == false)

func test_get_trades() -> void:
	var result: Array = TradeManager.get_trades()
	assert(typeof(result) == TYPE_ARRAY)

func test_get_trade_detail() -> void:
	var result: Dictionary = TradeManager.get_trade_detail()
	assert(typeof(result) == TYPE_DICTIONARY)

func test_get_auctions() -> void:
	var result: Array = TradeManager.get_auctions()
	assert(typeof(result) == TYPE_ARRAY)

func test_get_my_auctions() -> void:
	var result: Array = TradeManager.get_my_auctions()
	assert(typeof(result) == TYPE_ARRAY)

func test_get_auction_detail() -> void:
	var result: Dictionary = TradeManager.get_auction_detail()
	assert(typeof(result) == TYPE_DICTIONARY)

func test_reset() -> void:
	TradeManager._trades = [{"id": "t1"}]
	TradeManager._trade_detail = {"id": "t2"}
	TradeManager._auctions = [{"id": "a1"}]
	TradeManager._my_auctions = [{"id": "a2"}]
	TradeManager._auction_detail = {"id": "a3"}
	TradeManager._is_loading = true

	TradeManager.reset()

	assert(TradeManager._trades == [])
	assert(TradeManager._trade_detail == {})
	assert(TradeManager._auctions == [])
	assert(TradeManager._my_auctions == [])
	assert(TradeManager._auction_detail == {})
	assert(TradeManager._is_loading == false)

func test_getters_return_duplicates() -> void:
	TradeManager._trades = [{"trade_id": "t1"}]
	TradeManager._trade_detail = {"trade_id": "t2"}
	TradeManager._auctions = [{"listing_id": "a1"}]
	TradeManager._my_auctions = [{"listing_id": "a2"}]
	TradeManager._auction_detail = {"listing_id": "a3"}

	var trades: Array = TradeManager.get_trades()
	var trade_detail: Dictionary = TradeManager.get_trade_detail()
	var auctions: Array = TradeManager.get_auctions()
	var my_auctions: Array = TradeManager.get_my_auctions()
	var auction_detail: Dictionary = TradeManager.get_auction_detail()

	trades[0]["trade_id"] = "modified"
	trade_detail["trade_id"] = "modified"
	auctions[0]["listing_id"] = "modified"
	my_auctions[0]["listing_id"] = "modified"
	auction_detail["listing_id"] = "modified"

	assert(TradeManager._trades[0].get("trade_id", "") == "t1", "get_trades 应返回副本")
	assert(TradeManager._trade_detail.get("trade_id", "") == "t2", "get_trade_detail 应返回副本")
	assert(TradeManager._auctions[0].get("listing_id", "") == "a1", "get_auctions 应返回副本")
	assert(TradeManager._my_auctions[0].get("listing_id", "") == "a2", "get_my_auctions 应返回副本")
	assert(TradeManager._auction_detail.get("listing_id", "") == "a3", "get_auction_detail 应返回副本")

	TradeManager.reset()

func test_create_trade_empty_recipient() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.trade_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.create_trade("", 100, [])

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_RECIPIENT")

func test_accept_trade_empty_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.trade_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.accept_trade("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_TRADE_ID")

func test_reject_trade_empty_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.trade_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.reject_trade("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_TRADE_ID")

func test_cancel_trade_empty_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.trade_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.cancel_trade("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_TRADE_ID")

func test_create_auction_empty_item_key() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.auction_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.create_auction_listing("", 1, 10, 20, 24)

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_ITEM_KEY")

func test_create_auction_invalid_quantity() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.auction_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.create_auction_listing("item_001", 0, 10, 20, 24)

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_QUANTITY")

func test_create_auction_invalid_starting_price() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.auction_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.create_auction_listing("item_001", 1, 0, 20, 24)

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_STARTING_PRICE")

func test_cancel_auction_empty_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.auction_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.cancel_auction_listing("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_LISTING_ID")

func test_bid_auction_empty_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.auction_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.bid_auction("", 10)

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_LISTING_ID")

func test_bid_auction_invalid_amount() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.auction_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.bid_auction("listing_001", 0)

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_BID_AMOUNT")

func test_buyout_auction_empty_id() -> void:
	var error_emitted: bool = false
	var error_code: String = ""

	var conn = TradeManager.auction_error.connect(func(code: String, msg: String):
		error_emitted = true
		error_code = code
	)

	TradeManager.buyout_auction("")

	conn.disconnect()

	assert(error_emitted == true)
	assert(error_code == "INVALID_LISTING_ID")