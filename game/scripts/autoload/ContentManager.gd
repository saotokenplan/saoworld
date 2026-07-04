extends Node
## 内容包更新管理
## 负责管理内容包列表、更新检查、内容版本同步

signal content_updates_loaded
signal content_package_loaded
signal update_available(package_id: String)
signal content_error(error_code: String, message: String)

var available_updates: Array[Dictionary] = []
var installed_packages: Array[String] = []
var current_package_version: String = ""
var schema_version: int = 1

func _ready() -> void:
	_load_local_state()

func fetch_updates() -> void:
	var result: Dictionary = APIManager.get("/content/updates")
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		available_updates = data.get("items", [])
		_check_for_updates()
		content_updates_loaded.emit()
	else:
		content_error.emit(result.get("code", "UNKNOWN_ERROR"), result.get("message", "Failed to fetch updates"))

func fetch_package(package_id: String) -> Dictionary:
	var result: Dictionary = APIManager.get("/content/packages/%s" % package_id)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		content_package_loaded.emit()
		return data
	else:
		content_error.emit(result.get("code", "UNKNOWN_ERROR"), result.get("message", "Failed to fetch package"))
		return {}

func install_package(package_id: String) -> bool:
	if package_id in installed_packages:
		return true
	
	installed_packages.append(package_id)
	_save_local_state()
	return true

func is_package_installed(package_id: String) -> bool:
	return package_id in installed_packages

func has_updates_available() -> bool:
	for pkg in available_updates:
		var pkg_id: String = pkg.get("package_id", "")
		if pkg_id not in installed_packages:
			return true
	return false

func get_update_count() -> int:
	var count: int = 0
	for pkg in available_updates:
		var pkg_id: String = pkg.get("package_id", "")
		if pkg_id not in installed_packages:
			count += 1
	return count

func _check_for_updates() -> void:
	for pkg in available_updates:
		var pkg_id: String = pkg.get("package_id", "")
		if pkg_id not in installed_packages:
			update_available.emit(pkg_id)

func _save_local_state() -> void:
	var save_data: Dictionary = {
		"schema_version": schema_version,
		"installed_packages": installed_packages,
		"current_package_version": current_package_version
	}
	var file := FileAccess.open("user://content_state.json", FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(save_data))
		file.close()

func _load_local_state() -> void:
	if not FileAccess.file_exists("user://content_state.json"):
		return
	var file := FileAccess.open("user://content_state.json", FileAccess.READ)
	if file:
		var content: String = file.get_as_text()
		file.close()
		var parsed: Variant = JSON.parse_string(content)
		if typeof(parsed) == TYPE_DICTIONARY:
			var data: Dictionary = parsed
			if data.has("schema_version"):
				schema_version = data["schema_version"]
			if data.has("installed_packages"):
				installed_packages = data["installed_packages"]
			if data.has("current_package_version"):
				current_package_version = data["current_package_version"]

func reset() -> void:
	available_updates.clear()
	installed_packages.clear()
	current_package_version = ""
	_save_local_state()
