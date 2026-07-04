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

| 测试文件 | 覆盖模块 |
|---------|---------|
| test_game_state.gd | GameState 全局状态管理 |
| test_api_manager.gd | APIManager API 请求管理 |
