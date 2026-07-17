extends Node

signal trades_loaded
signal trade_created
signal trade_updated(trade_id: String)
signal trade_error(error_code: String, message: String)

signal auctions_loaded
signal auction_created
signal auction_updated(listing_id: String)
signal auction_error(error_code: String, message: String)

var _trades: Array = []
var _trade_detail: Dictionary = {}
var _auctions: Array = []
var _my_auctions: Array = []
var _auction_detail: Dictionary = {}
var _is_loading: bool = false

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)

func _on_auth_error(request_id: String, message: String) -> void:
	trade_error.emit("AUTH_ERROR", message)
	auction_error.emit("AUTH_ERROR", message)

func create_trade(recipient_id: String, offer_coins: int, offer_items: Array = []) -> void:
	if recipient_id == "":
		trade_error.emit("INVALID_RECIPIENT", "接收者ID不能为空")
		return

	_set_loading(true)
	var body: Dictionary = {
		"recipient_id": recipient_id,
		"offer_coins": offer_coins,
		"offer_items": offer_items
	}
	var result: Dictionary = APIManager.post("/player/trades", body)

	if result.get("success", false):
		_trade_detail = result.get("data", {})
		trade_created.emit()
	else:
		_handle_trade_error(result)

	_set_loading(false)

func accept_trade(trade_id: String) -> void:
	if trade_id == "":
		trade_error.emit("INVALID_TRADE_ID", "交易ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/player/trades/%s/accept" % trade_id)

	if result.get("success", false):
		_trade_detail = result.get("data", {})
		trade_updated.emit(trade_id)
	else:
		_handle_trade_error(result)

	_set_loading(false)

func reject_trade(trade_id: String) -> void:
	if trade_id == "":
		trade_error.emit("INVALID_TRADE_ID", "交易ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/player/trades/%s/reject" % trade_id)

	if result.get("success", false):
		_trade_detail = result.get("data", {})
		trade_updated.emit(trade_id)
	else:
		_handle_trade_error(result)

	_set_loading(false)

func cancel_trade(trade_id: String) -> void:
	if trade_id == "":
		trade_error.emit("INVALID_TRADE_ID", "交易ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/player/trades/%s/cancel" % trade_id)

	if result.get("success", false):
		_trade_detail = result.get("data", {})
		trade_updated.emit(trade_id)
	else:
		_handle_trade_error(result)

	_set_loading(false)

