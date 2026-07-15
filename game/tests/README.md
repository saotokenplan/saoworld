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
| test_vote_discussion_panel.gd | VoteDiscussionPanel 投票讨论区面板 | 30 |
| test_world_manager.gd | WorldManager 区域管理 | 39 |
| test_vote_manager.gd | VoteManager 投票系统管理（含落地信息、讨论区方法） | 32 |
| test_content_manager.gd | ContentManager 内容更新管理 | 22 |
| test_combat_manager.gd | CombatManager 战斗系统管理 | 13 |
| test_npc_dialog.gd | NPCDialog 对话交互组件 | 13 |
| test_vote_result_panel.gd | VoteResultPanel 投票结果展示 | 12 |
| test_vote_history_panel.gd | VoteHistoryPanel 投票历史面板 | 7 |
| test_audio_manager.gd | AudioManager 音频管理 | 17 |
| test_player_manager.gd | PlayerManager 玩家信息管理（含索引优化、声望预排序、并行请求） | 41 |
| test_player.gd | Player 玩家移动与状态 | 15 |
| test_api_manager.gd | APIManager API 请求管理 | 11 |
| test_game_state.gd | GameState 全局状态管理 | 11 |
| test_voting_panel.gd | VotingPanel 投票界面 | 5 |
| test_content_package_detail.gd | ContentPackageDetail 内容包详情弹窗 | 9 |
| test_inventory_manager.gd | InventoryManager 背包系统管理 | 9 |
| test_save_manager.gd | SaveManager 存档系统管理（含异步存档、缓存机制） | 24 |
| test_quest_panel.gd | QuestPanel 任务面板组件 | 9 |
| test_npc_panel.gd | NPCPanel NPC 列表 | 4 |
| test_combat_hud.gd | CombatHUD 战斗 HUD | 7 |
| test_world_map.gd | WorldMap 世界地图组件 | 7 |
| test_reputation_panel.gd | ReputationPanel 声望面板组件 | 6 |
| test_main_menu.gd | MainMenu 主菜单 | 2 |
| test_quest_tracker.gd | QuestTracker 任务追踪 HUD | 5 |
| test_region_scene.gd | CoreRegion 区域探索场景 | 5 |
| test_world_map_navigation.gd | WorldMap 区域导航与进入 | 5 |
| test_enemy.gd | Enemy 怪物实体 | 8 |
| test_personal_center.gd | PersonalCenter 个人中心 | 1 |
| test_feedback_manager.gd | FeedbackManager 用户反馈管理 | 18 |
| test_feedback_panel.gd | FeedbackPanel 反馈面板 | 22 |

## 测试覆盖范围

### 核心单例测试
- **GameState**：章节管理、玩家信息、区域解锁、经验等级、投票参与记录、状态重置
- **APIManager**：基础 URL、认证 Token、请求 ID 生成、错误码映射、重试策略、HTTP 方法支持
- **VoteManager**：投票周期状态、候选项管理、投票统计、状态重置、投票落地信息判断（is_vote_landed、get_content_package_for_vote、get_landed_at、get_affected_regions）
- **ContentManager**：内容更新管理、包安装/卸载、更新检测、状态查询、错误分类
- **AudioManager**：音量控制（音乐/音效）、静音切换、音量边界值、信号发射
- **WorldManager**：区域列表管理、区域详情、缓存机制
- **PlayerManager**：玩家信息、任务列表、区域状态、索引字典（O(1) 查询）、预排序声望级别、并行 API 请求追踪
- **CombatManager**：战斗状态机、伤害计算、胜负判定
- **InventoryManager**：背包数据管理、物品添加/移除/使用
- **SaveManager**：存档读写、自动保存、备份管理、异步存档（Thread）、存档信息缓存（TTL）、缓存失效机制
- **FeedbackManager**：反馈提交管理、类型/优先级验证、快捷方法（bug/suggestion/question）、待处理请求追踪、响应解析

### UI 组件测试
- **VotingPanel**：信号声明、候选项选择状态、投票状态、提交按钮逻辑
- **VoteResultPanel**：信号声明、百分比计算、获胜者判定、总票数计算
- **VoteHistoryPanel**：信号声明、分页状态、历史数据管理、落地展示
- **VoteDiscussionPanel**：初始状态、讨论列表渲染、回复列表渲染、排序切换、发布验证、信号发射
- **NPCPanel**：信号声明、NPC 列表加载、数据覆盖
- **NPCDialog**：对话加载、多轮对话、选项选择、任务接取、信号发射
- **MainMenu**：信号声明（12 个按钮信号）、存档状态设置
- **PersonalCenter**：closed 信号声明
- **CombatHUD**：attack_pressed/flee_pressed 信号、is_in_combat 状态、show_victory/show_defeat/hide_hud 方法
- **ContentPackageDetail**：状态文本映射、状态颜色映射、信号声明、package_data 清理
- **QuestPanel**：任务列表、详情展示、目标进度、奖励展示、任务接取
- **WorldMap**：区域渲染、状态标识、点击选择、详情展示、区域导航
- **ReputationPanel**：声望列表、详情展示、信号声明
- **FeedbackPanel**：反馈表单、输入验证、长度限制、加载状态、消息显示、表单清空

### 场景与角色测试
- **Player**：初始状态、重置状态、移动状态信号、输入方向、配置加载
- **CoreRegion**：场景结构、玩家实例化、进入信号、返回信号、区域数据设置
- **WorldMapNavigation**：进入区域信号、按钮显隐逻辑、区域选择进入流程
- **Enemy**：初始属性、伤害方法、死亡状态

## 测试约定

1. 每个测试函数只测试一个场景
2. 使用 `assert_eq`、`assert_true`、`assert_false`、`assert_neq` 进行断言
3. 测试完成后使用 `reset()` 或 `reset_state()` 清理状态
4. 信号测试使用连接回调收集信号参数
5. 测试文件与被测试模块同名，前缀为 `test_`
