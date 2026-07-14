extends Node

## 怪物数据管理器
## 负责从 world-service 获取和管理怪物定义数据

signal monsters_loaded
signal monster_detail_loaded(monster_id: String)
signal monsters_error(error_code: String, message: String)
signal auth_error(message: String)
signal loading_changed(is_loading: bool)

var monster_list: Array[Dictionary] = []
var monster_cache: Dictionary = {}
var is_loading: bool = false
var last_error: Dictionary = {}
var schema_version: int = 1

const MONSTER_TYPE: Dictionary = {
	"beast": {"name": "野兽", "color": "#8B4513"},
	"humanoid": {"name": "人形", "color": "#4169E1"},
	"undead": {"name": "亡灵", "color": "#6A0DAD"},
	"mechanical": {"name": "机械", "color": "#708090"},
	"elemental": {"name": "元素", "color": "#00CED1"},
	"demon": {"name": "恶魔", "color": "#DC143C"},
	"dragon": {"name": "龙族", "color": "#FFD700"},
	"boss": {"name": "Boss", "color": "#FF4500"},
}

const AGGRESSION_LEVEL: Dictionary = {
	"passive": {"name": "被动", "icon": "🟢"},
	"defensive": {"name": "防御", "icon": "🟡"},
	"aggressive": {"name": "攻击", "icon": "🔴"},
	"berserker": {"name": "狂暴", "icon": "💀"},
}


func _ready() -> void:
	APIManager.auth_error.connect(_on_auth_error)


func _on_auth_error(request_id: String, message: String) -> void:
	auth_error.emit(message)


func fetch_monsters(
	monster_type: String = "",
	chapter_id: String = "",
	region_key: String = "",
	limit: int = 20,
	offset: int = 0
) -> void:
	_set_loading(true)
	var params: Array[String] = []
	params.append("limit=%d" % limit)
	params.append("offset=%d" % offset)
	if monster_type != "":
		params.append("monster_type=%s" % monster_type)
	if chapter_id != "":
		params.append("chapter_id=%s" % chapter_id)
	if region_key != "":
		params.append("region_key=%s" % region_key)

	var endpoint: String = "/world/monsters?%s" % "&".join(params)
	var result: Dictionary = APIManager.get(endpoint)
	_handle_monsters_response(result)


func fetch_monster_detail(monster_id: String) -> void:
	_set_loading(true)
	var endpoint: String = "/world/monsters/%s" % monster_id
	var result: Dictionary = APIManager.get(endpoint)
	_handle_monster_detail_response(result)


func get_monster_by_key(monster_key: String) -> Dictionary:
	for monster: Dictionary in monster_list:
		if monster.get("monster_key", "") == monster_key:
			return monster
	return {}


func get_monster_type_display(monster_type: String) -> Dictionary:
	return MONSTER_TYPE.get(monster_type, {"name": "未知", "color": "#999999"})


func get_aggression_display(aggression: String) -> Dictionary:
	return AGGRESSION_LEVEL.get(aggression, {"name": "未知", "icon": "❓"})


func _handle_monsters_response(result: Dictionary) -> void:
	_set_loading(false)
	if result.has("error"):
		last_error = result.error
		monsters_error.emit(result.error.get("code", "UNKNOWN"), result.error.get("message", ""))
		return

	var data: Dictionary = result.get("data", {})
	monster_list.clear()
	for monster: Dictionary in data.get("monsters", []):
		monster_list.append(_validate_monster(monster))
		monster_cache[monster.get("monster_id", "")] = monster

	monsters_loaded.emit()


func _handle_monster_detail_response(result: Dictionary) -> void:
	_set_loading(false)
	if result.has("error"):
		last_error = result.error
		monsters_error.emit(result.error.get("code", "UNKNOWN"), result.error.get("message", ""))
		return

	var data: Dictionary = result.get("data", {})
	var monster: Dictionary = _validate_monster(data)
	monster_cache[monster.get("monster_id", "")] = monster
	monster_detail_loaded.emit(monster.get("monster_id", ""))


func _validate_monster(data: Dictionary) -> Dictionary:
	if not data.has("monster_id") or data.monster_id == "":
		push_warning("MonsterManager: monster data missing monster_id")
	if not data.has("monster_key") or data.monster_key == "":
		push_warning("MonsterManager: monster data missing monster_key")
	if not data.has("name") or data.name == "":
		push_warning("MonsterManager: monster data missing name")
	if not data.has("monster_type") or data.monster_type == "":
		push_warning("MonsterManager: monster data missing monster_type")

	var level: int = data.get("level", 1)
	if level < 1 or level > 60:
		push_warning("MonsterManager: monster level out of range: %d" % level)
		data.level = clampi(level, 1, 60)

	var hp: int = data.get("hp", 0)
	if hp <= 0:
		push_warning("MonsterManager: monster hp must be positive: %d" % hp)
		data.hp = 1

	return data


func _set_loading(value: bool) -> void:
	is_loading = value
	loading_changed.emit(value)
