# game/ - Godot Client

Godot 4 + typed GDScript 客户端项目。

## 项目结构

遵循 [30-godot-client.md](../../.trae/rules/30-godot-client.md) 规范：

```
game/
├── project.godot          # Godot 项目文件
├── icon.svg               # 项目图标
├── scenes/                # 场景文件 (.tscn)
│   ├── Main.tscn          # 主入口场景
│   ├── player/            # 玩家相关场景
│   ├── npc/               # NPC 场景
│   ├── world/             # 世界/地图/区域场景
│   ├── ui/                # UI 界面场景
│   │   ├── main_menu/     # 主菜单
│   │   ├── voting/        # 投票相关UI
│   │   ├── quests/        # 任务相关UI
│   │   └── common/        # 通用UI组件
│   └── common/            # 通用场景组件
├── scripts/               # GDScript 脚本 (.gd)
│   ├── Main.gd            # 主入口脚本
│   ├── autoload/          # 自动加载单例（全局管理器）
│   │   ├── GameState.gd   # 游戏全局状态
│   │   ├── APIManager.gd  # 后端API请求管理
│   │   ├── VoteManager.gd # 投票状态管理
│   │   ├── ContentManager.gd # 内容包管理
│   │   └── AudioManager.gd # 音频管理
│   ├── player/            # 玩家逻辑
│   ├── npc/               # NPC 逻辑
│   ├── world/             # 世界逻辑
│   ├── ui/                # UI 逻辑
│   └── utils/             # 工具类
├── data/                  # 静态数据 (JSON/Resource)
│   ├── regions/           # 区域定义数据
│   ├── quests/            # 任务定义数据
│   ├── npcs/              # NPC 定义数据
│   └── config/            # 配置数据
├── assets/                # 美术、音频资源
│   ├── sprites/
│   ├── audio/
│   └── fonts/
└── tests/                 # GUT 测试脚本
```

## 核心 Autoload 单例

| 单例 | 职责 |
|------|------|
| `GameState` | 游戏全局状态（玩家信息、章节、区域解锁状态） |
| `APIManager` | 后端 API 请求（统一请求/响应格式、认证、追踪） |
| `VoteManager` | 投票相关状态（当前周期、候选项、投票历史） |
| `ContentManager` | 内容包更新管理（更新检查、已安装包列表） |
| `AudioManager` | 音频管理（音乐/音效音量、静音） |

## 与后端通信

所有 API 请求通过 `APIManager` 单例统一发送，遵循 [12-api-design.md](../../.trae/rules/12-api-design.md) 规范：

- 请求头携带 `Authorization`、`X-Trace-Id`、`X-Player-Id`
- 投票提交携带 `Idempotency-Key` 防止重复提交
- 响应数据按统一 envelope 结构解析（`request_id`、`data`、`meta`、`trace_id`）

## 测试框架

使用 GUT (Godot Unit Testing) 进行单元测试，测试文件位于 `tests/` 目录。

## 数据规范

- 所有数据文件必须带 `schema_version` 字段
- 优先使用 Godot Resource (.tres) 格式
- 简单配置使用 JSON 格式
