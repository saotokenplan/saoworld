extends "res://addons/gut/test.gd"
## APIManager 单元测试

func test_default_base_url() -> void:
	var api := APIManager
	assert_true(api.base_url.find("localhost") != -1, "默认 base_url 应包含 localhost")

func test_auth_token_management() -> void:
	var api := APIManager
	api.set_auth_token("test_token_123")
	assert_eq(api.auth_token, "test_token_123", "Token 应正确设置")
	api.clear_auth_token()
	assert_eq(api.auth_token, "", "Token 应正确清除")

func test_trace_id_management() -> void:
	var api := APIManager
	api.set_trace_id("trace_test_001")
	assert_eq(api.trace_id, "trace_test_001", "Trace ID 应正确设置")
	api.set_trace_id("")

func test_generate_request_id() -> void:
	var api := APIManager
	var req_id_1: String = api.generate_request_id()
	var req_id_2: String = api.generate_request_id()
	assert_true(req_id_1.begins_with("req_"), "请求ID应以 req_ 开头")
	assert_neq(req_id_1, req_id_2, "两次生成的请求ID应不同")
