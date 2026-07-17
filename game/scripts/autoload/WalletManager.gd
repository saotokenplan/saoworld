extends Node

signal wallet_loaded
signal transactions_loaded
signal wallet_error(error_code: String, message: String)

var _wallet_data: Dictionary = {}
var _transactions: Array = []
var _is_loading: bool = false

func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)

func _on_auth_error(request_id: String, message: String) -> void:
	wallet_error.emit("AUTH_ERROR", message)

func fetch_wallet() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/player/wallet")

	if result.get("success", false):
		_wallet_data = result.get("data", {})
		wallet_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func fetch_transactions(limit: int = 20, offset: int = 0) -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/player/wallet/transactions?limit=%d&offset=%d" % [limit, offset])

	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		_transactions = data.get("transactions", data.get("items", []))
		transactions_loaded.emit()
	else:
		_handle_error(result)

	_set_loading(false)

func get_wallet() -> Dictionary:
	return _wallet_data.duplicate()

func get_gold_coins() -> int:
	return _wallet_data.get("gold_coins", 0)

func get_transactions() -> Array:
	return _transactions.duplicate()

func is_loading() -> bool:
	return _is_loading

func _handle_error(result: Dictionary) -> void:
	var err_code: String = result.get("code", "UNKNOWN_ERROR")
	var err_message: String = result.get("message", "操作失败")
	wallet_error.emit(err_code, err_message)

func _set_loading(loading: bool) -> void:
	_is_loading = loading

func reset() -> void:
	_wallet_data.clear()
	_transactions.clear()
	_is_loading = false