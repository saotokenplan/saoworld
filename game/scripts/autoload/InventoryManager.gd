extends Node
## 背包管理器
## 负责管理玩家背包数据，与后端 API 交互

signal inventory_updated
signal item_used(item_key: String, quantity: int)
signal item_added(item_key: String, quantity: int)
signal item_removed(item_key: String, quantity: int)
signal inventory_error(error_message: String)
signal equipment_updated(equipment: Array[Dictionary], stats: Dictionary)
signal equipment_error(error_message: String)

var _items: Array[Dictionary] = []
var _equipment: Array[Dictionary] = []
var _equipment_stats: Dictionary = {}
var _is_loading: bool = false
var _last_error: String = ""

## 获取所有物品
func get_items() -> Array[Dictionary]:
	return _items

## 获取指定物品
func get_item(item_key: String) -> Dictionary:
	for item: Dictionary in _items:
		if item.get("item_key", "") == item_key:
			return item
	return {}

## 获取指定类型的物品
func get_items_by_type(item_type: String) -> Array[Dictionary]:
	var filtered: Array[Dictionary] = []
	for item: Dictionary in _items:
		if item.get("item_type", "") == item_type:
			filtered.append(item)
	return filtered

## 获取物品数量
func get_item_quantity(item_key: String) -> int:
	var item: Dictionary = get_item(item_key)
	if item.is_empty():
		return 0
	return int(item.get("quantity", 0))

## 是否正在加载
func is_loading() -> bool:
	return _is_loading

## 获取最后错误
func get_last_error() -> String:
	return _last_error

## 从服务器加载背包数据
func load_inventory() -> void:
	if _is_loading:
		return
	_is_loading = true
	_last_error = ""
	
	var api_manager: Node = get_node_or_null("/root/APIManager")
	if api_manager == null:
		_is_loading = false
		_last_error = "APIManager 不可用"
		inventory_error.emit(_last_error)
		return
	
	var callback: Callable = _on_inventory_loaded
	api_manager.get("/api/v1/player/inventory", callback)

## 使用消耗品
func use_item(item_key: String, quantity: int = 1) -> void:
	if _is_loading:
		return
	_is_loading = true
	_last_error = ""
	
	var api_manager: Node = get_node_or_null("/root/APIManager")
	if api_manager == null:
		_is_loading = false
		_last_error = "APIManager 不可用"
		inventory_error.emit(_last_error)
		return
	
	var callback: Callable = _on_item_used.bind(item_key, quantity)
	api_manager.post("/api/v1/player/inventory/use?item_key=" + item_key, {"quantity": quantity}, callback)

## 从本地缓存加载背包（存档恢复用）
func load_from_cache(items_data: Array) -> void:
	_items.clear()
	for item_data: Dictionary in items_data:
		_items.append(item_data)
	inventory_updated.emit()

## 获取可序列化的背包数据
func serialize() -> Array:
	var result: Array = []
	for item: Dictionary in _items:
		result.append(item.duplicate())
	return result

## 清空背包缓存
func clear_cache() -> void:
	_items.clear()
	_equipment.clear()
	_equipment_stats.clear()
	inventory_updated.emit()

## 获取装备列表
func get_equipment() -> Array[Dictionary]:
	return _equipment

## 获取装备属性统计
func get_equipment_stats() -> Dictionary:
	return _equipment_stats

## 从服务器加载装备数据
func load_equipment() -> void:
	if _is_loading:
		return
	_is_loading = true
	_last_error = ""
	
	var api_manager: Node = get_node_or_null("/root/APIManager")
	if api_manager == null:
		_is_loading = false
		_last_error = "APIManager 不可用"
		equipment_error.emit(_last_error)
		return
	
	var callback: Callable = _on_equipment_loaded
	api_manager.get("/api/v1/player/equipment", callback)

## 装备物品
func equip_item(slot: String, item_key: String) -> void:
	if _is_loading:
		return
	_is_loading = true
	_last_error = ""
	
	var api_manager: Node = get_node_or_null("/root/APIManager")
	if api_manager == null:
		_is_loading = false
		_last_error = "APIManager 不可用"
		equipment_error.emit(_last_error)
		return
	
	var callback: Callable = _on_equip_item_completed.bind(slot)
	var body: Dictionary = {"item_key": item_key}
	api_manager.post("/api/v1/player/equipment/equip?slot=" + slot, body, callback)

## 卸下装备
func unequip_item(slot: String) -> void:
	if _is_loading:
		return
	_is_loading = true
	_last_error = ""
	
	var api_manager: Node = get_node_or_null("/root/APIManager")
	if api_manager == null:
		_is_loading = false
		_last_error = "APIManager 不可用"
		equipment_error.emit(_last_error)
		return
	
	var callback: Callable = _on_unequip_item_completed.bind(slot)
	var body: Dictionary = {}
	api_manager.post("/api/v1/player/equipment/unequip?slot=" + slot, body, callback)

## 回调：背包加载完成
func _on_inventory_loaded(response: Dictionary) -> void:
	_is_loading = false
	var code: int = response.get("code", 0)
	if code >= 400:
		_last_error = response.get("message", "加载背包失败")
		inventory_error.emit(_last_error)
		return
	
	var data: Dictionary = response.get("data", {})
	var items_array: Array = data.get("data", [])
	_items.clear()
	for item_data: Dictionary in items_array:
		_items.append(item_data)
	inventory_updated.emit()

## 回调：使用物品完成
func _on_item_used(response: Dictionary, item_key: String, quantity: int) -> void:
	_is_loading = false
	var code: int = response.get("code", 0)
	if code >= 400:
		_last_error = response.get("message", "使用物品失败")
		inventory_error.emit(_last_error)
		return
	
	# 更新本地缓存
	var data: Dictionary = response.get("data", {})
	var used_quantity: int = data.get("quantity", 0)
	
	for i: int in range(_items.size()):
		if _items[i].get("item_key", "") == item_key:
			if used_quantity <= 0:
				_items.remove_at(i)
			else:
				_items[i]["quantity"] = used_quantity
			break
	
	item_used.emit(item_key, quantity)
	inventory_updated.emit()

## 回调：装备加载完成
func _on_equipment_loaded(response: Dictionary) -> void:
	_is_loading = false
	var code: int = response.get("code", 0)
	if code >= 400:
		_last_error = response.get("message", "加载装备失败")
		equipment_error.emit(_last_error)
		return
	
	var data: Dictionary = response.get("data", {})
	_equipment = data.get("equipment", [])
	_equipment_stats = data.get("stats", {})
	equipment_updated.emit(_equipment, _equipment_stats)

## 回调：装备物品完成
func _on_equip_item_completed(response: Dictionary, slot: String) -> void:
	_is_loading = false
	var code: int = response.get("code", 0)
	if code >= 400:
		_last_error = response.get("message", "装备物品失败")
		equipment_error.emit(_last_error)
		return
	
	load_equipment()

## 回调：卸下装备完成
func _on_unequip_item_completed(response: Dictionary, slot: String) -> void:
	_is_loading = false
	var code: int = response.get("code", 0)
	if code >= 400:
		_last_error = response.get("message", "卸下装备失败")
		equipment_error.emit(_last_error)
		return
	
	load_equipment()
