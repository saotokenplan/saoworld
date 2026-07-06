# Build Agent 技术规范

> 文档状态：active
> 适用阶段：P2（多代理协同期）
> 维护要求：持续维护

## 职责定义

Build Agent 负责打包客户端、服务端、内容包，管理版本和发布。它确保所有通过门禁的代码都能正确构建和部署。

## 输入

| 输入来源 | 格式 | 说明 |
|---------|------|------|
| 代码分支 | Git | 通过门禁的分支 |
| 内容包 | JSON | 已审核通过的内容 |
| 版本配置 | yaml | 版本号和元数据 |
| 构建配置 | yaml | 构建参数和选项 |

### 输入数据结构

**构建任务输入**：
```json
{
  "build_task_id": "BUILD-001",
  "task_id": "TASK-001",
  "title": "构建迷雾森林版本",
  "type": "full",
  "branch": "feature/fog_forest",
  "version": "0.2.0",
  "components": ["client", "server", "content"],
  "content_packages": ["pkg_fog_forest_20260707_01"],
  "gray_scope": {
    "region_ids": ["region_fog_forest"],
    "player_percent": 10,
    "player_ids": []
  },
  "target_environment": "staging"
}
```

**版本配置输入**：
```json
{
  "version": "0.2.0",
  "build_number": 123,
  "git_commit": "abc123",
  "timestamp": "2026-07-07T20:00:00Z",
  "changelog": [
    {"type": "feature", "description": "新增迷雾森林区域"},
    {"type": "bugfix", "description": "修复投票提交响应慢问题"}
  ],
  "dependencies": {
    "python": ">=3.11",
    "godot": "4.2",
    "fastapi": ">=0.111"
  }
}
```

**构建配置输入**：
```json
{
  "client": {
    "platforms": ["windows", "linux", "mac"],
    "build_type": "release",
    "export_presets": "presets.cfg",
    "output_dir": "build/client"
  },
  "server": {
    "services": ["vote", "world", "content", "generation", "review", "player", "ops", "gateway"],
    "docker_registry": "registry.example.com",
    "build_args": {},
    "output_dir": "build/server"
  },
  "content": {
    "packages": ["pkg_fog_forest_20260707_01"],
    "output_dir": "build/content"
  }
}
```

## 输出

| 输出产物 | 格式 | 说明 |
|---------|------|------|
| 客户端构建 | .exe/.apk/.zip | 游戏客户端 |
| 服务端镜像 | Docker | Docker 镜像 |
| 内容包 | zip | 打包的内容包 |
| 回滚包 | zip | 可回滚的版本包 |
| 版本元数据 | JSON | 版本信息和构建记录 |
| 构建报告 | JSON/markdown | 构建结果报告 |

### 输出数据结构

**构建输出元数据**：
```json
{
  "build_id": "BUILD-001",
  "version": "0.2.0",
  "build_number": 123,
  "timestamp": "2026-07-07T20:00:00Z",
  "status": "success",
  "components": {
    "client": {
      "status": "success",
      "files": ["build/client/game-windows.exe", "build/client/game-linux.zip"],
      "size": "150MB"
    },
    "server": {
      "status": "success",
      "images": [
        {"name": "vote-service", "tag": "0.2.0"},
        {"name": "world-service", "tag": "0.2.0"}
      ],
      "registry": "registry.example.com"
    },
    "content": {
      "status": "success",
      "packages": ["build/content/pkg_fog_forest_20260707_01.zip"],
      "size": "5MB"
    }
  },
  "rollback_package": "build/rollback/0.2.0-rollback.zip",
  "git_commit": "abc123",
  "built_by": "build-agent"
}
```

**构建报告输出**：
```json
{
  "report_id": "BUILD-REPORT-001",
  "build_id": "BUILD-001",
  "timestamp": "2026-07-07T20:30:00Z",
  "results": {
    "client_build": {"status": "success", "duration": "15m", "errors": []},
    "server_build": {"status": "success", "duration": "10m", "errors": []},
    "content_packaging": {"status": "success", "duration": "2m", "errors": []},
    "rollback_generation": {"status": "success", "duration": "1m", "errors": []}
  },
  "summary": {
    "overall_status": "success",
    "total_components": 4,
    "success_components": 4,
    "failed_components": 0,
    "total_duration": "28m"
  }
}
```

