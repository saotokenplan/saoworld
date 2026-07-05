# 测试目录

本目录用于存放 Godot 客户端的 GUT (Godot Unit Testing) 测试脚本。

## 测试框架

使用 GUT (Godot Unit Testing) 框架进行单元测试。

### 安装 GUT

在 Godot 编辑器中：
1. 打开 AssetLib
2. 搜索 "GUT" (Godot Unit Test)
3. 安装 Gut 插件
4. 在 Project > Project Settings > Plugins 中启用 GUT

## 测试文件命名

- 测试文件：`test_<模块名>.gd`（如 `test_game_state.gd`）
- 测试函数：`test_<功能>_<场景>`（如 `test_set_player_info_success`）

## 运行测试

1. 在 Godot 编辑器中打开 GUT 面板
2. 选择测试目录
3. 点击 "Run All" 运行所有测试

## 已编写测试

| 测试文件 | 覆盖模块 | 测试数量 |
|---------|---------|---------|
| test_game_state.gd | GameState 全局状态管理 | 10 |
| test_api_manager.gd | APIManager API 请求管理 | 10 |
| test_vote_manager.gd | VoteManager 投票系统管理 | 7 |
| test_world_manager.gd | WorldManager 区域管理 | 7 |
| test_player_manager.gd | PlayerManager 玩家信息管理 | 6 |
| test_world_map.gd | WorldMap 世界地图组件 | 6 |
| test_quest_panel.gd | QuestPanel 任务面板组件 | 6 |
| test_npc_dialog.gd | NPCDialog 对话交互组件 | 5 |

## 测试覆盖范围

### 核心单例测试
- **GameState**：章节管理、玩家信息、区域解锁、经验等级、投票参与记录、状态重置
- **APIManager**：基础 URL、认证 Token、请求 ID 生成、错误码映射、重试策略、HTTP 方法支持
- **VoteManager**：投票周期状态、候选项管理、投票统计、状态重置
- **WorldManager**：区域列表管理、区域详情、缓存机制
- **PlayerManager**：玩家信息、任务列表、区域状态

### UI 组件测试
- **WorldMap**：区域渲染、状态标识、点击选择、详情展示
- **QuestPanel**：任务列表、详情展示、目标进度、奖励展示、任务接取
- **NPCDialog**：对话加载、多轮对话、选项选择、任务接取、信号发射

## 测试约定

1. 每个测试函数只测试一个场景
2. 使用 `assert_eq`、`assert_true`、`assert_false`、`assert_neq` 进行断言
3. 测试完成后使用 `reset()` 或 `reset_state()` 清理状态
4. 信号测试使用连接回调收集信号参数
5. 测试文件与被测试模块同名，前缀为 `test_`