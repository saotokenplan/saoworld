extends Control

signal close_pressed
signal listing_selected(listing_id: String)

var _auctions: Array = []
var _selected_listing: Dictionary = {}
var _current_category: String = ""

@onready var _close_button: Button = $CloseButton
@onready var _category_input: LineEdit = $CategoryInput
@onready var _search_button: Button = $SearchButton
@onready var _auctions_list: ItemList = $AuctionsList
@onready var _auction_detail: VBoxContainer = $AuctionDetail
@onready var _detail_label: Label = $AuctionDetail/DetailLabel
@onready var _bid_button: Button = $AuctionDetail/BidButton
@onready var _buyout_button: Button = $AuctionDetail/BuyoutButton
@onready var _empty_label: Label = $EmptyLabel
@onready var _loading_label: Label = $LoadingLabel

const AUCTION_STATUS_NAMES: Dictionary = {
	"active": "进行中",
	"closed": "已结束",
	"cancelled": "已取消"
}

func _ready() -> void:
	_close_button.pressed.connect(_on_close_pressed)
	_search_button.pressed.connect(_on_search_clicked)
	_auctions_list.item_selected.connect(_on_listing_selected)
	_bid_button.pressed.connect(_on_bid_clicked)
	_buyout_button.pressed.connect(_on_buyout_clicked)
	
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.auctions_loaded.connect(_on_auctions_loaded)
		trade_manager.auction_error.connect(_on_auction_error)
		trade_manager.auction_updated.connect(_on_auction_updated)
		trade_manager.fetch_auctions()

func _on_close_pressed() -> void:
	close_pressed.emit()

func _on_search_clicked() -> void:
	var category: String = _category_input.text.strip()
	_current_category = category
	
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.fetch_auctions(category)

func _on_listing_selected(index: int) -> void:
	if index < 0 or index >= _auctions.size():
		return
	
	_selected_listing = _auctions[index]
	_refresh_auction_detail()

func _on_bid_clicked() -> void:
	var listing_id: String = _selected_listing.get("listing_id", "")
	if listing_id == "":
		return
	
	var current_bid: int = _selected_listing.get("current_bid", 0)
	var next_bid: int = current_bid + 10
	
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.bid_auction(listing_id, next_bid)

func _on_buyout_clicked() -> void:
	var listing_id: String = _selected_listing.get("listing_id", "")
	if listing_id == "":
		return
	
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.buyout_auction(listing_id)

func _on_auctions_loaded() -> void:
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		_auctions = trade_manager.get_auctions()
		_refresh_auctions_display()

func _on_auction_error(error_code: String, message: String) -> void:
	_loading_label.visible = false
	_empty_label.visible = true
	_empty_label.text = "加载失败: " + message

func _on_auction_updated(listing_id: String) -> void:
	var trade_manager: Node = get_node_or_null("/root/TradeManager")
	if trade_manager != null:
		trade_manager.fetch_auctions(_current_category)

func _refresh_auctions_display() -> void:
	_auctions_list.clear()
	_loading_label.visible = false
	_auction_detail.visible = false
	
	if _auctions.is_empty():
		_empty_label.visible = true
		return
	
	_empty_label.visible = false
	
	for auction: Dictionary in _auctions:
		var listing_id: String = auction.get("listing_id", "")
		var item_name: String = auction.get("item_name", "")
		var item_key: String = auction.get("item_key", "")
		var quantity: int = auction.get("quantity", 1)
		var starting_price: int = auction.get("starting_price", 0)
		var current_bid: int = auction.get("current_bid", 0)
		var buyout_price: int = auction.get("buyout_price", 0)
		var status: String = auction.get("status", "")
		var seller_name: String = auction.get("seller_name", "")
		
		var status_name: String = AUCTION_STATUS_NAMES.get(status, status)
		var display_name: String = item_name if item_name != "" else item_key
		
		var display_text: String = "%s | %s | 数量: %d | 当前价: %d | 一口价: %d | %s" % [
			listing_id, display_name, quantity, current_bid, buyout_price, status_name
		]
		
		_auctions_list.add_item(display_text)

func _refresh_auction_detail() -> void:
	_auction_detail.visible = true
	
	var item_name: String = _selected_listing.get("item_name", "")
	var item_key: String = _selected_listing.get("item_key", "")
	var quantity: int = _selected_listing.get("quantity", 1)
	var starting_price: int = _selected_listing.get("starting_price", 0)
	var current_bid: int = _selected_listing.get("current_bid", 0)
	var buyout_price: int = _selected_listing.get("buyout_price", 0)
	var status: String = _selected_listing.get("status", "")
	var seller_name: String = _selected_listing.get("seller_name", "")
	var end_time: String = _selected_listing.get("end_time", "")
	
	var status_name: String = AUCTION_STATUS_NAMES.get(status, status)
	var display_name: String = item_name if item_name != "" else item_key
	
	var detail_text: String = "状态: %s\n\n" % status_name
	detail_text += "物品: %s\n" % display_name
	detail_text += "数量: %d\n\n" % quantity
	detail_text += "起拍价: %d\n" % starting_price
	detail_text += "当前价: %d\n" % current_bid
	detail_text += "一口价: %d\n\n" % buyout_price
	detail_text += "卖家: %s\n" % seller_name
	if end_time != "":
		detail_text += "结束时间: %s" % end_time
	
	_detail_label.text = detail_text
	
	var is_active: bool = (status == "active")
	_bid_button.visible = is_active
	_buyout_button.visible = is_active and buyout_price > 0

func clear() -> void:
	_auctions.clear()
	_selected_listing.clear()
	_auctions_list.clear()
	_auction_detail.visible = false
	_empty_label.visible = false
	_loading_label.visible = true