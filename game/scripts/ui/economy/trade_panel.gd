extends Control

signal close_pressed
signal trade_selected(trade_id: String)

var _trades: Array = []
var _selected_trade: Dictionary = {}
var _current_status: String = "all"

@onready var _close_button: Button = $CloseButton
@onready var _status_container: HBoxContainer = $StatusContainer
@onready var _trades_list: ItemList = $TradesList
@onready var _trade_detail: VBoxContainer = $TradeDetail
@onready var _detail_label: Label = $TradeDetail/DetailLabel
@onready var _accept_button: Button = $TradeDetail/AcceptButton
@onready var _reject_button: Button = $TradeDetail/RejectButton
@onready var _cancel_button: Button = $TradeDetail/CancelButton
@onready var _empty_label: Label = $EmptyLabel
@onready var _loading_label: Label = $LoadingLabel

const STATUS_NAMES: Dictionary = {
	"all": "全部",
	"pending": "待处理",
	"sent": "已发出",
	"completed": "已完成",
	"cancelled": "已取消"
}

const TRADE_STATUS_NAMES: Dictionary = {
	"pending": "待处理",
	"sent": "已发出",
	"completed": "已完成",
	"cancelled": "已取消"
}

func _ready() -> void:
	_close_button.pressed.connect(_on_close_pressed)
	_trades_list.item_selected.connect(_on_trade_selected)
	_accept_button.pressed.connect(_on_accept_trade)
	_reject_button.pressed.connect(_on_reject_trade)
	_cancel_button.pressed.connect(_on_cancel_trade)
	
	for child: Node in _status_container.get_children():
		if child is Button:
			child.pressed.connect(_on_status_button_pressed.bind(child.name))
	
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.trades_loaded.connect(_on_trades_loaded)
		trade_manager.trade_error.connect(_on_trade_error)
		trade_manager.trade_updated.connect(_on_trade_updated)
		trade_manager.fetch_trades()

func _on_close_pressed() -> void:
	close_pressed.emit()

func _on_status_button_pressed(status: String) -> void:
	_current_status = status
	for child: Node in _status_container.get_children():
		if child is Button:
			child.toggle_mode = (child.name == status)
	
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.fetch_trades(status)

func _on_trade_selected(index: int) -> void:
	if index < 0 or index >= _trades.size():
		return
	
	_selected_trade = _trades[index]
	_refresh_trade_detail()

func _on_accept_trade() -> void:
	var trade_id: String = _selected_trade.get("trade_id", "")
	if trade_id == "":
		return
	
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.accept_trade(trade_id)

func _on_reject_trade() -> void:
	var trade_id: String = _selected_trade.get("trade_id", "")
	if trade_id == "":
		return
	
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.reject_trade(trade_id)

func _on_cancel_trade() -> void:
	var trade_id: String = _selected_trade.get("trade_id", "")
	if trade_id == "":
		return
	
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.cancel_trade(trade_id)

func _on_trades_loaded() -> void:
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		_trades = trade_manager.get_trades()
		_refresh_trades_display()

func _on_trade_error(error_code: String, message: String) -> void:
	_loading_label.visible = false
	_empty_label.visible = true
	_empty_label.text = "加载失败: " + message

func _on_trade_updated(trade_id: String) -> void:
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.fetch_trades(_current_status)

func _refresh_trades_display() -> void:
	_trades_list.clear()
	_loading_label.visible = false
	_trade_detail.visible = false
	
	if _trades.is_empty():
		_empty_label.visible = true
		return
	
	_empty_label.visible = false
	
	for trade: Dictionary in _trades:
		var trade_id: String = trade.get("trade_id", "")
		var status: String = trade.get("status", "")
		var offer_coins: int = trade.get("offer_coins", 0)
		var offer_items: Array = trade.get("offer_items", [])
		var recipient_name: String = trade.get("recipient_name", "")
		var sender_name: String = trade.get("sender_name", "")
		
		var status_name: String = TRADE_STATUS_NAMES.get(status, status)
		var counterparty_name: String = sender_name if status == "pending" else recipient_name
		
		var display_text: String = "%s | %s | 金币: %d | 物品: %d | %s" % [
			trade_id, status_name, offer_coins, offer_items.size(), counterparty_name
		]
		
		_trades_list.add_item(display_text)

func _refresh_trade_detail() -> void:
	_trade_detail.visible = true
	
	var status: String = _selected_trade.get("status", "")
	var offer_coins: int = _selected_trade.get("offer_coins", 0)
	var request_coins: int = _selected_trade.get("request_coins", 0)
	var recipient_name: String = _selected_trade.get("recipient_name", "")
	var sender_name: String = _selected_trade.get("sender_name", "")
	var created_at: String = _selected_trade.get("created_at", "")
	
	var status_name: String = TRADE_STATUS_NAMES.get(status, status)
	
	var detail_text: String = "状态: %s\n\n" % status_name
	detail_text += "发送者: %s\n" % sender_name
	detail_text += "接收者: %s\n\n" % recipient_name
	detail_text += "提供金币: %d\n" % offer_coins
	detail_text += "请求金币: %d\n" % request_coins
	if created_at != "":
		detail_text += "\n创建时间: %s" % created_at
	
	_detail_label.text = detail_text
	
	_accept_button.visible = (status == "pending")
	_reject_button.visible = (status == "pending")
	_cancel_button.visible = (status == "sent")

func clear() -> void:
	_trades.clear()
	_selected_trade.clear()
	_trades_list.clear()
	_trade_detail.visible = false
	_empty_label.visible = false
	_loading_label.visible = true