func fetch_trades(trade_status: String = "", limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var url: String = "/player/trades?limit=%d&offset=%d" % [limit, offset]
	if trade_status != "":
		url += "&status=%s" % trade_status

	var result: Dictionary = APIManager.get(url)

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_trades = data.get("trades", data.get("items", []))
		trades_loaded.emit()
	else:
		_handle_trade_error(result)

	_set_loading(false)

func fetch_trade_detail(trade_id: String) -> void:
	if trade_id == "":
		trade_error.emit("INVALID_TRADE_ID", "交易ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.get("/player/trades/%s" % trade_id)

	if result.get("success", false):
		_trade_detail = result.get("data", {})
	else:
		_handle_trade_error(result)

	_set_loading(false)

func create_auction_listing(item_key: String, quantity: int, starting_price: int, buyout_price: int, duration_hours: int) -> void:
	if item_key == "":
		auction_error.emit("INVALID_ITEM_KEY", "物品Key不能为空")
		return
	if quantity <= 0:
		auction_error.emit("INVALID_QUANTITY", "数量必须大于0")
		return
	if starting_price <= 0:
		auction_error.emit("INVALID_STARTING_PRICE", "起拍价必须大于0")
		return

	_set_loading(true)
	var body: Dictionary = {
		"item_key": item_key,
		"quantity": quantity,
		"starting_price": starting_price,
		"buyout_price": buyout_price,
		"duration_hours": duration_hours
	}
	var result: Dictionary = APIManager.post("/player/auction/listings", body)

	if result.get("success", false):
		_auction_detail = result.get("data", {})
		auction_created.emit()
	else:
		_handle_auction_error(result)

	_set_loading(false)

func cancel_auction_listing(listing_id: String) -> void:
	if listing_id == "":
		auction_error.emit("INVALID_LISTING_ID", "拍卖ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/player/auction/listings/%s/cancel" % listing_id)

	if result.get("success", false):
		_auction_detail = result.get("data", {})
		auction_updated.emit(listing_id)
	else:
		_handle_auction_error(result)

	_set_loading(false)

func bid_auction(listing_id: String, bid_amount: int) -> void:
	if listing_id == "":
		auction_error.emit("INVALID_LISTING_ID", "拍卖ID不能为空")
		return
	if bid_amount <= 0:
		auction_error.emit("INVALID_BID_AMOUNT", "竞拍金额必须大于0")
		return

	_set_loading(true)
	var body: Dictionary = {"bid_amount": bid_amount}
	var result: Dictionary = APIManager.post("/player/auction/listings/%s/bid" % listing_id, body)

	if result.get("success", false):
		_auction_detail = result.get("data", {})
		auction_updated.emit(listing_id)
	else:
		_handle_auction_error(result)

	_set_loading(false)

func buyout_auction(listing_id: String) -> void:
	if listing_id == "":
		auction_error.emit("INVALID_LISTING_ID", "拍卖ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.post("/player/auction/listings/%s/buyout" % listing_id)

	if result.get("success", false):
		_auction_detail = result.get("data", {})
		auction_updated.emit(listing_id)
	else:
		_handle_auction_error(result)

	_set_loading(false)

func fetch_auctions(category: String = "", item_key: String = "", limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var url: String = "/player/auction/listings?limit=%d&offset=%d" % [limit, offset]
	if category != "":
		url += "&category=%s" % category
	if item_key != "":
		url += "&item_key=%s" % item_key

	var result: Dictionary = APIManager.get(url)

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_auctions = data.get("listings", data.get("items", []))
		auctions_loaded.emit()
	else:
		_handle_auction_error(result)

	_set_loading(false)

func fetch_auction_detail(listing_id: String) -> void:
	if listing_id == "":
		auction_error.emit("INVALID_LISTING_ID", "拍卖ID不能为空")
		return

	_set_loading(true)
	var result: Dictionary = APIManager.get("/player/auction/listings/%s" % listing_id)

	if result.get("success", false):
		_auction_detail = result.get("data", {})
	else:
		_handle_auction_error(result)

	_set_loading(false)

func fetch_my_listings(status: String = "", limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var url: String = "/player/auction/my-listings?limit=%d&offset=%d" % [limit, offset]
	if status != "":
		url += "&status=%s" % status

	var result: Dictionary = APIManager.get(url)

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_my_auctions = data.get("listings", data.get("items", []))
		auctions_loaded.emit()
	else:
		_handle_auction_error(result)

	_set_loading(false)

func get_trades() -> Array:
	return _trades.duplicate()

func get_trade_detail() -> Dictionary:
	return _trade_detail.duplicate()

func get_auctions() -> Array:
	return _auctions.duplicate()

func get_my_auctions() -> Array:
	return _my_auctions.duplicate()

func get_auction_detail() -> Dictionary:
	return _auction_detail.duplicate()

func is_loading() -> bool:
	return _is_loading

func _handle_trade_error(result: Dictionary) -> void:
	var err_code: String = result.get("code", "UNKNOWN_ERROR")
	var err_message: String = result.get("message", "操作失败")
	trade_error.emit(err_code, err_message)

func _handle_auction_error(result: Dictionary) -> void:
	var err_code: String = result.get("code", "UNKNOWN_ERROR")
	var err_message: String = result.get("message", "操作失败")
	auction_error.emit(err_code, err_message)

func _set_loading(loading: bool) -> void:
	_is_loading = loading

func reset() -> void:
	_trades.clear()
	_trade_detail.clear()
	_auctions.clear()
	_my_auctions.clear()
	_auction_detail.clear()
	_is_loading = false