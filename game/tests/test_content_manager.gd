extends Node
## ContentManager GUT 测试
## 覆盖内容更新管理、包安装/卸载、状态查询等核心逻辑

var content_manager: Node

func before_all() -> void:
	# 动态加载 ContentManager 脚本
	var script: GDScript = load("res://scripts/autoload/ContentManager.gd")
	content_manager = script.new()
	add_child(content_manager)

func before_each() -> void:
	content_manager.reset()

func test_initial_state() -> void:
	assert_eq(content_manager.available_updates.size(), 0, "available_updates should be empty initially")
	assert_eq(content_manager.installed_packages.size(), 0, "installed_packages should be empty initially")
	assert_eq(content_manager.current_package_version, "", "current_package_version should be empty initially")
	assert_eq(content_manager.schema_version, 1, "schema_version should be 1")
	assert_false(content_manager.is_loading, "is_loading should be false initially")
	assert_true(content_manager.last_error.is_empty(), "last_error should be empty initially")
	assert_eq(content_manager.last_check_time, 0.0, "last_check_time should be 0.0 initially")

func test_signals_declared() -> void:
	assert_true(content_manager.has_signal("content_updates_loaded"), "should have content_updates_loaded signal")
	assert_true(content_manager.has_signal("content_package_loaded"), "should have content_package_loaded signal")
	assert_true(content_manager.has_signal("update_available"), "should have update_available signal")
	assert_true(content_manager.has_signal("content_error"), "should have content_error signal")
	assert_true(content_manager.has_signal("auth_error"), "should have auth_error signal")
	assert_true(content_manager.has_signal("loading_changed"), "should have loading_changed signal")

func test_reset() -> void:
	content_manager.available_updates.append({"package_id": "test_pkg"})
	content_manager.installed_packages.append("test_pkg")
	content_manager.current_package_version = "1.0"
	content_manager.is_loading = true
	content_manager.last_error = {"code": "ERR"}
	content_manager.last_check_time = 100.0
	
	content_manager.reset()
	
	assert_eq(content_manager.available_updates.size(), 0, "available_updates should be cleared after reset")
	assert_eq(content_manager.installed_packages.size(), 0, "installed_packages should be cleared after reset")
	assert_eq(content_manager.current_package_version, "", "current_package_version should be empty after reset")
	assert_false(content_manager.is_loading, "is_loading should be false after reset")
	assert_true(content_manager.last_error.is_empty(), "last_error should be empty after reset")
	assert_eq(content_manager.last_check_time, 0.0, "last_check_time should be 0.0 after reset")

func test_is_package_installed_when_empty() -> void:
	assert_false(content_manager.is_package_installed("pkg_1"), "should return false when not installed")

func test_is_package_installed_after_install() -> void:
	content_manager.installed_packages.append("pkg_1")
	assert_true(content_manager.is_package_installed("pkg_1"), "should return true after install")

func test_uninstall_package_success() -> void:
	content_manager.installed_packages.append("pkg_1")
	var result: bool = content_manager.uninstall_package("pkg_1")
	assert_true(result, "uninstall should succeed for installed package")
	assert_false(content_manager.is_package_installed("pkg_1"), "package should not be installed after uninstall")

func test_uninstall_package_not_installed() -> void:
	var result: bool = content_manager.uninstall_package("nonexistent")
	assert_false(result, "uninstall should fail for non-installed package")

func test_has_updates_available_empty() -> void:
	assert_false(content_manager.has_updates_available(), "should return false when no updates")

func test_has_updates_available_with_uninstalled() -> void:
	content_manager.available_updates.append({"package_id": "pkg_new"})
	assert_true(content_manager.has_updates_available(), "should return true when there are uninstalled updates")

func test_has_updates_available_all_installed() -> void:
	content_manager.available_updates.append({"package_id": "pkg_1"})
	content_manager.installed_packages.append("pkg_1")
	assert_false(content_manager.has_updates_available(), "should return false when all updates installed")

func test_get_update_count_empty() -> void:
	assert_eq(content_manager.get_update_count(), 0, "should return 0 when no updates")

func test_get_update_count_with_updates() -> void:
	content_manager.available_updates.append({"package_id": "pkg_1"})
	content_manager.available_updates.append({"package_id": "pkg_2"})
	content_manager.installed_packages.append("pkg_1")
	assert_eq(content_manager.get_update_count(), 1, "should return count of uninstalled updates")

func test_get_available_updates_list() -> void:
	content_manager.available_updates.append({"package_id": "pkg_1"})
	content_manager.available_updates.append({"package_id": "pkg_2"})
	content_manager.installed_packages.append("pkg_1")
	
	var updates: Array = content_manager.get_available_updates_list()
	assert_eq(updates.size(), 1, "should return only uninstalled updates")
	assert_eq(updates[0].get("package_id", ""), "pkg_2", "should return the uninstalled package")

func test_get_package_status_installed() -> void:
	content_manager.installed_packages.append("pkg_1")
	assert_eq(content_manager.get_package_status("pkg_1"), "installed", "should return 'installed'")

func test_get_package_status_available() -> void:
	content_manager.available_updates.append({"package_id": "pkg_1"})
	assert_eq(content_manager.get_package_status("pkg_1"), "available", "should return 'available'")

func test_get_package_status_unknown() -> void:
	assert_eq(content_manager.get_package_status("nonexistent"), "unknown", "should return 'unknown'")

func test_is_auth_error_default() -> void:
	assert_false(content_manager.is_auth_error(), "should return false by default")

func test_is_auth_error_with_auth_error() -> void:
	content_manager.last_error = {"is_auth_error": true}
	assert_true(content_manager.is_auth_error(), "should return true when auth error")

func test_is_server_error_default() -> void:
	assert_false(content_manager.is_server_error(), "should return false by default")

func test_is_server_error_with_server_error() -> void:
	content_manager.last_error = {"is_server_error": true}
	assert_true(content_manager.is_server_error(), "should return true when server error")

func test_auto_check_interval_default() -> void:
	assert_eq(content_manager.auto_check_interval, 300.0, "default auto_check_interval should be 300.0")

func test_install_package_empty_data() -> void:
	# fetch_package 返回空数据时应失败
	var result: bool = content_manager.install_package("nonexistent")
	assert_false(result, "install should fail when package data is empty")
