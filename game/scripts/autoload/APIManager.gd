extends Node

signal request_started(request_id: String)
signal request_completed(request_id: String, response: Dictionary)
signal request_failed(request_id: String, error: Dictionary)
signal auth_error(request_id: String, message: String)
signal event_batch_submitted(event_count: int, success: bool)
signal event_submit_failed(error: Dictionary)

var base_url: String = "http://localhost:8000/api/v1"
var auth_token: String = ""
var trace_id: String = ""
var request_timeout: float = 30.0
var schema_version: int = 1
var max_retries: int = 2
var retry_delay: float = 2.0
var max_retry_interval: float = 30.0
var retry_jitter_factor: float = 0.25

var _request_pool: Array[HTTPRequest] = []
var _max_pool_size: int = 5
var _pending_requests: Dictionary = {}

var event_batch_interval: float = 30.0
var max_batch_size: int = 50
var event_queue: Array[Dictionary] = []
var event_flush_timer: Timer = null
var _event_id_counter: int = 0

const EVENT_TYPES: Dictionary = {
	"enter_region": {"name": "玩家进入区域", "realtime": false},
	"leave_region": {"name": "玩家离开区域", "realtime": false},
	"complete_quest": {"name": "玩家完成任务", "realtime": true},
	"interact_npc": {"name": "玩家与NPC交互", "realtime": false},
	"vote_submit": {"name": "玩家提交投票", "realtime": true},
	"view_content": {"name": "玩家查看内容", "realtime": false},
	"spend_resource": {"name": "玩家消耗资源", "realtime": false}
}

const ERROR_CODES: Dictionary = {
	"NO_OPEN_VOTE_CYCLE": {"message": "当前没有开放的投票周期", "status": 404},
	"INVALID_VOTE_STATE": {"message": "投票周期状态不允许投票", "status": 409},
	"CANDIDATE_NOT_FOUND": {"message": "候选项不存在或不属于当前周期", "status": 404},
	"CANDIDATE_NOT_ACTIVE": {"message": "候选项当前不可投票", "status": 409},
	"ALREADY_VOTED": {"message": "您在本周期已投票", "status": 409},
	"INVALID_PLAYER_ID": {"message": "无效的玩家 ID", "status": 400},
	"INTERNAL_ERROR": {"message": "服务器内部错误", "status": 500},
	"RATE_LIMITED": {"message": "请求过于频繁，请稍后重试", "status": 429},
	"TOKEN_EXPIRED": {"message": "登录已过期，请重新登录", "status": 401},
	"INVALID_TOKEN": {"message": "无效的登录凭证", "status": 401},
	"FORBIDDEN": {"message": "权限不足", "status": 403},
	"NOT_FOUND": {"message": "资源未找到", "status": 404},
	"BAD_REQUEST": {"message": "请求参数错误", "status": 400},
	"NETWORK_ERROR": {"message": "网络连接失败", "status": 0},
	"TIMEOUT": {"message": "请求超时", "status": 0},
	"INVALID_RESPONSE": {"message": "无效的响应数据", "status": 0},
	
	"VOTE_CYCLE_NOT_FOUND": {"message": "投票周期不存在", "status": 404},
	"VOTE_CYCLE_CONFLICT": {"message": "当前章节已存在开放中的投票周期", "status": 409},
	"INVALID_ARGUMENT": {"message": "参数无效", "status": 400},
	
	"REGION_NOT_FOUND": {"message": "区域不存在", "status": 404},
	"INVALID_REGION_STATUS": {"message": "区域状态不允许当前操作", "status": 409},
	
	"PACKAGE_NOT_FOUND": {"message": "内容包不存在", "status": 404},
	"INVALID_PACKAGE_STATE": {"message": "内容包状态不允许当前操作", "status": 409},
	
	"REQUEST_NOT_FOUND": {"message": "生成请求不存在", "status": 404},
	"OBJECT_NOT_FOUND": {"message": "生成对象不存在", "status": 404},
	"INVALID_REQUEST_STATUS": {"message": "生成请求状态不允许当前操作", "status": 409},
	"INVALID_OBJECT_STATUS": {"message": "生成对象状态不允许当前操作", "status": 409},
	"MAX_RETRIES_EXCEEDED": {"message": "已达到最大重试次数", "status": 409},
	
	"REVIEW_NOT_FOUND": {"message": "审核记录不存在", "status": 404},
	"NO_REVIEWS_FOUND": {"message": "该对象没有审核记录", "status": 404},
	"INVALID_REVIEW_STATUS": {"message": "审核记录状态不允许当前操作", "status": 409},
	
	"PLAYER_NOT_FOUND": {"message": "玩家不存在", "status": 404},
	"INVALID_QUEST_STATUS": {"message": "无效的任务状态", "status": 400},
	
	"ACTION_NOT_FOUND": {"message": "运营操作记录不存在", "status": 404},
	
	"SERVICE_UNAVAILABLE": {"message": "后端服务不可用", "status": 503},
	"GATEWAY_TIMEOUT": {"message": "请求超时", "status": 504}
}