**版本元数据输出**：
```json
{
  "version_id": "VER-001",
  "version": "0.2.0",
  "build_id": "BUILD-001",
  "release_date": "2026-07-07T20:00:00Z",
  "status": "gray",
  "changelog": [...],
  "components": [...],
  "rollback_package": "build/rollback/0.2.0-rollback.zip",
  "created_at": "2026-07-07T20:00:00Z"
}
```

## 核心流程

### 步骤 1：检查代码分支
- 验证分支是否存在且通过门禁
- 检查代码状态是否干净
- 获取 Git 提交信息

### 步骤 2：构建客户端
- 使用 Godot 导出客户端
- 针对不同平台构建（Windows/Linux/Mac）
- 生成压缩包
- 验证构建产物完整性

### 步骤 3：构建服务端镜像
- 为每个服务构建 Docker 镜像
- 推送镜像到 Docker registry
- 验证镜像可运行

### 步骤 4：打包内容包
- 将审核通过的内容打包
- 添加版本元数据和 schema_version
- 生成内容包签名
- 验证内容包完整性

### 步骤 5：生成回滚包
- 包含当前版本的所有构建产物
- 添加回滚脚本
- 添加版本信息
- 验证回滚包可解压和使用

### 步骤 6：写入版本元数据
- 创建版本记录
- 写入 changelog
- 记录构建参数
- 记录构建时间和时长

### 步骤 7：生成构建报告
- 汇总构建结果
- 记录每个组件的状态
- 记录错误信息
- 通知 Orchestrator 构建结果

### 步骤 8：发布到灰度环境
- 如果是灰度发布，部署到灰度环境
- 配置灰度范围
- 启动服务并验证

## 关键能力

- Godot 客户端构建
- Docker 镜像构建
- 内容包打包
- 版本管理
- 回滚包生成

## 协作机制

### 与 QA Agent
- **输入**：测试结果、门禁状态
- **输出**：构建结果、版本信息
- **触发条件**：测试通过后

### 与 Ops Agent
- **输入**：部署配置、目标环境
- **输出**：构建产物、部署请求
- **触发条件**：构建完成后

### 与 World Agent
- **输入**：审核通过的内容包
- **输出**：打包结果、内容包路径
- **触发条件**：内容审核通过后

### 与 Orchestrator
- **输入**：构建任务分配
- **输出**：构建报告、版本信息
- **触发条件**：构建执行完成后

## 错误处理和异常情况

### 构建失败
- **检测**：客户端或服务端构建失败
- **处理**：分析错误日志，修复问题后重新构建
- **通知**：记录构建失败日志，包含错误原因

### 镜像推送失败
- **检测**：Docker 镜像推送到 registry 失败
- **处理**：检查网络和权限，重新推送
- **通知**：记录镜像推送失败日志

### 内容包缺失
- **检测**：需要打包的内容包不存在
- **处理**：等待内容包生成或使用空内容包
- **通知**：记录内容包缺失日志

### 回滚包生成失败
- **检测**：回滚包生成失败
- **处理**：重新生成，确保包含所有必要文件
- **通知**：记录回滚包生成失败日志

### 资源不足
- **检测**：构建过程中内存或磁盘不足
- **处理**：清理临时文件，增加资源分配
- **通知**：记录资源不足日志

## 约束条件

- 必须遵循 42-release-rollback.md 规范
- 必须支持灰度发布
- 必须生成回滚包
- 版本号必须符合语义化规范
- 必须验证构建产物完整性
- 必须记录构建过程和结果
- 必须支持多平台构建

## 验收标准

- 客户端构建成功
- 服务端镜像构建成功
- 内容包打包成功
- 回滚包可用
- 版本元数据完整
- 构建报告清晰完整
- 构建产物通过验证
- 输出格式符合规范，可被其他代理直接使用