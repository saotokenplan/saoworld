# 客户端性能优化分析报告

> 生成时间：2026-07-15 04:00
> 任务标识：auto-20260715-0400
> 分析范围：game/scripts/ 目录下核心脚本

---

## 一、场景结构分析

### 场景加载机制

当前场景切换流程（[Main.gd](file:///workspace/game/scripts/Main.gd)）：

1. **问题**：`_find_region_data()` 每次调用都会打开文件并解析 JSON，没有缓存机制
   - 位置：第 101-118 行
   - 影响：频繁切换区域时重复 IO 操作

2. **问题**：场景切换时直接 `queue_free()`，没有渐进式卸载
   - 位置：第 44 行
   - 影响：大场景切换可能导致帧率波动

### 优化建议

| 优先级 | 优化项 | 实施步骤 |
|--------|--------|----------|
| P0 | 区域数据缓存 | 在 WorldManager 中预加载区域列表，避免重复文件读取 |
| P1 | 场景异步加载 | 使用 `ResourceLoader.load_threaded_request()` 异步加载场景 |
| P2 | 场景渐进式卸载 | 在 _process 中分批释放场景资源 |

---

## 二、脚本性能分析

### 2.1 VoteManager.gd

**问题清单**：

| 问题 | 位置 | 严重程度 | 说明 |
|------|------|----------|------|
| 频繁进度轮询 | 第 482-504 行 | 高 | `_poll_vote_progress()` 每 10 秒发起一次 API 请求 |
| 线性搜索 | 第 149-153、173-181 行 | 中 | `get_candidate_by_id()`、`get_candidate_percentage()` 使用 O(n) 搜索 |
| 无轮询节流 | 第 489-501 行 | 中 | 投票进度轮询没有根据网络状态动态调整间隔 |

**优化建议**：

```gdscript
# 优化：添加时间衰减轮询策略
var progress_poll_interval: int = 10
var progress_poll_max_interval: int = 60
var poll_interval_multiplier: float = 1.2

func _poll_vote_progress() -> void:
    fetch_vote_progress()
    if current_progress.get("is_near_end", false):
        progress_poll_interval = max(5, progress_poll_interval / poll_interval_multiplier)
    else:
        progress_poll_interval = min(progress_poll_max_interval, 
                                     progress_poll_interval * poll_interval_multiplier)
    if progress_poll_timer:
        progress_poll_timer.wait_time = progress_poll_interval
```

---

### 2.2 WorldManager.gd

**问题清单**：

| 问题 | 位置 | 严重程度 | 说明 |
|------|------|----------|------|
| 声望检查重复调用 | 第 361-378、464-481 行 | 中 | `is_npc_accessible()`、`is_quest_accessible()` 每次都重新获取声望 |
| 自定义排序开销 | 第 252-269 行 | 低 | `sort_regions()` 使用自定义排序函数，大数据量时较慢 |
| 无缓存失效机制 | 第 137-138 行 | 中 | `clear_cache()` 只能手动调用，没有自动过期机制 |

**优化建议**：

```gdscript
# 优化：添加缓存过期机制
var cache_ttl: float = 300.0
var region_cache_timestamps: Dictionary = {}

func fetch_region_detail(region_id: String) -> Dictionary:
    if region_cache.has(region_id):
        var timestamp: float = region_cache_timestamps.get(region_id, 0)
        if Time.get_ticks_msec() - timestamp < cache_ttl * 1000:
            return region_cache[region_id]
        region_cache.erase(region_id)
    
    _set_loading(true)
    var result: Dictionary = APIManager.get("/world/regions/%s" % region_id)
    
    if result.get("success", false):
        var data: Dictionary = result.get("data", {})
        region_cache[region_id] = data
        region_cache_timestamps[region_id] = Time.get_ticks_msec()
        ...
```

---

### 2.3 APIManager.gd

**问题清单**：

| 问题 | 位置 | 严重程度 | 说明 |
|------|------|----------|------|
| 同步阻塞请求 | 第 178-181 行 | 高 | `_make_request()` 使用 while 循环阻塞等待响应 |
| 请求节点重复创建 | 第 119-120 行 | 中 | 每次请求都创建新的 HTTPRequest 节点 |
| 代码重复 | 第 114-201、356-399 行 | 低 | `_make_request()` 和 `_make_request_async()` 大量重复代码 |
| 重试策略简单 | 第 185-199 行 | 中 | 固定指数退避，没有抖动 |

**优化建议**：

```gdscript
# 优化：使用连接池和异步回调
var request_pool: Array[HTTPRequest] = []
var max_pool_size: int = 5

func _get_request_from_pool() -> HTTPRequest:
    for req in request_pool:
        if not req.is_processing():
            return req
    if request_pool.size() < max_pool_size:
        var new_req := HTTPRequest.new()
        add_child(new_req)
        request_pool.append(new_req)
        return new_req
    return HTTPRequest.new()
```

---

### 2.4 PlayerManager.gd

**问题清单**：

| 问题 | 位置 | 严重程度 | 说明 |
|------|------|----------|------|
| 声望等级计算复杂 | 第 277-292、299-337 行 | 中 | `calculate_reputation_level()` 和 `get_reputation_progress()` 有重复排序逻辑 |
| 线性搜索 | 第 139-143、177-181 行 | 低 | `get_player_quest_by_id()`、`get_player_region_by_id()` 使用 O(n) 搜索 |
| 全量刷新开销 | 第 206-210 行 | 中 | `refresh_all()` 一次性发起 4 个 API 请求 |

**优化建议**：

```gdscript
# 优化：预计算声望等级映射
const REPUTATION_LEVEL_THRESHOLDS: Array[Dictionary] = [
    {"key": "exalted", "threshold": 42000},
    {"key": "revered", "threshold": 21000},
    {"key": "honored", "threshold": 9000},
    {"key": "friendly", "threshold": 3000},
    {"key": "neutral", "threshold": 0},
    {"key": "hostile", "threshold": -3000}
]

func calculate_reputation_level(reputation: int) -> String:
    for level in REPUTATION_LEVEL_THRESHOLDS:
        if reputation >= level["threshold"]:
            return level["key"]
    return "hostile"
```

---

### 2.5 SaveManager.gd

**问题清单**：

| 问题 | 位置 | 严重程度 | 说明 |
|------|------|----------|------|
| 玩家位置查找 | 第 129 行 | 中 | 使用 `get_nodes_in_group()` 查找玩家，场景复杂时较慢 |
| 全量存档写入 | 第 72-74 行 | 中 | 每次存档都完整序列化，没有增量保存 |
| 备份策略简单 | 第 96-98 行 | 低 | 只有单份备份，没有历史版本管理 |

**优化建议**：

```gdscript
# 优化：使用信号获取玩家位置，避免遍历场景树
var player_position: Vector2 = Vector2.ZERO

func _ready() -> void:
    get_tree().connect("player_position_updated", _on_player_position_updated)

func _on_player_position_updated(pos: Vector2, region_id: String) -> void:
    player_position = pos
    current_region_id = region_id
```

---

## 三、资源加载策略分析

### 当前状态

- 场景使用 `preload()` 在脚本加载时预加载（[Main.gd](file:///workspace/game/scripts/Main.gd) 第 3-11 行）
- 数据文件使用 `FileAccess.open()` 动态读取
- 没有资源缓存管理机制

### 问题识别

| 问题 | 影响 |
|------|------|
| 所有场景在启动时预加载 | 增加启动时间，占用初始内存 |
| 数据文件重复读取 | 频繁访问同一数据时重复 IO |
| 没有资源卸载机制 | 长时间游玩后内存占用持续增长 |

### 优化建议

| 优先级 | 优化项 | 说明 |
|--------|--------|------|
| P0 | 按需加载场景 | 将 `preload()` 改为 `load()` 或异步加载 |
| P1 | 数据缓存层 | 创建 DataManager 统一管理数据加载和缓存 |
| P2 | 资源生命周期管理 | 实现资源引用计数和自动卸载 |

---

## 四、优化优先级排序

### P0 - 阻塞性问题（必须立即修复）

1. **APIManager 同步阻塞请求**：改为异步回调模式
2. **区域数据重复读取**：添加缓存机制
3. **频繁进度轮询**：实现动态间隔调整

### P1 - 重要优化（建议尽快实施）

4. **HTTP 请求连接池**：复用 HTTPRequest 节点
5. **声望计算优化**：预计算等级映射
6. **场景异步加载**：使用线程加载大场景

### P2 - 常规优化（可后续迭代）

7. **缓存过期机制**：自动清理过期缓存
8. **玩家位置获取优化**：使用信号替代场景树遍历
9. **资源生命周期管理**：实现引用计数

---

## 五、性能目标与验收标准

### 优化目标

| 指标 | 目标值 | 现状 |
|------|--------|------|
| 场景加载时间 | < 200ms | 未测量 |
| API 请求响应时间 | < 500ms（P95） | 未测量 |
| 内存增长 | < 50MB/h | 未测量 |
| 帧率稳定性 | 60FPS ± 5% | 未测量 |

### 验收标准

1. ✅ APIManager 请求改为异步非阻塞模式
2. ✅ WorldManager 区域数据缓存机制实现
3. ✅ VoteManager 动态轮询间隔实现
4. ✅ 场景加载使用异步方式
5. ✅ 核心 API 接口测试覆盖
6. ✅ 性能基准测试脚本创建

---

## 六、实施计划

### 第一阶段：API 层优化（1-2天）

- APIManager 异步化改造
- 添加请求连接池
- 实现智能重试策略

### 第二阶段：数据层优化（1-2天）

- WorldManager 缓存机制
- PlayerManager 声望计算优化
- 全局数据缓存层

### 第三阶段：场景层优化（1天）

- 场景异步加载
- 场景切换优化
- 资源生命周期管理

### 第四阶段：测试验证（1天）

- 性能基准测试
- 回归测试
- 监控指标接入
