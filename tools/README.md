# tools/ - 工具脚本与离线工具

离线脚本、校验器、Git hooks 安装器、打包工具、一次性数据迁移脚本，以及 AI 研发闭环工具模块。

## 目录结构

```
tools/
├── agents/             # P2 多代理协同工具
│   ├── product_agent/      # Product Agent（需求分析与优先级排序）
│   ├── system_designer_agent/ # System Designer Agent（系统设计）
│   ├── gameplay_agent/     # Gameplay Agent（客户端代码实现）
│   ├── world_agent/        # World Agent（世界内容生成）
│   ├── backend_agent/      # Backend Agent（后端代码实现）
│   ├── qa_agent/           # QA Agent（测试与质量保证）
│   ├── build_agent/        # Build Agent（构建与发布）
│   ├── ops_agent/          # Ops Agent（运维监控分析）
│   ├── orchestrator/       # Orchestrator（统一调度器）
│   ├── pyproject.toml      # 项目配置
│   └── __init__.py
├── content_check/      # 内容审核四项检查
│   ├── world_consistency.py  # 世界一致性检查器
│   ├── reward_boundary.py    # 数值边界检查器
│   ├── content_safety.py     # 内容安全检查器
│   ├── duplication.py        # 重复度检查器
│   ├── base.py               # 检查器基类
│   ├── config.py             # 配置管理
│   ├── tests/                # 测试用例（28 个）
│   └── pyproject.toml        # 项目配置
├── loop_logging/       # Loop 基础设施工具
│   ├── agent_session_logger.py  # Agent 会话日志采集
│   ├── ci_failure_logger.py     # CI 失败日志采集
│   ├── prod_incident_logger.py  # 生产事件日志采集
│   ├── signature_extractor.py   # 失败签名提取
│   ├── clusterer.py             # 失败聚类
│   ├── gap_classifier.py        # 缺口分类（缺gate/覆盖不足/信噪比低）
│   ├── rule_registry.py         # 规则版本化管理
│   ├── threshold_manager.py     # 阈值管理
│   ├── golden_case_manager.py   # 黄金案例管理
│   ├── rule_evaluator.py        # 规则评估
│   ├── feedback_collector.py    # 反馈信号采集
│   ├── rule_improvement_generator.py # 规则改进建议生成
│   ├── issue_generator.py       # Issue 自动生成
│   ├── cli.py                   # CLI 命令行工具
│   ├── schema.py                # 数据结构定义
│   ├── tests/                   # 测试用例（36 个）
│   └── pyproject.toml           # 项目配置
├── playtest/           # 端到端集成测试框架
│   ├── conftest.py         # 测试夹具
│   ├── test_vote_flow.py   # 投票流程集成测试
│   ├── test_vote_integration.py # 投票服务集成测试
│   ├── test_content_integration.py # 内容服务集成测试
│   ├── test_event_bus.py   # 事件总线集成测试
│   ├── run_vote_flow.sh    # 投票流程运行脚本
│   └── pyproject.toml      # 项目配置
├── deploy.sh           # 部署脚本
├── rollback.sh         # 回滚脚本
├── health-check.sh     # 健康检查脚本
├── migrate-all.sh      # 全量数据库迁移脚本
├── gray-release.sh     # 灰度发布脚本
├── verify-release.sh   # 发布验证脚本
├── validate-commit-msg.py  # Git 提交信息校验
├── generate-commit-msg.py  # Git 提交信息生成建议
├── install-git-hooks.sh    # Git Hooks 安装脚本
└── README.md           # 本文件
```

## 核心模块

### 1. Agents - P2 多代理协同

9 个专业代理角色 + 统一调度器，实现 AI-first 全流程研发闭环。

**代理角色**：

| 代理 | 职责 | 测试 |
|------|------|------|
| Product Agent | 读取目标、玩家反馈和路线图，输出版本需求和优先级 | 23 个 |
| System Designer Agent | 设计玩法系统、模块边界、数据结构和接口约束 | 18 个 |
| Gameplay Agent | 编写 Godot 场景、角色控制、交互和任务逻辑 | 16 个 |
| World Agent | 生成 NPC、区域、事件、任务和世界描述配置 | 25 个 |
| Backend Agent | 编写后端服务（模型、Repository、API、测试） | 24 个 |
| QA Agent | 编写和执行自动化测试、试玩脚本、回归检查 | 16 个 |
| Build Agent | 打包客户端、服务端、内容包，管理版本和发布 | 17 个 |
| Ops Agent | 读取监控和线上数据，归纳问题并形成改进建议 | 20 个 |
| Orchestrator | 统一调度所有代理，负责任务分配、依赖编排、门禁检查 | 54 个 |