func _ready() -> void:
	_load_config()
	_init_event_system()

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

func put(endpoint: String, body: Dictionary = {}, headers: Dictionary = {}) -> Dictionary:
	return _make_request("PUT", endpoint, body, headers)

func delete(endpoint: String, headers: Dictionary = {}) -> Dictionary:
	return _make_request("DELETE", endpoint, {}, headers)

func _make_request(method: String, endpoint: String, body: Dictionary, extra_headers: Dictionary, retry_count: int = 0) -> Dictionary:
	var request_id: String = generate_request_id()
	request_started.emit(request_id)
	
	var url: String = base_url + endpoint
	var http_request := _get_request_from_pool()
	if not is_instance_valid(http_request):
		http_request = HTTPRequest.new()
		add_child(http_request)
	
	var headers: PackedStringArray = _build_request_headers(extra_headers, request_id)
	
	var error_code: Error = OK
	var request_body: String = ""
	
	if method == "POST":
		request_body = JSON.stringify(body)
		error_code = http_request.request(url, headers, HTTPClient.METHOD_POST, request_body)
	elif method == "PUT":
		request_body = JSON.stringify(body)
		error_code = http_request.request(url, headers, HTTPClient.METHOD_PUT, request_body)
	elif method == "DELETE":
		error_code = http_request.request(url, headers, HTTPClient.METHOD_DELETE)
	else:
		error_code = http_request.request(url, headers, HTTPClient.METHOD_GET)
	
	if error_code != OK:
		var err: Dictionary = _build_error("NETWORK_ERROR", "Failed to send request: %s" % str(error_code), request_id)
		request_failed.emit(request_id, err)
		_return_request_to_pool(http_request)
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
			_return_request_to_pool(http_request)
	)
	
	var timeout_time: float = request_timeout
	var elapsed: float = 0.0
	while not completed and elapsed < timeout_time:
		await get_tree().process_frame
		elapsed += get_process_delta_time()
	
	if not completed:
		http_request.cancel_request()
		_return_request_to_pool(http_request)
		if _can_retry(method) and retry_count < max_retries:
			var delay: float = _calculate_retry_delay(retry_count)
			await get_tree().create_timer(delay).timeout
			return _make_request(method, endpoint, body, extra_headers, retry_count + 1)
		
		var timeout_err: Dictionary = _build_error("TIMEOUT", "Request timed out", request_id)
		request_failed.emit(request_id, timeout_err)
		return timeout_err
	
	if not response_result.get("success", false):
		var err_code: String = response_result.get("code", "")
		if err_code == "TOKEN_EXPIRED" or err_code == "INVALID_TOKEN":
			auth_error.emit(request_id, response_result.get("message", "Auth error"))
		if _can_retry(method) and response_result.get("status_code", 0) == 500 and retry_count < max_retries:
			var delay: float = _calculate_retry_delay(retry_count)
			await get_tree().create_timer(delay).timeout
			return _make_request(method, endpoint, body, extra_headers, retry_count + 1)
	
	return response_result

