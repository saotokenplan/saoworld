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
| test_world_manager.gd | WorldManager 区域管理 | 39 |
| test_vote_manager.gd | VoteManager 投票系统管理（含落地信息、讨论区方法） | 32 |
| test_combat_manager.gd | CombatManager 战斗系统管理 | 13 |
| test_npc_dialog.gd | NPCDialog 对话交互组件 | 13 |
| test_api_manager.gd | APIManager API 请求管理 | 11 |
| test_game_state.gd | GameState 全局状态管理 | 11 |
| test_player_manager.gd | PlayerManager 玩家信息管理 | 15 |
| test_player.gd | Player 玩家移动与状态 | 15 |
| test_enemy.gd | Enemy 怪物实体 | 8 |
| test_content_package_detail.gd | ContentPackageDetail 内容包详情弹窗 | 9 |
| test_inventory_manager.gd | InventoryManager 背包系统管理 | 9 |
| test_save_manager.gd | SaveManager 存档系统管理 | 9 |
| test_quest_panel.gd | QuestPanel 任务面板组件 | 9 |
| test_world_map.gd | WorldMap 世界地图组件 | 7 |
| test_reputation_panel.gd | ReputationPanel 声望面板组件 | 6 |
| test_quest_tracker.gd | QuestTracker 任务追踪 HUD | 5 |
| test_region_scene.gd | CoreRegion 区域探索场景 | 5 |
| test_world_map_navigation.gd | WorldMap 区域导航与进入 | 5 |
| test_vote_discussion_panel.gd | VoteDiscussionPanel 投票讨论区面板 | 30 |

## 测试覆盖范围

### 核心单例测试
- **GameState**：章节管理、玩家信息、区域解锁、经验等级、投票参与记录、状态重置
- **APIManager**：基础 URL、认证 Token、请求 ID 生成、错误码映射、重试策略、HTTP 方法支持
- **VoteManager**：投票周期状态、候选项管理、投票统计、状态重置、投票落地信息判断（is_vote_landed、get_content_package_for_vote、get_landed_at、get_affected_regions）
- **WorldManager**：区域列表管理、区域详情、缓存机制
- **PlayerManager**：玩家信息、任务列表、区域状态

### UI 组件测试
- **WorldMap**：区域渲染、状态标识、点击选择、详情展示、区域导航
- **QuestPanel**：任务列表、详情展示、目标进度、奖励展示、任务接取
- **NPCDialog**：对话加载、多轮对话、选项选择、任务接取、信号发射
- **ContentPackageDetail**：状态文本映射、状态颜色映射、信号声明、package_data 清理
- **VoteDiscussionPanel**：初始状态、讨论列表渲染、回复列表渲染、排序切换、发布验证、信号发射
- **ReputationPanel**：声望列表、详情展示、信号声明

### 场景与角色测试
- **Player**：初始状态、重置状态、移动状态信号、输入方向、配置加载
- **CoreRegion**：场景结构、玩家实例化、进入信号、返回信号、区域数据设置
- **WorldMapNavigation**：进入区域信号、按钮显隐逻辑、区域选择进入流程

## 测试约定

1. 每个测试函数只测试一个场景
2. 使用 `assert_eq`、`assert_true`、`assert_false`、`assert_neq` 进行断言
3. 测试完成后使用 `reset()` 或 `reset_state()` 清理状态
4. 信号测试使用连接回调收集信号参数
5. 测试文件与被测试模块同名，前缀为 `test_`