**核心能力**：
- `AgentDispatcher`：动态导入并调用各 Agent 核心方法
- `WorkflowExecutor`：基于 Kahn 算法的拓扑排序，按依赖关系顺序执行
- 支持 `use_real_dispatch` 参数在模拟/真实两种模式间切换

```bash
# 进入 agents 目录
cd tools/agents

# 运行 Orchestrator CLI
python -m orchestrator.cli --help

# 运行测试
pip install -e .
python -m pytest -q
```

### 2. Content Check - 内容审核四项检查

AI 生成内容的自动化质量门禁，确保生成内容符合世界观、数值、安全和原创性要求。

**四项检查**：

| 检查器 | 说明 |
|--------|------|
| 世界一致性 | 阵营关系不冲突、NPC 身份不越界、聚落资源与地貌匹配 |
| 数值边界 | 奖励不超章节上限、敌人强度在允许区间、无刷取漏洞 |
| 内容安全 | 敏感词检测、高风险主题识别、年龄层适配 |
| 重复度 | NPC 设定相似度、支线骨架复用、文案段落重复率 |

```bash
# 进入 content_check 目录
cd tools/content_check

# 运行测试
pip install -e .
python -m pytest -q  # 28 个测试全部通过
```

### 3. Loop Logging - Loop 基础设施

三层 Loop 工程基础设施，用于日志采集、失败分析、规则评估和持续改进。

**核心能力**：
- 结构化日志采集（Agent 会话、CI 失败、生产事件）
- 失败签名提取与聚类分析
- 缺口分类（缺门禁 / 覆盖不足 / 信噪比低）
- 规则版本化管理与阈值管理
- 黄金案例管理
- 规则评估与改进建议生成
- Gate Improvement Issue 自动生成

```bash
# 进入 loop_logging 目录
cd tools/loop_logging

# CLI 工具
python -m cli --help

# 规则改进分析
python -m cli rule-improvement --log-dir ./logs

# 运行测试
pip install -e .
python -m pytest -q  # 36 个测试全部通过
```

### 4. Playtest - 端到端集成测试

跨服务端到端集成测试框架，验证核心玩法链路的完整性。

**测试覆盖**：
- 投票服务健康检查与 envelope 格式
- 内容服务健康检查与 envelope 格式
- 事件总线发布与订阅机制
- 投票完整流程（创建周期、状态迁移、投票提交、关闭计票、历史查询）
- 内容包完整流程（创建、灰度发布、全量发布、回滚、详情查询）

```bash
# 进入 playtest 目录
cd tools/playtest

# 运行测试
pip install -e .
python -m pytest -q  # 15 个端到端测试通过
```

## 运维脚本

| 脚本 | 说明 |
|------|------|
| `deploy.sh` | 服务部署脚本 |
| `rollback.sh` | 服务回滚脚本（支持回滚日志记录） |
| `health-check.sh` | 健康检查脚本（支持服务级别检查） |
| `migrate-all.sh` | 全量数据库迁移脚本（所有 8 个服务） |
| `gray-release.sh` | 灰度发布脚本 |
| `verify-release.sh` | 发布验证脚本（内容包状态、灰度范围、系统状态） |

## Git 工具

| 脚本 | 说明 |
|------|------|
| `validate-commit-msg.py` | 提交信息格式校验（`<type>(<scope>): <summary>`），由 commit-msg hook 调用 |
| `generate-commit-msg.py` | 根据暂存文件自动生成建议提交信息 |
| `install-git-hooks.sh` | 安装项目 Git Hooks（设置 `core.hooksPath`） |

**Git Hooks**：
- `pre-commit`：检查大文件、合并冲突标记、调试断点
- `commit-msg`：验证提交信息格式

```bash
# 安装 Git Hooks
bash tools/install-git-hooks.sh

# 手动验证提交信息
python tools/validate-commit-msg.py --message "feat(vote): 增加投票提交接口"
```

## 技术栈

- **语言**：Python >= 3.11
- **配置**：pydantic-settings
- **测试**：pytest + pytest-asyncio
- **代码质量**：ruff
- **类型检查**：mypy（content_check + loop_logging）
- **机器学习**：scikit-learn（loop_logging 聚类功能）

## 相关文档

- 门禁 Runbook：`docs/runbook/gates/`
- 门禁注册表：`docs/40-dev-loop/gate_registry.yaml`
- 代理角色规范：`docs/40-dev-loop/p2-agent-design/`
- 研发闭环规划：`docs/40-dev-loop/ai-coding-game-dev-loop-plan.md`