func _can_retry(method: String) -> bool:
	var safe_methods: Array[String] = ["GET", "HEAD", "OPTIONS"]
	return method in safe_methods

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
		var err_code: String = data.get("code", _get_error_code_by_status(status_code))
		var err_message: String = data.get("message", _get_error_message(err_code))
		
		var err: Dictionary = {
			"success": false,
			"status_code": status_code,
			"request_id": data.get("request_id", request_id),
			"trace_id": data.get("trace_id", trace_id),
			"code": err_code,
			"message": err_message,
			"details": data.get("details", []),
			"is_auth_error": status_code == 401,
			"is_rate_limited": status_code == 429,
			"is_client_error": status_code >= 400 and status_code < 500,
			"is_server_error": status_code >= 500
		}
		request_failed.emit(request_id, err)
		return err

func _get_error_code_by_status(status_code: int) -> String:
	match status_code:
		400: return "BAD_REQUEST"
		401: return "INVALID_TOKEN"
		403: return "FORBIDDEN"
		404: return "NOT_FOUND"
		409: return "CONFLICT"
		429: return "RATE_LIMITED"
		500: return "INTERNAL_ERROR"
		_: return "UNKNOWN_ERROR"

func _get_error_message(error_code: String) -> String:
	if ERROR_CODES.has(error_code):
		return ERROR_CODES[error_code]["message"]
	return "未知错误"

func _build_error(code: String, message: String, request_id: String) -> Dictionary:
	var status: int = 0
	if ERROR_CODES.has(code):
		status = ERROR_CODES[code]["status"]
	
	return {
		"success": false,
		"status_code": status,
		"request_id": request_id,
		"trace_id": trace_id,
		"code": code,
		"message": message,
		"details": [],
		"is_auth_error": status == 401,
		"is_rate_limited": status == 429,
		"is_client_error": status >= 400 and status < 500,
		"is_server_error": status >= 500
	}

func _remove_request(req: HTTPRequest) -> void:
	if is_instance_valid(req):
		req.queue_free()

func _get_request_from_pool() -> HTTPRequest:
	for req in _request_pool:
		if req and is_instance_valid(req) and not req.is_processing():
			return req
	if _request_pool.size() < _max_pool_size:
		var new_req := HTTPRequest.new()
		new_req.name = "HTTPRequest_%d" % _request_pool.size()
		add_child(new_req)
		_request_pool.append(new_req)
		return new_req
	return HTTPRequest.new()

func _return_request_to_pool(req: HTTPRequest) -> void:
	if not req:
		return
	for existing_req in _request_pool:
		if existing_req == req:
			return
	if _request_pool.size() < _max_pool_size:
		if not is_instance_valid(req):
			req = HTTPRequest.new()
		req.name = "HTTPRequest_%d" % _request_pool.size()
		add_child(req)
		_request_pool.append(req)
	else:
		if is_instance_valid(req):
			req.queue_free()

func _calculate_retry_delay(retry_count: int) -> float:
	var base_delay: float = retry_delay * pow(2, retry_count)
	var jitter: float = base_delay * retry_jitter_factor * (rand_range(-1.0, 1.0))
	return min(max(base_delay + jitter, retry_delay), max_retry_interval)

func get_async(endpoint: String, headers: Dictionary = {}, callback: Callable = null) -> String:
	return _make_request_async("GET", endpoint, {}, headers, callback)

func post_async(endpoint: String, body: Dictionary = {}, headers: Dictionary = {}, idempotency_key: String = "", callback: Callable = null) -> String:
	if idempotency_key != "":
		headers["Idempotency-Key"] = idempotency_key
	return _make_request_async("POST", endpoint, body, headers, callback)

func put_async(endpoint: String, body: Dictionary = {}, headers: Dictionary = {}, callback: Callable = null) -> String:
	return _make_request_async("PUT", endpoint, body, headers, callback)

func delete_async(endpoint: String, headers: Dictionary = {}, callback: Callable = null) -> String:
	return _make_request_async("DELETE", endpoint, {}, headers, callback)

