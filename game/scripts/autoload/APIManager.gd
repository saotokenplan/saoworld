extends Node
## 后端 API 请求管理器
## 负责统一发送 API 请求、解析响应、处理错误、管理认证

signal request_started(request_id: String)
signal request_completed(request_id: String, response: Dictionary)
signal request_failed(request_id: String, error: Dictionary)

var base_url: String = "http://localhost:8000/api/v1"
var auth_token: String = ""
var trace_id: String = ""
var request_timeout: float = 30.0
var schema_version: int = 1

func _ready() -> void:
	_load_config()

func set_base_url(url: String) -> void:
	base_url = url

func set_auth_token(token: String) -> void:
	auth_token = token

func clear_auth_token() -> void:
	auth_token = ""

func set_trace_id(tid: String) -> void:
	trace_id = tid

func generate_request_id() -> String:
	return "req_%s" % str(Time.get_unix_time_from_system())

func get(endpoint: String, headers: Dictionary = {}) -> Dictionary:
	return _make_request("GET", endpoint, {}, headers)

func post(endpoint: String, body: Dictionary = {}, headers: Dictionary = {}, idempotency_key: String = "") -> Dictionary:
	if idempotency_key != "":
		headers["Idempotency-Key"] = idempotency_key
	return _make_request("POST", endpoint, body, headers)

func _make_request(method: String, endpoint: String, body: Dictionary, extra_headers: Dictionary) -> Dictionary:
	var request_id: String = generate_request_id()
	request_started.emit(request_id)
	
	var url: String = base_url + endpoint
	var http_request := HTTPRequest.new()
	add_child(http_request)
	
	var headers: PackedStringArray = PackedStringArray()
	headers.append("Content-Type: application/json")
	
	if auth_token != "":
		headers.append("Authorization: Bearer %s" % auth_token)
	
	if trace_id != "":
		headers.append("X-Trace-Id: %s" % trace_id)
	
	headers.append("X-Request-Id: %s" % request_id)
	
	if GameState.player_id != "":
		headers.append("X-Player-Id: %s" % GameState.player_id)
	
	for key in extra_headers.keys():
		headers.append("%s: %s" % [key, extra_headers[key]])
	
	var error_code: Error = OK
	var request_body: String = ""
	
	if method == "POST" or method == "PUT" or method == "PATCH":
		request_body = JSON.stringify(body)
		error_code = http_request.request(url, headers, HTTPClient.METHOD_POST, request_body)
	else:
		error_code = http_request.request(url, headers, HTTPClient.METHOD_GET)
	
	if error_code != OK:
		var err: Dictionary = _build_error("NETWORK_ERROR", "Failed to send request: %s" % str(error_code), request_id)
		request_failed.emit(request_id, err)
		_remove_request(http_request)
		return err
	
	var completed: bool = false
	var response_result: Dictionary = {}
	
	http_request.request_completed.connect(
		func _on_request_completed(_result: int, response_code: int, _headers: PackedStringArray, _body: PackedByteArray) -> void:
			var response_text: String = _body.get_string_from_utf8()
			var parsed: Variant = JSON.parse_string(response_text)
			
			if typeof(parsed) == TYPE_DICTIONARY:
				response_result = _parse_response(parsed, response_code, request_id)
			else:
				response_result = _build_error("INVALID_RESPONSE", "Invalid JSON response", request_id)
			
			completed = true
			_remove_request(http_request)
	)
	
	var timeout_time: float = request_timeout
	var elapsed: float = 0.0
	while not completed and elapsed < timeout_time:
		await get_tree().process_frame
		elapsed += get_process_delta_time()
	
	if not completed:
		http_request.cancel_request()
		_remove_request(http_request)
		var timeout_err: Dictionary = _build_error("TIMEOUT", "Request timed out", request_id)
		request_failed.emit(request_id, timeout_err)
		return timeout_err
	
	return response_result

func _parse_response(data: Dictionary, status_code: int, request_id: String) -> Dictionary:
	if status_code >= 200 and status_code < 300:
		request_completed.emit(request_id, data)
		return {
			"success": true,
			"status_code": status_code,
			"request_id": data.get("request_id", request_id),
			"trace_id": data.get("trace_id", trace_id),
			"data": data.get("data", {}),
			"meta": data.get("meta", {})
		}
	else:
		var err: Dictionary = {
			"success": false,
			"status_code": status_code,
			"request_id": data.get("request_id", request_id),
			"trace_id": data.get("trace_id", trace_id),
			"code": data.get("code", "UNKNOWN_ERROR"),
			"message": data.get("message", "Unknown error"),
			"details": data.get("details", [])
		}
		request_failed.emit(request_id, err)
		return err

func _build_error(code: String, message: String, request_id: String) -> Dictionary:
	return {
		"success": false,
		"status_code": 0,
		"request_id": request_id,
		"trace_id": trace_id,
		"code": code,
		"message": message,
		"details": []
	}

func _remove_request(req: HTTPRequest) -> void:
	if is_instance_valid(req):
		req.queue_free()

func _load_config() -> void:
	var config_path: String = "res://data/config/game_config.tres"
	if ResourceLoader.exists(config_path):
		var config := load(config_path)
		if config and config.has("api_base_url"):
			base_url = config.api_base_url
