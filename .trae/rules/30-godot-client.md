# 30 - Godot 客户端规范

> 适用角色：客户端开发
> 本文件定义 Godot 4 客户端的场景、脚本、数据规范。

## 引擎版本

- **引擎**：Godot 4.x
- **脚本语言**：typed GDScript（强制类型注解）

---

## 目录结构

```
game/
├── project.godot       # Godot 项目文件
├── scenes/             # 场景文件 (.tscn)
│   ├── player/         # 玩家相关场景
│   ├── npc/            # NPC 场景
│   ├── world/          # 世界/地图/区域场景
│   ├── ui/             # UI 界面场景
│   │   ├── voting/     # 投票相关UI
│   │   ├── quests/     # 任务相关UI
│   │   └── common/     # 通用UI组件
│   └── common/         # 通用场景组件
├── scripts/            # GDScript 脚本 (.gd)
│   ├── autoload/       # 自动加载单例（全局管理器）
│   ├── player/         # 玩家逻辑
│   ├── npc/            # NPC 逻辑
│   ├── world/          # 世界逻辑
│   ├── ui/             # UI 逻辑
│   └── utils/          # 工具类
├── data/               # 静态数据 (JSON/Resource)
│   ├── regions/        # 区域定义数据
│   ├── quests/         # 任务定义数据
│   ├── npcs/           # NPC 定义数据
│   └── config/         # 配置数据
├── assets/             # 美术、音频资源
│   ├── sprites/
│   ├── audio/
│   └── fonts/
└── tests/              # 测试脚本
```

---

## 场景规范

- 每个核心玩法实体应有独立场景
- **场景文件与主脚本文件同名**（如 `player.tscn` 对应 `player.gd`）
- 场景目录按领域划分（player/npc/world/ui）
- 复杂UI拆分为子场景，避免单一场景过大
- 场景中的节点命名要清晰表达用途，使用 PascalCase 或 snake_case

### 场景组织原则

- UI 场景与游戏世界场景分离
- 可复用组件放在 `scenes/common/`
- 投票界面单独放在 `scenes/ui/voting/`
- 每个区域一个主场景，区域内元素作为子场景或实例

---

## 脚本规范

### 强制使用类型注解

所有 GDScript 必须使用 typed GDScript，标注变量、函数参数、返回值类型：

```gdscript
# 正确示例
var player_name: String = ""
var health: int = 100

func take_damage(amount: int) -> void:
    health -= amount

func get_npc(npc_id: String) -> GDScript:
    return npc_database.get(npc_id)
```

### 脚本组织原则

- 单文件尽量只承载一个主要职责
- 全局管理器使用 Autoload（自动加载单例），放在 `scripts/autoload/`
- 复杂配置放入 `data/` 目录，**禁止硬编码**在场景脚本里
- 运行时依赖优先通过配置注入，不直接写死资源路径
- 使用信号（signals）进行节点间解耦通信，避免直接节点引用耦合

### Autoload 单例约定

建议的全局管理器：
- `GameState`：游戏全局状态（玩家信息、当前章节等）
- `APIManager`：后端 API 请求管理
- `VoteManager`：投票相关状态管理
- `ContentManager`：内容包更新管理
- `AudioManager`：音频管理

---

## 数据规范

- 客户端静态数据统一放在 `game/data/` 目录
- 生成内容与常量模板分目录存放
- **所有数据文件必须带 `schema_version` 字段**
- 从服务端获取的动态数据必须校验格式后再使用
- 敏感配置（API地址等）通过环境变量或项目配置注入，不硬编码

### 数据文件格式

- 优先使用 Godot Resource (.tres) 格式获得类型安全
- 简单配置可使用 JSON 格式
- 数据加载使用统一的 ResourceLoader 或自定义数据管理器

---

## 与后端通信规范

- 所有 API 请求通过 `APIManager` 单例统一发送
- 请求头必须携带：
  - `Authorization: Bearer <token>`（如已登录）
  - `X-Trace-Id`（可选，用于追踪）
  - `X-Player-Id`（玩家相关接口）
- 投票提交必须携带 `Idempotency-Key` 防止重复提交
- 网络错误必须有用户友好的提示和重试机制
- 响应数据按照 API 规范的 envelope 结构解析

---

## 投票相关UI要求

投票结算后客户端必须展示：
- 总票数与各候选项占比
- 最终采用方向
- 预计影响区域
- 预计上线周期
- 上一轮投票结果的实际落地情况

---

## 相关规则

- 仓库结构与命名 → [01-repository-structure.md](./01-repository-structure.md)
- API 设计规范 → [12-api-design.md](./12-api-design.md)