func _make_request_async(method: String, endpoint: String, body: Dictionary, extra_headers: Dictionary, callback: Callable = null, retry_count: int = 0) -> String:
	var request_id: String = generate_request_id()
	request_started.emit(request_id)
	
	var url: String = base_url + endpoint
	var http_request := _get_request_from_pool()
	if not is_instance_valid(http_request):
		http_request = HTTPRequest.new()
		add_child(http_request)
	
	var headers: PackedStringArray = _build_request_headers(extra_headers, request_id)
	
	var error_code: Error = OK
	var request_body: String = ""
	
	if method == "POST":
		request_body = JSON.stringify(body)
		error_code = http_request.request(url, headers, HTTPClient.METHOD_POST, request_body)
	elif method == "PUT":
		request_body = JSON.stringify(body)
		error_code = http_request.request(url, headers, HTTPClient.METHOD_PUT, request_body)
	elif method == "DELETE":
		error_code = http_request.request(url, headers, HTTPClient.METHOD_DELETE)
	else:
		error_code = http_request.request(url, headers, HTTPClient.METHOD_GET)
	
	if error_code != OK:
		_return_request_to_pool(http_request)
		var err: Dictionary = _build_error("NETWORK_ERROR", "Failed to send request: %s" % str(error_code), request_id)
		request_failed.emit(request_id, err)
		if callback:
			callback.call(err)
		return request_id
	
	var timeout_timer: Timer = Timer.new()
	timeout_timer.wait_time = request_timeout
	timeout_timer.autostart = true
	timeout_timer.one_shot = true
	add_child(timeout_timer)
	
	_pending_requests[request_id] = {
		"http_request": http_request,
		"timeout_timer": timeout_timer,
		"method": method,
		"endpoint": endpoint,
		"body": body,
		"extra_headers": extra_headers,
		"callback": callback,
		"retry_count": retry_count
	}
	
	http_request.request_completed.connect(
		func(_result: int, response_code: int, _headers: PackedStringArray, _body: PackedByteArray) -> void:
			_handle_async_response(request_id, response_code, _body)
	)
	
	timeout_timer.timeout.connect(
		func() -> void:
			_handle_async_timeout(request_id)
	)
	
	return request_id

func _build_request_headers(extra_headers: Dictionary, request_id: String) -> PackedStringArray:
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
	
	return headers

func _handle_async_response(request_id: String, response_code: int, body: PackedByteArray) -> void:
	if not _pending_requests.has(request_id):
		return
	
	var pending := _pending_requests[request_id]
	var http_request := pending["http_request"]
	var timeout_timer := pending["timeout_timer"]
	var callback := pending["callback"]
	var method := pending["method"]
	var endpoint := pending["endpoint"]
	var body_data := pending["body"]
	var extra_headers := pending["extra_headers"]
	var retry_count := pending["retry_count"]
	
	if is_instance_valid(timeout_timer):
		timeout_timer.stop()
		timeout_timer.queue_free()
	
	_return_request_to_pool(http_request)
	
	var response_text: String = body.get_string_from_utf8()
	var parsed: Variant = JSON.parse_string(response_text)
	
	var response_result: Dictionary = {}
	if typeof(parsed) == TYPE_DICTIONARY:
		response_result = _parse_response(parsed, response_code, request_id)
	else:
		response_result = _build_error("INVALID_RESPONSE", "Invalid JSON response", request_id)
	
	_pending_requests.erase(request_id)
	
	if not response_result.get("success", false):
		var err_code: String = response_result.get("code", "")
		if err_code == "TOKEN_EXPIRED" or err_code == "INVALID_TOKEN":
			auth_error.emit(request_id, response_result.get("message", "Auth error"))
		if _can_retry(method) and response_result.get("status_code", 0) == 500 and retry_count < max_retries:
			var delay: float = _calculate_retry_delay(retry_count)
			var timer := Timer.new()
			timer.wait_time = delay
			timer.autostart = true
			timer.one_shot = true
			timer.timeout.connect(
				func() -> void:
					_make_request_async(method, endpoint, body_data, extra_headers, callback, retry_count + 1)
					timer.queue_free()
			)
			add_child(timer)
			return
	
	if callback:
		callback.call(response_result)

