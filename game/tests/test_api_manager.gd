extends "res://addons/gut/test.gd"

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

func test_error_code_constants_exist() -> void:
	var api := APIManager
	assert_true(api.ERROR_CODES.has("NO_OPEN_VOTE_CYCLE"), "ERROR_CODES 应包含 NO_OPEN_VOTE_CYCLE")
	assert_true(api.ERROR_CODES.has("INVALID_VOTE_STATE"), "ERROR_CODES 应包含 INVALID_VOTE_STATE")
	assert_true(api.ERROR_CODES.has("ALREADY_VOTED"), "ERROR_CODES 应包含 ALREADY_VOTED")
	assert_true(api.ERROR_CODES.has("TOKEN_EXPIRED"), "ERROR_CODES 应包含 TOKEN_EXPIRED")
	assert_true(api.ERROR_CODES.has("INTERNAL_ERROR"), "ERROR_CODES 应包含 INTERNAL_ERROR")

func test_error_code_status_mapping() -> void:
	var api := APIManager
	assert_eq(api.ERROR_CODES["ALREADY_VOTED"]["status"], 409, "ALREADY_VOTED 状态码应为 409")
	assert_eq(api.ERROR_CODES["TOKEN_EXPIRED"]["status"], 401, "TOKEN_EXPIRED 状态码应为 401")
	assert_eq(api.ERROR_CODES["INTERNAL_ERROR"]["status"], 500, "INTERNAL_ERROR 状态码应为 500")

func test_get_error_code_by_status() -> void:
	var api := APIManager
	assert_eq(api._get_error_code_by_status(400), "BAD_REQUEST")
	assert_eq(api._get_error_code_by_status(401), "INVALID_TOKEN")
	assert_eq(api._get_error_code_by_status(403), "FORBIDDEN")
	assert_eq(api._get_error_code_by_status(404), "NOT_FOUND")
	assert_eq(api._get_error_code_by_status(409), "CONFLICT")
	assert_eq(api._get_error_code_by_status(429), "RATE_LIMITED")
	assert_eq(api._get_error_code_by_status(500), "INTERNAL_ERROR")

func test_get_error_message() -> void:
	var api := APIManager
	var msg: String = api._get_error_message("ALREADY_VOTED")
	assert_true(msg.length() > 0, "错误消息不应为空")

func test_build_error_includes_status() -> void:
	var api := APIManager
	var err: Dictionary = api._build_error("ALREADY_VOTED", "Test error", "req_001")
	assert_eq(err["status_code"], 409, "错误应包含正确的状态码")
	assert_eq(err["code"], "ALREADY_VOTED", "错误应包含正确的错误码")

func test_can_retry_safe_methods() -> void:
	var api := APIManager
	assert_true(api._can_retry("GET"))
	assert_true(api._can_retry("HEAD"))
	assert_true(api._can_retry("OPTIONS"))
	assert_false(api._can_retry("POST"))
	assert_false(api._can_retry("PUT"))
	assert_false(api._can_retry("DELETE"))

func test_http_methods_available() -> void:
	var api := APIManager
	assert_true(api.has_method("get"))
	assert_true(api.has_method("post"))
	assert_true(api.has_method("put"))
	assert_true(api.has_method("delete"))

func test_async_http_methods_available() -> void:
	var api := APIManager
	assert_true(api.has_method("get_async"))
	assert_true(api.has_method("post_async"))
	assert_true(api.has_method("put_async"))
	assert_true(api.has_method("delete_async"))

func test_request_pool_initial_empty() -> void:
	var api := APIManager
	assert_eq(api._request_pool.size(), 0, "初始连接池应为空")

func test_request_pool_max_size() -> void:
	var api := APIManager
	assert_eq(api._max_pool_size, 5, "最大连接池大小应为 5")

func test_retry_delay_with_jitter() -> void:
	var api := APIManager
	api.retry_delay = 2.0
	api.retry_jitter_factor = 0.25
	api.max_retry_interval = 30.0
	
	var delay_0: float = api._calculate_retry_delay(0)
	var delay_1: float = api._calculate_retry_delay(1)
	var delay_2: float = api._calculate_retry_delay(2)
	
	assert_true(delay_0 >= 1.5 and delay_0 <= 2.5, "第0次重试延迟应在 1.5-2.5 秒之间")
	assert_true(delay_1 >= 3.0 and delay_1 <= 5.0, "第1次重试延迟应在 3.0-5.0 秒之间")
	assert_true(delay_2 >= 6.0 and delay_2 <= 10.0, "第2次重试延迟应在 6.0-10.0 秒之间")

func test_retry_delay_clamped() -> void:
	var api := APIManager
	api.retry_delay = 2.0
	api.retry_jitter_factor = 0.25
	api.max_retry_interval = 5.0
	
	var delay: float = api._calculate_retry_delay(10)
	assert_true(delay <= 5.0, "重试延迟不应超过最大间隔")

func test_retry_delay_minimum() -> void:
	var api := APIManager
	api.retry_delay = 2.0
	api.retry_jitter_factor = 0.25
	
	var delay: float = api._calculate_retry_delay(0)
	assert_true(delay >= 2.0, "重试延迟不应低于最小延迟")

func test_max_retry_interval_config() -> void:
	var api := APIManager
	assert_true(api.max_retry_interval > 0, "最大重试间隔应大于 0")

func test_retry_jitter_factor_config() -> void:
	var api := APIManager
	assert_true(api.retry_jitter_factor >= 0.0 and api.retry_jitter_factor <= 1.0, 
		"抖动因子应在 0.0-1.0 之间")