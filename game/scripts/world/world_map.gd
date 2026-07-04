extends Node2D
## 世界/区域场景基础框架

signal region_selected(region_id: String)

var regions: Array[Dictionary] = []

func _ready() -> void:
	pass

func load_regions(region_list: Array[Dictionary]) -> void:
	regions = region_list
	_render_regions()

func _render_regions() -> void:
	pass

func select_region(region_id: String) -> void:
	region_selected.emit(region_id)
