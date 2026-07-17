extends Control

signal close_pressed

var _wallet_data: Dictionary = {}
var _transactions: Array = []

@onready var _close_button: Button = $CloseButton
@onready var _gold_label: Label = $GoldLabel
@onready var _transactions_list: ItemList = $TransactionsList
@onready var _empty_label: Label = $EmptyLabel
@onready var _loading_label: Label = $LoadingLabel

const TRANSACTION_TYPE_NAMES: Dictionary = {
	"earn": "获得",
	"spend": "消耗",
	"trade": "交易",
	"auction": "拍卖",
	"quest_reward": "任务奖励",
	"gift": "赠送"
}

func _ready() -> void:
	_close_button.pressed.connect(_on_close_pressed)
	
	var wallet_manager: Node = get_node_or_null("/root/WalletManager")
	if wallet_manager != null:
		wallet_manager.wallet_loaded.connect(_on_wallet_loaded)
		wallet_manager.transactions_loaded.connect(_on_transactions_loaded)
		wallet_manager.wallet_error.connect(_on_wallet_error)
		wallet_manager.fetch_wallet()
		wallet_manager.fetch_transactions()

func _on_close_pressed() -> void:
	close_pressed.emit()

func _on_wallet_loaded() -> void:
	var wallet_manager: Node = get_node_or_null("/root/WalletManager")
	if wallet_manager != null:
		_wallet_data = wallet_manager.get_wallet()
		_refresh_wallet_display()

func _on_transactions_loaded() -> void:
	var wallet_manager: Node = get_node_or_null("/root/WalletManager")
	if wallet_manager != null:
		_transactions = wallet_manager.get_transactions()
		_refresh_transactions_display()

func _on_wallet_error(error_code: String, message: String) -> void:
	_loading_label.visible = false
	_empty_label.visible = true
	_empty_label.text = "加载失败: " + message

func _refresh_wallet_display() -> void:
	var gold_coins: int = _wallet_data.get("gold_coins", 0)
	_gold_label.text = "金币余额: %d" % gold_coins

func _refresh_transactions_display() -> void:
	_transactions_list.clear()
	_loading_label.visible = false
	
	if _transactions.is_empty():
		_empty_label.visible = true
		return
	
	_empty_label.visible = false
	
	for transaction: Dictionary in _transactions:
		var transaction_type: String = transaction.get("transaction_type", "unknown")
		var amount: int = transaction.get("amount", 0)
		var description: String = transaction.get("description", "")
		var created_at: String = transaction.get("created_at", "")
		
		var type_name: String = TRANSACTION_TYPE_NAMES.get(transaction_type, transaction_type)
		var sign: String = "+" if amount > 0 else ""
		var display_text: String = "%s | %s%d | %s" % [type_name, sign, amount, description]
		if created_at != "":
			display_text += " | %s" % created_at
		
		_transactions_list.add_item(display_text)

func clear() -> void:
	_wallet_data.clear()
	_transactions.clear()
	_transactions_list.clear()
	_gold_label.text = "金币余额: 0"
	_empty_label.visible = false
	_loading_label.visible = true