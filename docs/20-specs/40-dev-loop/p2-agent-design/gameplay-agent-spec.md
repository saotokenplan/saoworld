# Gameplay Agent 技术规范

> 文档状态：active
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

Gameplay Agent 负责编写 Godot 场景、角色控制、交互和任务逻辑。它将 System Designer Agent 的设计方案转化为可运行的客户端代码。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| design-note.md | markdown | 技术设计文档（客户端部分） |
| 现有场景 | .tscn | 当前场景文件 |
| 现有脚本 | .gd | 当前 GDScript 文件 |
| 数据配置 | json/yaml | 区域、任务、NPC 数据 |

### 输入数据结构

**设计任务输入**：
```json
{
  "design_id": "DESIGN-001",
  "task_id": "TASK-001",
  "title": "新增迷雾森林场景",
  "type": "scene",
  "target_module": "game",
  "requirements": [
    "创建场景文件 scenes/world/fog_forest.tscn",
    "创建脚本文件 scripts/world/fog_forest.gd",
    "包含区域渲染和状态标识",
    "支持点击选择和详情展示"
  ],
  "data_config": "game/data/regions/fog_forest.json"
}
```

**场景配置输入**：
```json
{
  "scene_name": "fog_forest",
  "nodes": [
    {
      "name": "FogForest",
      "type": "Node2D",
      "children": [
        {
          "name": "Background",
          "type": "Sprite2D",
          "properties": {"texture": "res://assets/tiles/fog_forest.png"}
        },
        {
          "name": "PlayerSpawn",
          "type": "Marker2D",
          "properties": {"position": [100, 100]}
        }
      ]
    }
  ],
  "signals": [
    {"name": "region_selected", "parameters": [{"name": "region_id", "type": "String"}]}
  ]
}
```

**脚本接口输入**：
```json
{
  "script_name": "fog_forest",
  "extends": "Node2D",
  "properties": [
    {"name": "region_id", "type": "String", "default": "\"region_fog_forest\""},
    {"name": "is_unlocked", "type": "bool", "default": false}
  ],
  "methods": [
    {
      "name": "_ready",
      "return_type": "void",
      "parameters": []
    },
    {
      "name": "on_region_click",
      "return_type": "void",
      "parameters": [{"name": "event", "type": "InputEventMouseButton"}]
    },
    {
      "name": "update_region_status",
      "return_type": "void",
      "parameters": [{"name": "status", "type": "String"}]
    }
  ]
}
```

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| 场景文件 | .tscn | Godot 场景 |
| 脚本文件 | .gd | typed GDScript |
| 测试文件 | .gd | GUT 测试用例 |
| 资源文件 | .png/.wav | 游戏资源（可选） |

### 输出数据结构

**场景输出元数据**：
```json
{
  "scene_id": "SCENE-001",
  "design_id": "DESIGN-001",
  "task_id": "TASK-001",
  "file_path": "scenes/world/fog_forest.tscn",
  "script_path": "scripts/world/fog_forest.gd",
  "version": "1.0",
  "status": "completed",
  "created_at": "2026-07-07T12:00:00Z"
}
```

**测试用例输出**：
```json
{
  "test_file": "tests/test_fog_forest.gd",
  "tests": [
    {
      "name": "test_scene_loading",
      "description": "验证场景能正常加载",
      "expected_result": "场景加载成功，无错误"
    },
    {
      "name": "test_region_status_display",
      "description": "验证区域状态正确显示",
      "expected_result": "锁定状态显示锁图标，解锁状态显示正常"
    },
    {
      "name": "test_region_click_signal",
      "description": "验证点击区域触发信号",
      "expected_result": "region_selected 信号正确触发"
    }
  ]
}
```

## 核心流程

### 步骤 1：分析设计文档
- 读取 design-note.md 中客户端相关部分
- 理解场景结构和节点需求
- 识别脚本接口和信号定义

### 步骤 2：检查现有代码
- 分析现有场景和脚本结构
- 识别可复用的组件和模式
- 评估改动对现有系统的影响

### 步骤 3：创建场景文件
- 根据设计创建 .tscn 文件
- 添加必要的节点和层级
- 设置节点属性和信号连接
- 确保场景文件与脚本文件同名

### 步骤 4：编写脚本逻辑
- 根据设计编写 typed GDScript
- 实现方法和属性定义
- 添加信号定义和处理
- 实现交互逻辑（点击、拖动等）
- 实现状态管理

### 步骤 5：集成数据配置
- 从 data/ 目录加载配置数据
- 将配置数据映射到场景和脚本
- 实现动态内容加载
- 添加 schema_version 校验

### 步骤 6：编写测试用例
- 创建 GUT 测试文件
- 编写场景加载测试
- 编写节点引用测试
- 编写信号连接测试
- 编写核心逻辑测试

### 步骤 7：运行测试验证
- 执行 GUT 测试
- 分析失败原因
- 修复问题
- 重新运行测试直到全部通过

### 步骤 8：交付成果
- 将场景、脚本、测试文件提交到版本控制
- 通知 QA Agent 进行回归测试

## 关键能力

- Godot 场景设计和实现
- GDScript 编程（typed）
- 角色控制和交互逻辑
- 任务系统实现
- 场景节点管理和信号通信

## 协作机制

### 与 System Designer Agent
- **输入**：design-note.md（客户端部分）、数据结构定义
- **输出**：实现反馈、技术问题、变更请求
- **触发条件**：客户端设计完成后

### 与 World Agent
- **输入**：区域配置、NPC 配置、任务配置
- **输出**：内容反馈、配置问题
- **触发条件**：内容配置更新后

### 与 QA Agent
- **输出**：测试用例、代码变更
- **输入**：测试结果、失败摘要
- **触发条件**：测试执行完成后

### 与 Build Agent
- **输出**：场景文件、脚本文件、资源文件
- **输入**：构建结果、资源缺失报告
- **触发条件**：构建执行前

## 错误处理和异常情况

### 设计不完整
- **检测**：设计文档缺少关键信息
- **处理**：向 System Designer Agent 请求补充
- **通知**：记录设计缺失日志

### 节点引用失效
- **检测**：场景中引用的节点不存在
- **处理**：修复节点引用或创建缺失节点
- **通知**：记录节点引用错误日志

### 脚本语法错误
- **检测**：GDScript 编译失败
- **处理**：修复语法错误
- **通知**：记录编译错误日志

### 数据配置缺失
- **检测**：脚本无法找到配置文件
- **处理**：创建默认配置或等待配置完成
- **通知**：记录配置缺失日志

### 测试失败
- **检测**：GUT 测试未通过
- **处理**：分析失败原因，修复代码
- **通知**：记录测试失败日志

## 约束条件

- 必须使用 typed GDScript
- 场景文件与脚本文件同名
- 必须遵循 30-godot-client.md 规范
- 必须编写测试用例
- 场景节点命名清晰，使用 PascalCase 或 snake_case
- 必须使用信号进行节点间通信，避免直接引用
- 配置数据必须带 schema_version 字段

## 验收标准

- 场景文件结构合理，节点命名清晰
- 脚本代码符合 typed GDScript 规范
- 测试用例覆盖核心逻辑
- GUT 测试全部通过
- 场景加载正常，无错误日志
- 信号连接正确，交互响应正常
- 配置数据正确加载和显示
- 输出格式符合规范，可被其他代理直接使用