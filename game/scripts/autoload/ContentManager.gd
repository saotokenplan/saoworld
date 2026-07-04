extends Node

signal content_updates_loaded
signal content_package_loaded
signal update_available(package_id: String)
signal content_error(error_code: String, message: String)
signal auth_error(message: String)
signal loading_changed(is_loading: bool)

var available_updates: Array[Dictionary] = []
var installed_packages: Array[String] = []
var current_package_version: String = ""
var schema_version: int = 1
var is_loading: bool = false
var last_error: Dictionary = {}
var auto_check_interval: float = 300.0
var last_check_time: float = 0.0

func _ready() -> void:
	_load_local_state()
	APIManager.auth_error.connect(_on_auth_error)

func _on_auth_error(request_id: String, message: String) -> void:
	auth_error.emit(message)

func fetch_updates() -> void:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/content/updates")
	
	if result.get("success", false):
		_handle_updates_success(result)
	else:
		_handle_content_error(result)
	
	_set_loading(false)

func _handle_updates_success(result: Dictionary) -> void:
	var data: Dictionary = result.get("data", {})
	available_updates = data.get("items", [])
	last_check_time = Time.get_unix_time_from_system()
	_check_for_updates()
	last_error.clear()
	content_updates_loaded.emit()

func _handle_content_error(result: Dictionary) -> void:
	var err_code: String = result.get("code", "UNKNOWN_ERROR")
	var err_message: String = result.get("message", "内容更新失败")
	
	last_error = {
		"code": err_code,
		"message": err_message,
		"is_auth_error": result.get("is_auth_error", false),
		"is_server_error": result.get("is_server_error", false)
	}
	
	content_error.emit(err_code, err_message)

func fetch_package(package_id: String) -> Dictionary:
	_set_loading(true)
	var result: Dictionary = APIManager.get("/content/packages/%s" % package_id)
	
	if result.get("success", false):
		var data: Dictionary = result.get("data", {})
		last_error.clear()
		content_package_loaded.emit()
		_set_loading(false)
		return data
	else:
		_handle_content_error(result)
		_set_loading(false)
		return {}

func install_package(package_id: String) -> bool:
	var pkg_data: Dictionary = fetch_package(package_id)
	if pkg_data.empty():
		return false
	
	var pkg_version: String = pkg_data.get("version", "")
	if pkg_version == "":
		return false
	
	installed_packages.append(package_id)
	current_package_version = pkg_version
	_save_local_state()
	return true

func uninstall_package(package_id: String) -> bool:
	if package_id not in installed_packages:
		return false
	
	installed_packages.erase(package_id)
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

func get_available_updates_list() -> Array[Dictionary]:
	var updates: Array[Dictionary] = []
	for pkg in available_updates:
		var pkg_id: String = pkg.get("package_id", "")
		if pkg_id not in installed_packages:
			updates.append(pkg)
	return updates

func check_for_updates_if_needed() -> void:
	var now: float = Time.get_unix_time_from_system()
	if now - last_check_time >= auto_check_interval:
		fetch_updates()

func force_check_updates() -> void:
	fetch_updates()

func get_package_status(package_id: String) -> String:
	if package_id in installed_packages:
		return "installed"
	for pkg in available_updates:
		if pkg.get("package_id", "") == package_id:
			return "available"
	return "unknown"

func _check_for_updates() -> void:
	for pkg in available_updates:
		var pkg_id: String = pkg.get("package_id", "")
		if pkg_id not in installed_packages:
			update_available.emit(pkg_id)

func _save_local_state() -> void:
	var save_data: Dictionary = {
		"schema_version": schema_version,
		"installed_packages": installed_packages,
		"current_package_version": current_package_version,
		"last_check_time": last_check_time
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
			if data.has("last_check_time"):
				last_check_time = data["last_check_time"]

func _set_loading(loading: bool) -> void:
	if is_loading != loading:
		is_loading = loading
		loading_changed.emit(is_loading)

func is_auth_error() -> bool:
	return last_error.get("is_auth_error", false)

func is_server_error() -> bool:
	return last_error.get("is_server_error", false)

func reset() -> void:
	available_updates.clear()
	installed_packages.clear()
	current_package_version = ""
	is_loading = false
	last_error.clear()
	last_check_time = 0.0
	_save_local_state()