func _handle_async_timeout(request_id: String) -> void:
	if not _pending_requests.has(request_id):
		return
	
	var pending := _pending_requests[request_id]
	var http_request := pending["http_request"]
	var callback := pending["callback"]
	var method := pending["method"]
	var endpoint := pending["endpoint"]
	var body_data := pending["body"]
	var extra_headers := pending["extra_headers"]
	var retry_count := pending["retry_count"]
	
	http_request.cancel_request()
	_return_request_to_pool(http_request)
	
	_pending_requests.erase(request_id)
	
	if _can_retry(method) and retry_count < max_retries:
		var delay: float = _calculate_retry_delay(retry_count)
		var timer := Timer.new()
		timer.wait_time = delay
		timer.autostart = true
		timer.one_shot = true
		timer.timeout.connect(
			func() -> void:
				_make_request_async(method, endpoint, body_data, extra_headers, callback, retry_count + 1)
				timer.queue_free()
		)
		add_child(timer)
		return
	
	var timeout_err: Dictionary = _build_error("TIMEOUT", "Request timed out", request_id)
	request_failed.emit(request_id, timeout_err)
	
	if callback:
		callback.call(timeout_err)

func _load_config() -> void:
	var config_path: String = "res://data/config/game_config.tres"
	if ResourceLoader.exists(config_path):
		var config := load(config_path)
		if config and config.has("api_base_url"):
			base_url = config.api_base_url
		if config and config.has("event_batch_interval"):
			event_batch_interval = config.event_batch_interval

func _init_event_system() -> void:
	event_flush_timer = Timer.new()
	event_flush_timer.wait_time = event_batch_interval
	event_flush_timer.autostart = true
	event_flush_timer.one_shot = false
	event_flush_timer.timeout.connect(_on_event_flush_timer_timeout)
	add_child(event_flush_timer)

func _generate_event_id() -> String:
	_event_id_counter += 1
	return "evt_%s_%s" % [str(Time.get_unix_time_from_system()), str(_event_id_counter)]

func _on_event_flush_timer_timeout() -> void:
	if event_queue.size() > 0:
		flush_events()

func submit_event(event_type: String, player_id: String, region_id: String = "", payload: Dictionary = {}, trace_id: String = "") -> void:
	if not EVENT_TYPES.has(event_type):
		print("Unknown event type: %s" % event_type)
		return

	if player_id == "":
		player_id = GameState.player_id

	var event: Dictionary = {
		"event_id": _generate_event_id(),
		"event_type": event_type,
		"player_id": player_id,
		"region_id": region_id,
		"timestamp": _get_current_timestamp(),
		"payload": payload,
		"trace_id": trace_id if trace_id != "" else self.trace_id,
		"schema_version": schema_version
	}

	if EVENT_TYPES[event_type]["realtime"]:
		_submit_event_realtime(event)
	else:
		event_queue.append(event)
		if event_queue.size() >= max_batch_size:
			flush_events()

func _get_current_timestamp() -> String:
	var now: DateTime = DateTime.now()
	return now.format("%Y-%m-%dT%H:%M:%SZ")

func _submit_event_realtime(event: Dictionary) -> void:
	var events: Array[Dictionary] = [event]
	_submit_events_batch(events)

func flush_events() -> void:
	if event_queue.size() == 0:
		return

	var events_to_send: Array[Dictionary] = event_queue.duplicate()
	event_queue.clear()
	_submit_events_batch(events_to_send)

func _submit_events_batch(events: Array[Dictionary]) -> void:
	var endpoint: String = "/events/batch"
	var body: Dictionary = {"events": events}
	
	var headers: Dictionary = {}
	if auth_token != "":
		headers["Authorization"] = "Bearer %s" % auth_token
	if trace_id != "":
		headers["X-Trace-Id"] = trace_id
	
	post_async(endpoint, body, headers, "", func(response: Dictionary) -> void:
		if response.get("success", false):
			event_batch_submitted.emit(events.size(), true)
		else:
			var err_code: String = response.get("code", "EVENT_SUBMIT_FAILED")
			var err_message: String = response.get("message", "Event batch submission failed")
			var err: Dictionary = {
				"success": false,
				"status_code": response.get("status_code", 0),
				"request_id": response.get("request_id", ""),
				"code": err_code,
				"message": err_message
			}
			event_submit_failed.emit(err)
	})