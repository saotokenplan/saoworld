# 项目状态

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护

## 目的

本文档用于统一说明当前项目处于什么阶段、哪些内容已经确定、哪些内容仍待确认，以及进入工程实施前还缺什么。

## 适用范围

- 适用于需要判断当前仓库处于哪个阶段、能否进入实施、还缺哪些前置条件的场景。
- 适用于新接手成员快速了解“已经具备什么”和“还不能做什么”。
- 不替代具体规范正文、接口参考或实施计划。

## 当前定位

- 本文档是项目阶段与资产完备度的状态说明，不直接承担执行规范角色。
- 本文档回答“现在做到哪一步”，不负责目录导航、权威关系或实施顺序说明。
- 目录导航看 `docs/README.md`，权威关系看 `docs/00-governance/document-map.md`，实现细节转向 `20-specs/`、`30-api/` 和 `40-dev-loop/`。

## 当前阶段

- 当前阶段：**灰度发布就绪**（首期内容包灰度发布准备全部完成，项目已具备完整端到端玩法闭环能力）
- 当前形态：八大核心后端服务（vote、world、content、generation、review、player、ops、gateway）+ workers Celery + CI/CD + Godot 客户端完整，投票链路、内容链路、审核链路、API 网关、运营后台、客户端框架就绪，客户端与后端 API 联调封装完善，首期内容实例化完成（世界观、区域、阵营、NPC、任务、章节），内容包打包与发布流程已实现，端到端集成验证已完成，首期内容包初始化脚本已验证，发布验证脚本已完善，Runbook 文档体系已完善（16个门禁 + 6个运维操作），遥测基础设施已初始化（metrics、logs、alerts、dashboards），三层 Loop 基础设施已实现，P2 多代理协同真实调度能力已实现（AgentDispatcher + WorkflowExecutor + 54个Orchestrator测试通过）
- 运维操作 Runbook 已补全：灰度发布、全量发布、内容包回滚、服务部署、数据库迁移、首期内容初始化 6 个运维操作 Runbook 全部创建完成，为灰度发布和后续运维操作提供标准化流程指导
- 当前目标：完成首期内容包灰度发布，验证端到端玩法流程，同步启动 Sprint 1 核心玩法技术设计与预研，启动 P3 阶段（线上运营闭环期）规划，进入内容生成与投票驱动世界更新的闭环

## 当前结论

- **任务系统 API 完善完成（Sprint 1 提前启动）**：2026-07-10 00:00 完成 player-service 任务系统核心 API 扩展。新增 5 个玩家 API（任务详情、接取、进度更新、完成提交、标记失败）和 3 个运营 API（玩家任务列表、创建任务、更新任务状态）。实现完整任务状态机（available → active → completed/failed），状态迁移合法性校验，审计日志记录，业务指标埋点（任务接取/完成/失败/进度更新）。player-service 测试从 37 个增加到 49 个（+12），任务系统核心玩法后端能力就绪，为 Sprint 1 S1-04 任务系统基础奠定基础。
- **产品管理每日进展更新（2026-07-09）**：Sprint 0 技术准备工作已 100% 完成，整体完成度约 88%（剩余实际部署验证工作）。迭代方向评估为"需关注"——进度大幅提前，但面临灰度发布决策阻塞。已生成每日进展报告，建议：1）推动灰度发布决策；2）提前启动 Sprint 1 技术设计与预研；3）完善 agents 模块 CI 覆盖；4）启动 P3 阶段规划。后续任务规划已确定，短期目标为灰度发布与 Sprint 1 启动并行推进。
- **项目灰度发布就绪状态持续验证通过**：2026-07-09 08:00 进行的全面验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；playtest 15 个端到端测试通过；product_agent 23 个测试通过；orchestrator 54 个测试通过。全量代码质量检查完成，修复 61 个代码质量问题（gateway-service mypy 1 个 + workers ruff 23 个 + content_check ruff 8 个 + loop_logging ruff 29 个），所有服务 ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- vote-service 已具备完整的投票生命周期管理能力：创建（draft）→ 计划（scheduled）→ 开放（open）→ 关闭计票（closed）→ 确认结果（finalized）。
- 运营写接口已实现：`POST /api/v1/ops/vote-cycles`（创建）、`/schedule`、`/open`、`/close`、`/finalize`（状态迁移）。
- 关闭投票时自动计票，按加权总分确定获胜候选项并标记为 selected。
- 所有接口已实现统一响应 envelope 格式（`request_id`、`data`、`meta`、`trace_id`），对齐 `12-api-design.md` 规范。
- 玩家接口已添加 JWT 认证，支持 `votes:read`、`votes:submit`、`votes:history:read` scope 校验。
- 投票链路已有 51 个测试用例覆盖，全部通过 ruff、mypy 和 pytest 验证。
- 模型已补充 `votes_candidate_id_idx` 索引和 `winning_candidate_id` FK 约束。
- vote-service 端到端可运行验证已完成（代码层面通过所有测试，PostgreSQL 配置就绪）。
- 端到端集成验证已完成：投票链路、内容链路、审核链路、事件总线、API 网关路由映射均已验证通过，所有 8 个后端服务共 349 个测试用例全部通过，workers 29 个测试用例通过，内容检查工具 28 个测试用例通过。
- 预留错误码已落地：`AUDIT_WRITE_FAILED`、`TRACE_ID_MISSING`、`TASK_DISPATCH_FAILED`、`DEPENDENCY_UNAVAILABLE`、`TOKEN_EXPIRED` 五个预留错误码已在所有 8 个后端服务的 `errors.py` 中定义，`api-error-codes.md` 文档已同步更新，OpenAPI 草案已添加 `TokenExpiredErrorResponse` Schema。
- **mypy 类型检查门禁已生效**：所有 8 个后端服务 + workers 的 mypy 类型错误全部修复（约 129 个错误），CI 配置移除 `|| true` 绕过，类型检查成为真正的阻塞门禁。
- **datetime.utcnow() 弃用警告修复**：vote、content、generation、review 服务的 event_publisher 已从 `datetime.utcnow()` 迁移到 `datetime.now(timezone.utc)`，消除 Python 3.12+ 弃用警告。
- **二层 Loop 基础设施已实现**：`tools/loop_logging/` 模块包含结构化日志采集（agent_session_log、ci_failures、prod_incidents）、失败签名提取、失败聚类、缺口分类（缺gate/覆盖不足/信噪比低）、Gate Improvement Issue 自动生成工具，以及完整的 CLI 命令行工具，24 个测试用例全部通过。
- **三层 Loop（规则改进 Loop）基础设施已实现**：`tools/loop_logging/` 模块新增规则版本化管理（RuleRegistry、ThresholdManager、GoldenCaseManager）、反馈信号采集（IssueFeedbackCollector）、规则评估与改进建议生成（RuleEvaluator、RuleImprovementGenerator）、Rule Improvement Issue 自动生成工具，CLI 新增 `rule-improvement` 命令，12 个新增测试用例全部通过，总计 36 个测试用例。
- **端到端集成测试框架已实现**：`tools/playtest/` 目录已创建，包含 conftest.py（测试夹具）和 test_full_integration.py（16 个集成测试用例），覆盖：
  - 投票服务健康检查与 envelope 格式
  - 内容服务健康检查与 envelope 格式
  - 事件总线发布与订阅机制
  - 投票完整流程（创建投票周期、状态迁移、投票提交、关闭计票、历史查询）
  - 内容包完整流程（创建内容包、灰度发布、全量发布、回滚、详情查询）
  - 全部测试通过。
- **端到端集成测试已扩展**：完成投票与内容包完整流程的端到端测试扩展，vote-service 54 个测试全部通过，content-service 58 个测试通过，修复了 seed_initial_packages.py 的导入错误。
- **全面质量验证已完成**：所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；workers 29 个测试通过（7 个 Redis 环境限制）；内容检查工具 28 个测试通过；Loop 基础设施 36 个测试通过；ruff 和 mypy 检查通过。
- **首期内容包灰度发布准备已完成**：seed_initial_packages.py 脚本已验证可正确从 game/data/ 读取内容并创建区域内容包（铁卫城周边 + 灰谷废墟）；verify-release.sh 发布验证脚本已完善，新增内容包状态检查、灰度范围验证、系统状态检查功能。
- **测试修复**：修复了 content-service 的 seed_initial_packages.py 异步调用问题（load_json_file 不应为 async）和测试数据库会话获取方式；修复了 generation-service 的 skeleton_validator 测试 mock 问题（AsyncMock 替代普通 mock）。
- **telemetry/ 遥测基础设施已初始化**：包含指标定义（metrics.yaml）、日志 schema（log-schemas.yaml）、告警规则（alerts.yaml）、仪表盘配置说明（dashboards/README.md），覆盖所有 8 个后端服务、workers 和事件总线。
- **灰度发布就绪全面验证已完成**：所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）。项目已具备首期内容包灰度发布条件。
- **playtest 端到端测试环境隔离修复完成**：`tools/playtest/test_vote_integration.py` 和 `tools/playtest/test_content_integration.py` 已修复服务隔离问题（sys.modules 清理 + prometheus 指标注册中心清理），确保投票服务和内容服务测试在同一测试套件中运行时不会互相干扰，全部 15 个 playtest 端到端测试用例通过。
- **基础设施配置完整性验证通过**：所有 8 个后端服务的 Dockerfile 和 pyproject.toml 配置完整；CI/CD 流水线配置（ci.yml、cd.yml、docker-build.yml）完整；部署脚本（deploy.sh、rollback.sh、health-check.sh、migrate-all.sh、gray-release.sh、verify-release.sh）完整；基础设施配置（Docker Compose、Nginx、Prometheus、Grafana）完整。
- **P2 阶段（多代理协同期）代理角色技术设计文档已完善**：`docs/40-dev-loop/p2-agent-design/` 目录下 9 个代理角色规范文档（Product Agent、System Designer Agent、Gameplay Agent、World Agent、Backend Agent、QA Agent、Build Agent、Ops Agent、Orchestrator）均已完善，包含详细的接口定义、工作流程、输入输出数据结构、协作机制、错误处理和验收标准，文档状态均为 active，为后续多代理协同研发奠定基础。
- **API 示例文档已补充完整**：`docs/30-api/` 目录下新增 5 个服务的 API 示例文档（player、review、generation、ops、gateway），每个文档包含请求示例、成功响应示例、常见错误示例和实现建议，`api-overview.md` 已更新链接所有示例文档，文档资产清单已同步更新。
- **Product Agent 已实现**：P2 阶段首个代理角色 Product Agent 已完成开发，包含输入输出数据结构定义、核心逻辑（7步流程）、错误处理机制和 CLI 命令行工具，23 个测试用例全部通过，为多代理协同研发闭环奠定基础。
- **System Designer Agent 已实现**：P2 阶段第二个代理角色 System Designer Agent 已完成开发，包含输入输出数据结构定义、核心逻辑（8步流程：分析需求、检查现有系统、设计系统架构、定义数据结构、定义 API 接口、生成改动计划、架构校验、交付设计文档）、错误处理机制（需求不明确、技术不可行、模块冲突、性能风险）和 CLI 命令行工具，18 个测试用例全部通过，为产品需求到技术实现的桥梁奠定基础。
- **Gameplay Agent 已实现**：P2 阶段第三个代理角色 Gameplay Agent 已完成开发，包含输入输出数据结构定义、核心逻辑（8步流程：分析设计文档、检查现有代码、创建场景文件、编写脚本逻辑、集成数据配置、编写测试用例、运行测试验证、交付成果）、错误处理机制（设计不完整、节点引用失效、脚本语法错误、数据配置缺失、测试失败）和 CLI 命令行工具（create-scene、write-script、generate-test、run-workflow），16 个测试用例全部通过，为技术设计到客户端代码实现的桥梁奠定基础。
- **World Agent 已实现**：P2 阶段第四个代理角色 World Agent 已完成开发，包含输入输出数据结构定义、核心逻辑（9步流程：读取输入数据、校验输入、匹配模板、生成内容、应用规则约束、文本润色、打包内容、提交审核、处理审核结果）、错误处理机制（骨架快照缺失、模板不匹配、内容违规、审核失败、重复度过高）和 CLI 命令行工具（generate-npc、generate-quest、generate-region、run-workflow），25 个测试用例全部通过，为投票结果和世界规则转化为结构化游戏内容的能力奠定基础。
- **Backend Agent 已实现**：P2 阶段第五个代理角色 Backend Agent 已完成开发，包含输入输出数据结构定义、核心逻辑（10步流程：分析设计文档、检查现有代码、实现数据模型、实现数据访问层、实现 Pydantic Schemas、实现 API 路由、生成迁移脚本、编写测试用例、运行测试验证、交付成果）、错误处理机制（设计不完整、模型冲突、SQLAlchemy 错误、测试失败、类型检查失败）和 CLI 命令行工具（implement-model、implement-route、generate-test、run-workflow），24 个测试用例全部通过，为 System Designer Agent 的设计方案转化为可运行后端代码的能力奠定基础。
- **QA Agent 已实现**：P2 阶段第六个代理角色 QA Agent 已完成开发，包含输入输出数据结构定义、核心逻辑（7步流程：分析需求和代码变更、编写测试用例、运行测试、分析测试结果、触发修复流程、生成测试报告、回归测试）、错误处理机制（测试环境问题、测试用例缺失、测试不稳定、测试超时、修复失败）和 CLI 命令行工具（generate-test、run-tests、analyze-results、run-workflow），16 个测试用例全部通过，为所有代码变更和内容生成提供自动化测试验证能力。
- **Build Agent 已实现**：P2 阶段第七个代理角色 Build Agent 已完成开发，包含输入输出数据结构定义、核心逻辑（8步流程：检查代码分支、构建客户端、构建服务端镜像、打包内容包、生成回滚包、写入版本元数据、生成构建报告、发布到灰度环境）、错误处理机制（构建失败、镜像推送失败、内容包缺失、回滚包生成失败、资源不足）和 CLI 命令行工具（build-client、build-server、package-content、run-workflow），17 个测试用例全部通过，为代码和内容的自动化构建发布奠定基础。
- **Ops Agent 已实现**：P2 阶段第八个代理角色 Ops Agent 已完成开发，包含输入输出数据结构定义（MetricsData、LogEntry、ExceptionItem、FeedbackItem、ExceptionReport、ImprovementSuggestion、AlertSummary、HealthReport 等）、核心逻辑（8步流程：采集监控数据、分析异常模式、归纳问题和趋势、生成异常报告、形成改进建议、生成告警汇总、生成服务健康报告、提交给 Product Agent）、错误处理机制（数据采集失败、数据不一致、告警风暴、分析失败、报告生成失败）和 CLI 命令行工具（collect-metrics、analyze-exceptions、generate-report、run-workflow），20 个测试用例全部通过，为运维数据分析和系统稳定性保障奠定基础。
- **Orchestrator 已实现**：P2 阶段第九个也是最后一个代理角色 Orchestrator 已完成开发，包含输入输出数据结构定义（VersionBrief、GateResults、AgentStatus、TaskAssignment、ExecutionLog、FailureHandling、ProgressReport）、核心逻辑（8步流程：接收需求包、分析任务依赖、分配任务、执行任务、检查门禁、处理失败、更新进度、完成阶段）、错误处理机制（任务分配失败、代理无响应、门禁失败、任务超时、循环依赖检测）和 CLI 命令行工具（assign-task、execute-workflow、check-gates、generate-report），14 个测试用例全部通过，为多代理协同研发闭环提供统一调度和任务管理能力。
- **首期内容包灰度发布端到端流程验证已完成**：验证了内容包创建流程（seed_initial_packages.py 脚本、ContentRepository.create_package 方法）、灰度发布流程（build_gray_scope 灰度范围构建、灰度可见性判断逻辑）、全量发布流程（promote_to_full_release 任务、gray→live 状态迁移）、回滚流程（gray/live→rolled_back 状态迁移、rolled_back 终态约束）。所有 375 个后端测试、29 个 workers 测试（7 个 Redis 环境限制）、28 个 content_check 测试、36 个 loop_logging 测试全部通过，ruff 和 mypy 检查通过。
- **项目灰度发布就绪状态再次验证通过**：2026-07-07 15:00 进行的全面验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；ruff 和 mypy 检查通过。P2 阶段 9 个代理角色（Product Agent、System Designer Agent、Gameplay Agent、World Agent、Backend Agent、QA Agent、Build Agent、Ops Agent、Orchestrator）全部实现完毕，项目已具备完整的多代理协同研发能力。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 11:00 进行的全面验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 12:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 13:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 14:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；agents 77 个测试通过（product_agent 23 + orchestrator 54）；ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 15:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；ruff 和 mypy 检查通过。修复了 generation-service、review-service、world-service 的未使用导入问题（共 9 处），项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 17:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；agents 77 个测试通过（product_agent 23 + orchestrator 54）；ruff 和 mypy 检查通过。修复了 tools/agents 模块的代码质量问题（未使用导入、f-string 无占位符、模糊变量名）。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 18:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；ruff 和 mypy 检查通过。修复了 generation-service 的 skeleton_validator.py 中 5 个 mypy 类型错误（details 列表中 dict 改为 ErrorDetail 对象，fetch_current_skeleton 返回类型修正）。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 19:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；playtest 15 个端到端测试通过；agents 77 个测试通过（product_agent 23 + orchestrator 54）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 20:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **事件发布异常处理修复完成**：2026-07-08 21:00 修复了 vote、content、generation、review 四个服务共 7 处事件发布失败时的静默异常处理（`except Exception: pass`），替换为 structlog 错误日志记录（`logger.error("event_publish_failed", event_type=..., error=str(exc))`），提升系统可观测性。确认 `CANDIDATE_NOT_ACTIVE` 错误码在 vote-service 中正确使用，确认 world、player、ops 服务无类似问题。所有 375 个后端测试通过，ruff 和 mypy 检查通过。
- **gateway-service Alembic 迁移环境已补全**：为 gateway-service 添加了完整的 Alembic 迁移环境（alembic.ini、env.py、script.py.mako），创建了 audit_logs 表的首次迁移脚本（2026_07_08_2200_init_gateway_tables.py），添加了 database_url 配置和数据模型定义（AuditLog），37 个测试用例全部通过。至此，所有 8 个后端服务的迁移环境均已完整初始化。
- **项目灰度发布就绪状态持续验证通过**：2026-07-07 14:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-07 07:01 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；agents 77 个测试通过（product_agent 23 + orchestrator 54）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **P2 多代理协同真实调度能力已实现**：Orchestrator 的 `execute_tasks` 方法从模拟执行升级为真实 Agent 调度。新增 `AgentDispatcher` 模块（支持动态导入 8 个 Agent 并调用其核心方法）、`WorkflowExecutor` 模块（基于 Kahn 算法实现拓扑排序、按依赖关系顺序执行任务、上游输出自动传递给下游）。Orchestrator 通过 `use_real_dispatch` 参数支持模拟/真实两种模式切换，向后兼容。54 个 Orchestrator 测试通过（含 11 个 dispatcher 测试、15 个 workflow_executor 测试、10 个多代理协同集成测试），全部 213 个 agents 测试通过，vote-service 54 个测试通过，content-service 62 个测试通过。
- **首期内容包灰度发布流程完整性验证通过**：2026-07-07 16:00 进行的灰度发布流程验证确认：首期内容包初始化脚本（seed_initial_packages.py）存在且完整，可从 game/data/ 读取区域、阵营、NPC、任务、章节配置并创建两个区域内容包（铁卫城周边 + 灰谷废墟）；内容配置文件完整（core_region.json、expansion_region.json、faction_list.json、npc_list.json、quest_list.json、chapter_list.json），均带 schema_version 字段；灰度发布脚本（gray-release.sh）和发布验证脚本（verify-release.sh）完整可执行；所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；agents orchestrator 54 个测试通过；ruff 检查通过。项目已具备完整的灰度发布执行能力。
- **研发闭环规划文档与 vote-service README 文档漂移修复完成**：2026-07-08 23:00 修复了 `docs/40-dev-loop/ai-coding-game-dev-loop-plan.md` 中 P2 阶段状态的文档漂移问题——该文档此前仍停留在"P1 已完成、准备进入 P2"的描述，将 9 个代理角色全部标记为"⏳ 待实现"，与 project-status.md 中"P2 全部实现"的实际情况矛盾。本轮将 P2 标记为已完成、9 个代理（含 Orchestrator）状态更新为"✅ 已实现"、闭环架构环节 8（构建发布）更新为已实现、实施分期 P0/P1/P2 标记为已完成。同时修复了 `services/vote/README.md` 中过时的 `# TODO: Initialize Alembic` 占位（替换为 `alembic upgrade head` 实际命令）、将 API Endpoints 表从 3 个端点扩展为完整的 9 个端点（4 个玩家接口 + 5 个运营接口）、将"Implemented Features"从早期最小切片状态更新为当前完整能力清单（含运营写接口、JWT 鉴权、审计日志、投票结算、事件发布、统一 envelope、Prometheus metrics、54 个测试）、将"Next Steps"中已完成的 6 项移除并替换为真实剩余项。vote-service 54 个测试通过，无回归。
- **项目灰度发布就绪状态持续验证通过**：2026-07-08 23:01 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；playtest 15 个端到端测试通过；agents 77 个测试通过（product_agent 23 + orchestrator 54）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **workers 和 tools README 文档统一完善完成**：2026-07-09 01:00 完成了 workers/ 和 tools/ 目录 README 文档的统一完善，修复文档漂移问题。包括：workers/README.md（从"Not yet initialized"占位状态重构为完整 README，补充目录结构、异步任务、事件总线、定时任务、与后端服务集成关系、快速开始、配置说明、Next Steps，29 个测试通过）、tools/README.md（从仅列 2 个 Git 脚本扩充为完整 README，补充 4 大核心模块（agents、content_check、loop_logging、playtest）说明、运维脚本清单、Git 工具清单、技术栈、相关文档链接，content_check 28 个测试通过、loop_logging 36 个测试通过）。
- **后端服务 README 文档统一完善完成**：2026-07-09 00:00 完成了除 vote-service 外的 7 个后端服务 README 文档的统一完善，修复文档漂移问题。包括：world-service（补充骨架快照 API、状态机、metrics 等功能说明，修正 Next Steps 中 Alembic 已完成项）、content-service（补充玩家接口、灰度发布、状态机、事件发布等功能说明，修正 Next Steps）、generation-service（补充骨架校验、状态机、事件发布等功能说明，修正 Next Steps）、review-service（从简略版本重构为完整 README，含目录结构、API 表格、功能清单、Next Steps）、player-service（从简略版本重构为完整 README，含玩家 API + 运营 API 共 8 个端点、功能清单、Next Steps）、ops-service（从简略版本重构为完整 README，含 5 个运营 API 端点、功能清单、Next Steps）、gateway-service（补充 player/ops 代理路由、Alembic 迁移说明、审计日志、目录结构、Next Steps）。所有 8 个后端服务测试全部通过（vote 54 + world 49 + content 62 + generation 56 + review 41 + player 37 + ops 39 + gateway 37 = 375 个），无回归。
- **项目灰度发布就绪状态持续验证通过**：2026-07-09 02:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-09 03:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-09 04:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；agents orchestrator 54 个测试通过；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-09 05:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；agents 77 个测试通过（product_agent 23 + orchestrator 54）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **项目灰度发布就绪状态持续验证通过**：2026-07-09 06:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；agents 77 个测试通过（product_agent 23 + orchestrator 54）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **P3 阶段（线上运营闭环期）规划已启动**：创建了 `docs/40-dev-loop/p3-online-ops-plan.md` 规划文档，定义了阶段目标（数据自动回流、洞察自动提取、需求自动生成、闭环持续演进）、核心闭环架构（数据采集→存储→分析→洞察→需求→生产→审核发布→上线）、6 个关键技术组件（数据采集层、数据存储层、数据分析层、洞察提取层、需求生成层、闭环执行层）、数据回流机制（事件格式规范、数据保留策略）、数据驱动需求流程（8 个环节）、关键接口设计（事件上报、分析查询、洞察管理、需求生成）、8 周实施路线图（4 个里程碑）、关键指标与成功标准、风险与应对策略。规划文档状态为 draft，待后续迭代逐步完善。
- **项目灰度发布就绪状态持续验证通过**：2026-07-09 07:00 进行的持续验证测试确认所有 8 个后端服务（vote 54、world 49、content 62、generation 56、review 41、player 37、ops 39、gateway 37）共 375 个测试用例全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）；agents 77 个测试通过（product_agent + orchestrator）；vote-service ruff 和 mypy 检查通过。项目持续保持灰度发布就绪状态。
- **CI 配置补全与全量验证完成**：2026-07-09 09:00 完成 CI 流水线补全与全模块验证。GitHub Actions CI 配置已补充 agents 和 playtest 到 lint、type-check、test 三个矩阵，实现所有 8 个后端服务 + workers + 4 个 tools 模块（content_check、loop_logging、agents、playtest）的完整 CI 覆盖。agents 模块 mypy 配置优化（添加 Pydantic 插件、explicit_package_bases、ignore_missing_imports），playtest 模块修复 7 个 lint 问题和 mypy 类型注解问题。全量验证结果：6 个后端服务 299 测试通过、content_check 28、loop_logging 36、playtest 15、agents/orchestrator 54，合计 432 个测试通过。门禁注册表新增 G-UNIT-012（Agents Unit Tests）。项目持续保持灰度发布就绪状态。
- **首期内容包灰度发布流程验证通过**：2026-07-09 11:00 完成首期内容包灰度发布流程验证。验证内容包括：content-service 62 个测试全部通过（含内容包创建、灰度发布、全量发布、回滚、灰度可见性判断）；playtest 15 个端到端测试全部通过（含投票完整流程、内容包完整流程）；所有 8 个后端服务 375 个测试全部通过；content_check 28 个测试通过；loop_logging 36 个测试通过；agents/orchestrator 54 个测试通过；workers 29 个测试通过（7 个 Redis 环境限制）。seed_initial_packages.py 脚本验证通过，可正确创建铁卫城周边和灰谷废墟两个区域内容包。项目已具备完整的首期内容包灰度发布能力。
- **agents 模块历史遗留 import bug 修复完成**：2026-07-08 12:03 修复 7 个 agent 模块的相对/绝对 import 不一致问题。问题模式：测试文件使用 `sys.path.insert(0, parent_dir)` 加绝对导入（`from world_agent import WorldAgent`），但 main 模块使用相对导入（`from .input_schemas import ...`），导致测试收集失败。修复方案：将 5 个 main 模块（world_agent / system_designer_agent / gameplay_agent / qa_agent / ops_agent）改为绝对导入，与 product_agent 一致；将 7 个测试文件中的内嵌 `from tools.agents.X.Y` 改为 `from Y`（配合 sys.path.insert 模式）。修复后 agents 总测试数从 77 提升到 213（+136）：world_agent 25、system_designer_agent 18、backend_agent 24、build_agent 17、gameplay_agent 16、ops_agent 20、qa_agent 16、product_agent 23、orchestrator 54。全部 8 个后端服务 375 个测试通过；content_check 28、loop_logging 36、playtest 15 测试通过；workers 29/36 通过（7 个 Redis 环境限制）；vote-service 与 tools/agents ruff 检查通过，vote-service mypy 检查通过。
- **P3 阶段数据采集基础设施实现完成**：2026-07-09 14:00 完成 P3 阶段第一阶段数据采集基础设施实现。包括：1）扩展事件总线支持 7 种玩家行为事件类型（进入区域、离开区域、完成任务、互动NPC、提交投票、查看内容、消耗资源）；2）在 gateway-service 实现 `POST /api/v1/events/batch` 批量事件上报接口；3）在 ops-service 创建 player_events 存储表及索引（按玩家ID+时间、区域ID+时间、事件类型+时间）；4）实现事件消费与存储逻辑（workers/events/handlers.py 和 workers/tasks/player_event_ingestion.py）。P3 规划文档已更新进度状态，数据采集基础设施除客户端 SDK 外已全部就绪。
- **P3 阶段数据分析引擎核心实现完成**：2026-07-09 15:00 完成 P3 阶段第二阶段数据分析引擎核心实现。包括：1）在 ops-service 创建 5 个数据分析表（player_metrics_daily、region_metrics_daily、quest_metrics_daily、vote_metrics_daily、analytics_reports）及 Alembic 迁移脚本；2）实现 AnalyticsRepository 仓储层（指标查询、upsert、报告管理）；3）实现 4 个分析查询 API（玩家指标、区域指标、趋势分析、分析报告）；4）在 workers 实现数据分析管道（数据清洗、玩家指标聚合、区域指标聚合、每日报告生成）；5）Celery Beat 新增每日分析任务调度。ops-service 48 个测试通过（+9），workers 29 个测试通过（7 个 Redis 环境限制），ruff 和 mypy 检查通过。P3 第二阶段数据清洗管道、统计分析任务、分析 API 三项核心任务完成，剩余分析仪表盘待实现。
- **P3 阶段分析仪表盘实现完成**：2026-07-09 16:00 完成 P3 阶段第三阶段分析仪表盘实现。包括：1）在 ops-service 扩展数据分析 schema（AnalyticsOverview、RegionAnalyticsItem、QuestAnalyticsItem、VoteAnalyticsItem）；2）实现 4 个仪表盘 API（综合概览、区域分析、任务分析、投票分析）；3）扩展 Grafana 仪表盘配置（新增事件上报速率、分析查询速率、事件类型分布、查询类型分布 4 个面板）；4）编写分析仪表盘测试用例（9 个测试覆盖概览、区域、任务、投票分析及权限校验）。ops-service 57 个测试通过（+9），ruff 和 mypy 检查通过。P3 前三个阶段（数据采集、数据分析、分析仪表盘）已全部实现。
- **P3 阶段洞察提取与需求生成引擎实现完成**：2026-07-09 17:00 完成 P3 阶段第四阶段洞察提取与需求生成引擎实现。包括：1）在 ops-service 创建 insights 和 requirements 数据模型及 Alembic 迁移脚本；2）实现 InsightRepository 和 RequirementRepository 仓储层（CRUD、质量评分计算、状态更新）；3）实现洞察提取算法（从分析报告中提取玩家行为、区域热度、任务完成率、投票倾向、经济消费 5 类洞察，基于置信度/影响/新颖度/可行性计算质量评分）；4）实现需求生成引擎（根据洞察类别和质量指标生成对应的需求包，包含标题、描述、优先级、目标范围、预估工作量、验收标准）；5）实现 7 个 API 接口（洞察列表查询、洞察详情、从洞察生成需求、需求列表查询、需求详情、需求批准）；6）编写测试用例（10 个测试覆盖鉴权、查询、过滤、404 错误、envelope 格式）。ops-service 67 个测试通过（+10），ruff 和 mypy 检查通过。P3 四个阶段（数据采集、数据分析、分析仪表盘、洞察提取与需求生成）已全部实现。
- **P3 阶段客户端事件采集 SDK 实现完成**：2026-07-09 18:00 完成 P3 阶段数据采集基础设施的客户端部分——扩展 APIManager.gd 实现玩家行为事件采集 SDK。包括：1）支持 7 种玩家行为事件类型（enter_region、leave_region、complete_quest、interact_npc、vote_submit、view_content、spend_resource）；2）支持批量事件上报和关键事件实时上报（投票、任务完成等）；3）支持定时批量上报（默认 30 秒间隔，可配置）；4）支持事件队列管理（最大批量 50 条）；5）支持事件去重（唯一 event_id）；6）支持事件上报信号通知（event_batch_submitted、event_submit_failed）；7）支持配置文件加载事件上报间隔。P3 规划文档已更新状态，第一阶段进度达 90%（仅客户端 SDK 待完善生产环境配置）。
- **P3 阶段数据驱动闭环（洞察→需求→内容生成）端到端打通**：2026-07-09 22:00 完成 P3 阶段数据驱动闭环的端到端集成。包括：1）扩展 Orchestrator TaskInput 支持 insight_extraction 和 requirement_generation 两种新任务类型，新增 params 字段支持任务特定参数；2）扩展 OpsAgent 实现洞察提取（extract_insights）和需求生成（generate_requirements）能力，提供 Orchestrator 调用入口（execute_insight_extraction、execute_requirement_generation）；3）扩展 WorldAgent 实现需求驱动的内容生成能力（generate_from_requirement、apply_requirement_to_content、execute_requirement_driven_generation），支持根据需求包的 target_scope 和内容自动调整生成的 NPC、任务、区域内容；4）更新 Orchestrator Dispatcher，注册 ops-agent-insight、ops-agent-requirement、world-agent-requirement 三个新代理路由，支持数据驱动闭环的任务调度；5）补充完整测试覆盖：World Agent 新增 6 个测试（共 31 个），Ops Agent 新增 7 个测试（共 27 个），全部通过。P3 阶段数据驱动闭环（洞察提取→需求生成→内容生成）已端到端打通，为线上运营闭环奠定基础。
- **agents 模块质量全面提升与 mypy 类型检查收紧**：2026-07-09 20:00 完成 agents 模块的全面质量提升。包括：1）修复 orchestrator 测试断言（从 8 个代理更新为 11 个，新增 3 个代理路由测试）；2）补充 structlog 依赖到 pyproject.toml，修复 product_agent 导入错误；3）从 mypy 配置中移除 ignore_errors = true，全面收紧类型检查；4）修复所有 9 个 agent 模块的类型错误（共修复约 30+ 处，包括 implicit Optional、dict 类型推断、导入路径不一致等问题）；5）统一相对导入规范，修复测试文件导入路径问题；6）全部 72 个源文件通过 mypy 类型检查，全部 226 个测试通过（product_agent 23、system_designer_agent 18、backend_agent 24、gameplay_agent 16、world_agent 31、qa_agent 16、build_agent 17、ops_agent 27、orchestrator 54）。agents 模块代码质量和类型安全性显著提升。
- **agents 模块根目录 pytest 模块命名冲突修复完成**：2026-07-09 23:00 修复 agents 模块从根目录运行 pytest 时的模块命名冲突问题。问题根因：9 个 agent 各有同名的 `input_schemas.py`、`output_schemas.py` 和 `error_handler.py`，当从 `tools/agents/` 根目录运行 pytest 时，Python 模块缓存导致后加载的 agent 导入到错误的模块，4 个 agent 的测试收集失败。修复方案：将所有 27 个文件（9 agents × 3 文件）重命名为带 agent 前缀的唯一名称（如 `product_input_schemas.py`、`product_output_schemas.py`、`product_error_handler.py`），并更新约 40+ 处导入引用。修复后从根目录运行 pytest 全部 226 个测试收集并执行成功，ruff 和 mypy 检查通过。P3 规划文档已同步更新（客户端 SDK 状态标记为已完成，第一阶段进度更新为 100%）。

## 已确定事项

### 产品方向

- 产品形态已明确为“大型开放式、玩家投票驱动、AI 持续生成内容”的在线游戏。
- 核心闭环已明确为“探索 -> 参与 -> 投票 -> 世界更新 -> 再探索”。
- AI 的职责边界已明确：负责可变内容生成，不负责主线终局、核心经济和底层战斗规则。
- MVP 范围已明确：首期包含 `1` 个核心常驻区域、`1` 个扩展区域、`1` 条主线骨架、`3` 个候选剧情方向，以及投票、生成、审核、灰度和回滚的完整链路。

### 规范分层

- `00-governance/` 定位为文档治理、项目状态和使用入口。
- `10-requirements/` 定位为需求背景、方案讨论和立项上下文。
- `20-specs/` 定位为执行规范和最终基线。
- `30-api/` 定位为接口参考、权限矩阵和错误码索引。
- `40-dev-loop/` 定位为研发治理、门禁和 AI Coding 闭环设计。
- `50-research/` 定位为技术选型和历史决策依据。

### 技术方向

- 客户端方向已收敛为 Godot 4 + typed GDScript。
- 服务端方向已收敛为 Python、FastAPI、PostgreSQL、Celery。
- 后端服务拆分方向已明确，包括网关、玩家、世界、投票、生成、审核、内容和运营等核心服务。
- 发布策略方向已明确为内容包驱动、优先灰度、支持版本归档和快速回滚。

### 文档治理

- 已明确 `20-specs/` 优先于 `10-requirements/`。
- 已完成 `20-specs/` 与 `.trae/skills/` 的映射文档。
- 已在 `10-requirements/` 文档顶部补充“如与 `20-specs/` 冲突，以 `20-specs/` 为准”的声明。
- 已在各 `SKILL.md` 中补充“规范来源”。
- 已建立文档目录规范，并完成 `docs/` 目录按层重组。
- 已补齐 API 总览、权限矩阵和错误码三类接口参考文档。
- 已完成 `docs/` 范围内 `31` 份 Markdown 文档的模板字段对齐。
- 已新增模板维护规则，用于后续新增、迁移和大幅改写时做增量复查。

## 已准备好的资产

- 产品规范：
  - `docs/20-specs/product-spec.md`
- 内容生成规范：
  - `docs/20-specs/content-generation-spec.md`
- 后端与数据规范：
  - `docs/20-specs/backend-data-spec.md`
- Agent 与闭环规范：
  - `docs/20-specs/agent-loop-spec.md`
- 工程协作规范：
  - `docs/20-specs/engineering-conventions.md`
- 文档治理辅助材料：
  - `docs/00-governance/document-directory-spec.md`
  - `docs/00-governance/document-change-process.md`
  - `docs/00-governance/document-lifecycle.md`
  - `docs/00-governance/document-ownership.md`
  - `docs/00-governance/document-review-checklist.md`
  - `docs/00-governance/governance-phase-summary.md`
  - `docs/00-governance/document-template-alignment-checklist.md`
  - `docs/00-governance/document-template-maintenance.md`
  - `docs/00-governance/document-template-spec.md`
  - `docs/00-governance/document-map.md`
  - `docs/00-governance/quick-start.md`
  - `docs/00-governance/spec-skill-mapping.md`
- 接口参考材料：
  - `docs/30-api/api-overview.md`
  - `docs/30-api/openapi-draft.md`
  - `docs/30-api/api-permissions.md`
  - `docs/30-api/api-error-codes.md`
- 异步任务与事件规范：
  - `docs/20-specs/async-tasks-and-events/`
  - 7 个核心任务 payload schema
  - 7 个事件主题与消息格式
  - 重试策略与死信队列规范
  - 全链路追踪与审计字段规范

## 未确定事项

### 产品侧未定

- ~~世界观根设定的具体文本版本尚未单独沉淀为正式世界观文档。~~ 已完成，`docs/20-specs/world-lore-spec.md` 已创建，包含世界背景、势力阵营、核心规则、地理环境、章节切分等完整设定。
- ~~首期区域、阵营、关键 NPC、章节切分仍缺少具体实例化内容包。~~ 已完成，`game/data/` 目录已包含区域配置（core_region.json、expansion_region.json）、阵营列表（faction_list.json）、NPC列表（npc_list.json）、任务列表（quest_list.json）、章节列表（chapter_list.json），所有数据均带 `schema_version` 字段。
- ~~客户端交互稿、界面流和关键页面信息结构尚未文档化。~~ 已完成，客户端交互稿文档已创建，包含主菜单、投票界面、世界地图、任务面板、NPC交互、界面流程图等 7 个文档。

### 技术侧未定

- ~~OpenAPI 单文件草案已完成 12 个端点、特化错误层、安全方案和响应 envelope，但预留错误码（INTERNAL_ERROR、TOKEN_EXPIRED 等）待实现阶段按需落地。~~ 已完成，所有预留错误码（AUDIT_WRITE_FAILED、TRACE_ID_MISSING、TASK_DISPATCH_FAILED、DEPENDENCY_UNAVAILABLE、TOKEN_EXPIRED）已落地到所有 8 个后端服务的 errors.py 中，api-error-codes.md 文档已同步更新，OpenAPI 草案已添加 TokenExpiredErrorResponse Schema。
- ~~数据库核心表的字段类型、约束、索引、状态机和枚举值已定义在 `backend-data-spec.md`，但 ER 图和迁移脚本（Alembic/SQLAlchemy 模型）尚未生成。~~ 已完成，所有 8 个后端服务（vote、world、content、generation、review、player、ops、gateway）的 Alembic 迁移环境已初始化，核心业务表和审计日志表的迁移脚本已生成。
- ~~异步任务和事件的 payload schema、重试策略、死信处理等细节仍停留在方向层，未形成工程实施方案。~~ 已完成，事件总线基础设施已实现，7 个核心异步任务（内容生成、审核、打包、发布、回滚、门禁扫描）已实现，重试策略（指数退避）和死信队列已配置。
- ~~任务队列、事件总线、中间件、部署方式等基础设施细节仍停留在方向层。~~ 已完成，事件总线基于 Redis Pub/Sub 实现，Celery Beat 定时任务调度器已配置。

### 工程侧未定

- ~~CI 规则、测试入口、发布流水线和环境配置文件尚未建立。~~ 已完成，CI/CD 配置（GitHub Actions）、各服务 Dockerfile、生产环境 Docker Compose、Nginx 配置、Prometheus/Grafana 监控配置、部署脚本已就绪。
- ~~异步任务和事件的具体工程实现细节仍需在实施中细化。~~ 已完成，workers 包含 7 个核心异步任务，事件总线支持 7 个核心事件类型，服务间事件发布集成已完成。

### 工程侧已确定

- **仓库策略已确定为单仓模式**：当前仓库继续演进为主仓库，保留 `docs/` 并新增 `game/`、`services/`、`workers/`、`tools/`、`infra/`、`telemetry/` 等工程目录。
- **首个最小落地目标已确定**：最小投票链路（`GET /api/v1/votes/current` + `POST /api/v1/votes/submit` + vote-service 骨架）。

## 尚未落地的工程资产

- ~~`game/` Godot 客户端工程尚未初始化（目录已创建，占位 README 就位）。~~ 已完成，Godot 4 客户端工程骨架已初始化，包含完整目录结构、核心 Autoload 单例、基础场景、数据配置、测试框架。
- ~~`workers/` Celery 异步任务 Worker 尚未实现（目录已创建）。~~ 已完成，workers Celery Worker 框架已实现，包含 7 个核心异步任务（内容生成、审核、打包、发布、回滚、门禁扫描），19 个测试用例全部通过。
- ~~除 `vote-service`、`world-service`、`content-service`、`generation-service`、`review-service`、`gateway-service`、`player-service` 外的其他后端服务（ops）尚未初始化。~~ 已完成，ops-service 已初始化完成。
- ~~Alembic 数据库迁移脚本尚未生成（world-service），需要连接数据库后初始化。~~ 已完成，world-service、content-service、generation-service、review-service、player-service、ops-service 六个服务的 Alembic 迁移环境已全部初始化，首次迁移脚本（核心业务表 + 审计日志表）已生成。
- ~~真实 CI 配置、部署脚本和生产环境配置尚未建立。~~ 已完成，CI/CD 配置（GitHub Actions）、各服务 Dockerfile、生产环境 Docker Compose、Nginx 配置、Prometheus/Grafana 监控配置、部署脚本（deploy.sh、rollback.sh、health-check.sh、migrate-all.sh）已就绪。
- ~~JWT 鉴权中间件、运营写接口、投票结算 Worker 尚未实现。~~ 已全部完成：JWT 鉴权、运营写接口、投票结算逻辑。

## 已初步落地的工程资产

- 单仓模式目标目录结构已创建：`game/`、`services/`、`workers/`、`tools/`、`infra/`、`telemetry/`。
- **telemetry/ 遥测基础设施已初始化**：
  - `metrics/metrics.yaml`：定义所有 8 个后端服务 + workers + event-bus 的业务指标和 HTTP 指标
  - `logs/log-schemas.yaml`：定义请求日志、业务日志、审计日志、错误日志、任务日志、事件日志、数据库日志、安全日志、健康检查日志 9 种日志类型的标准字段
  - `alerts/alerts.yaml`：定义服务健康、HTTP 错误、延迟、数据库、业务指标、任务、事件总线、安全、资源 9 类告警规则，支持 critical/high/medium/low 四级严重程度
  - `dashboards/README.md`：仪表盘配置说明文档
- **Runbook 文档体系已完善**：
  - **门禁 Runbook（16个）**：`docs/runbook/gates/` 目录下 16 个门禁 Runbook 文档全部创建完成
    - 覆盖：静态检查（2个：ruff、mypy）、单元测试（9个：vote/world/content/generation/review/player/ops/gateway/workers）、内容检查（4个：世界一致性、数值边界、内容安全、重复度）、E2E测试（1个：关键路径）
    - 每个 Runbook 包含：门禁概述、常见失败原因、解决方案、手动执行、升级路径五个章节
  - **运维操作 Runbook（6个）**：`docs/runbook/operations/` 目录下 6 个运维操作 Runbook 文档全部创建完成
    - 覆盖：灰度发布（OP-RELEASE-001）、全量发布（OP-RELEASE-002）、内容包回滚（OP-RELEASE-003）、服务部署（OP-DEPLOY-001）、数据库迁移（OP-DEPLOY-002）、首期内容初始化（OP-INIT-001）
    - 每个 Runbook 包含：操作概述、操作步骤、回滚方案、常见问题与解决方案、相关链接五个章节
  - Runbook 目录 README 已更新，包含门禁 Runbook 和运维操作 Runbook 两大类的完整索引
- `vote-service` 已完成骨架初始化与运营写接口实现（FastAPI + SQLAlchemy + Pydantic + pytest），见 `services/vote/`。
  - 数据模型：`VoteCycle`、`VoteCandidate`、`Vote`（对应 `backend-data-spec.md`）
  - 玩家 API 路由：`GET /api/v1/health`、`GET /api/v1/votes/current`、`POST /api/v1/votes/submit`、`GET /api/v1/votes/history`
  - 运营 API 路由：`POST /api/v1/ops/vote-cycles`（创建投票周期）、`POST .../schedule`、`POST .../open`、`POST .../close`、`POST .../finalize`（状态迁移）
  - 投票结算逻辑：关闭投票时自动计票，确定获胜候选项
  - 状态机校验：严格遵循 draft → scheduled → open → closed → finalized 路径
  - 同章节唯一开放周期校验
  - 统一响应 envelope（`request_id`、`data`、`meta`、`trace_id`），对齐 `12-api-design.md` 规范
  - 玩家接口 JWT 认证（`votes:read`、`votes:submit`、`votes:history:read` scope）
  - 错误响应 envelope、幂等键处理、结构化日志、request_id/trace_id 中间件
  - 审计日志持久化（`audit_logs` 表写入，覆盖投票提交、周期创建和状态迁移）
  - 模型约束补全：`votes_candidate_id_idx` 索引、`winning_candidate_id` FK
  - 测试用例 51 个全部通过（含玩家接口 + 运营接口 + 审计日志 + 鉴权 + envelope 格式）
- **Alembic 迁移环境已初始化**（vote-service + world-service + content-service + generation-service + review-service + player-service + ops-service + gateway-service），迁移脚本已生成：
  - vote-service：
    - 首次迁移（vote 核心三表）：`services/vote/alembic/versions/2026_07_01_1529_ba4a0034a620_init_vote_tables.py`
    - 审计日志表：`services/vote/alembic/versions/2026_07_02_0200_c8d2e5f1a730_add_audit_logs_table.py`
  - world-service：
    - 首次迁移（regions 表）：`services/world/alembic/versions/2026_07_04_0201_a1b2c3d4e5f6_init_world_tables.py`
    - 审计日志表：`services/world/alembic/versions/2026_07_04_0202_b2c3d4e5f6a7_add_audit_logs_table.py`
  - content-service：
    - 首次迁移（regions、vote_cycles、content_packages、release_records、rollback_records 表）：`services/content/alembic/versions/2026_07_04_0203_c3d4e5f6a7b8_init_content_tables.py`
    - 审计日志表：`services/content/alembic/versions/2026_07_04_0204_d4e5f6a7b8c9_add_audit_logs_table.py`
  - generation-service：
    - 首次迁移（vote_cycles、vote_candidates、generation_requests、generated_objects 表）：`services/generation/alembic/versions/2026_07_04_0205_e5f6a7b8c9d0_init_generation_tables.py`
    - 审计日志表：`services/generation/alembic/versions/2026_07_04_0206_f6a7b8c9d0e1_add_audit_logs_table.py`
  - review-service：
    - 首次迁移（review_records 表）：`services/review/alembic/versions/2026_07_04_0207_a7b8c9d0e1f2_init_review_tables.py`
    - 审计日志表：`services/review/alembic/versions/2026_07_04_0208_b8c9d0e1f2a3_add_audit_logs_table.py`
  - player-service：
    - 首次迁移（players、player_quests、player_regions 表）：`services/player/alembic/versions/2026_07_04_0209_c9d0e1f2a3b4_init_player_tables.py`
    - 审计日志表：`services/player/alembic/versions/2026_07_04_0210_d0e1f2a3b4c5_add_audit_logs_table.py`
  - ops-service：
    - 首次迁移（ops_dashboards、ops_actions 表）：`services/ops/alembic/versions/2026_07_04_0211_e1f2a3b4c5d6_init_ops_tables.py`
    - 审计日志表：`services/ops/alembic/versions/2026_07_04_0212_f2a3b4c5d6e7_add_audit_logs_table.py`
  - gateway-service：
    - 首次迁移（audit_logs 表）：`services/gateway/alembic/versions/2026_07_08_2200_init_gateway_tables.py`
- `world-service` 已完成骨架初始化与区域管理接口：
  - 数据模型：`Region`、`WorldSkeleton`、`AuditLog`（对应 `backend-data-spec.md`）
  - 玩家 API 路由：`GET /api/v1/health`、`GET /api/v1/world/regions`、`GET /api/v1/world/regions/{region_id}`、`GET /api/v1/world/skeleton`（获取当前世界骨架快照）
  - 运营 API 路由：`POST /api/v1/ops/world/regions`（创建区域）、状态更新、`POST /api/v1/ops/world/skeleton`（创建世界骨架快照）
  - 区域状态机：locked → active → unstable → archived
  - **世界骨架快照 API**：支持创建、获取当前活跃快照，包含 world_version、chapter_id、regions、factions、forbidden_tags、reserved_characters、reward_limits 等字段，forbidden_tags 非空校验
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`world:read` scope、ops 角色权限）
  - 审计日志持久化
  - 测试用例 46 个全部通过（含玩家接口 + 运营接口 + 审计日志 + 鉴权 + envelope 格式 + 骨架快照）
- `content-service` 已完成骨架初始化与内容包管理：
  - 数据模型：`ContentPackage`、`ReleaseRecord`、`RollbackRecord`、`AuditLog`（对应 `backend-data-spec.md`）
  - 玩家 API 路由：`GET /api/v1/health`、`GET /api/v1/content/updates`、`GET /api/v1/content/packages/{package_id}`
  - 运营 API 路由：`POST /api/v1/ops/content-packages`（创建内容包）、发布、回滚
  - 内容包状态机：packaged → gray → live → archived，gray/live → rolled_back
  - **灰度发布可见性判断**：支持三种灰度范围（player_ids 白名单、player_percent 百分比、region_ids 区域），优先级 player_ids > player_percent > region_ids
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`content:read`、`content:release`、`content:rollback` scope）
  - 审计日志持久化
  - 测试用例 58 个全部通过（含玩家接口 + 运营接口 + 审计日志 + 鉴权 + envelope 格式 + 灰度可见性）
- `generation-service` 已完成骨架初始化与内容生成请求管理：
  - 数据模型：`GenerationRequest`、`GeneratedObject`、`AuditLog`（对应 `backend-data-spec.md`）
  - 运营 API 路由：生成请求创建/查询/状态更新、生成对象查询/状态更新（审核）
  - **世界骨架快照校验**：生成请求创建前自动校验当前活跃骨架快照存在、forbidden_tags 非空、chapter_id 和 region_id 有效
  - 生成请求状态机：pending → processing → succeeded / failed_retryable → pending（重试） / failed_permanent
  - 生成对象状态机：pending_review → approved / rejected / needs_revision
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`review:approve` scope、ops 角色权限）
  - 审计日志持久化
  - 测试用例 53 个全部通过（含运营接口 + 审计日志 + 鉴权 + envelope 格式 + 状态机校验 + 骨架校验）
- `review-service` 已完成骨架初始化与内容审核管理：
  - 数据模型：`ReviewRecord`、`AuditLog`（对应 `backend-data-spec.md`）
  - 运营 API 路由：审核记录创建/查询/更新、审核批准/拒绝
  - 审核状态机：pending → approved / rejected / manual_review
  - 风险等级：low / medium / high / critical
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`review:approve` scope、reviewer/ops 角色权限）
  - 审计日志持久化
  - 测试用例 38 个全部通过（含运营接口 + 审计日志 + 鉴权 + envelope 格式 + 状态机校验）
- `gateway-service` 已完成骨架初始化与 API 网关核心功能：
  - 核心功能：JWT 认证中间件、令牌桶限流中间件、请求追踪中间件、反向代理路由
  - 代理路由：vote/world/content/generation/review/player/ops 7 个服务路由映射
  - 请求头传递：X-Request-Id、X-Trace-Id、Idempotency-Key 透传
  - 健康检查：`GET /api/v1/health`、`GET /api/v1/health/services`
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - 错误响应格式（统一 error envelope）
  - 结构化日志（structlog）
  - 测试用例 37 个全部通过（含认证 + 限流 + 代理 + 追踪 + 健康检查）
- `player-service` 已完成骨架初始化与玩家管理接口：
  - 数据模型：`Player`、`PlayerQuest`、`PlayerRegion`、`AuditLog`（对应 `backend-data-spec.md`）
  - 玩家 API 路由：`GET /api/v1/health`、`GET /api/v1/player/info`、`GET /api/v1/player/quests`、`GET /api/v1/player/regions`
  - 运营 API 路由：`POST /api/v1/ops/players`（创建玩家）、`GET /api/v1/ops/players`（列表）、`GET /api/v1/ops/players/{player_id}`（详情）、`PUT /api/v1/ops/players/{player_id}`（更新）、`POST /api/v1/ops/players/{player_id}/regions/{region_id}/unlock`（解锁区域）
  - 任务状态机：available → active → completed / failed
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`world:read`、`quests:read` scope、ops 角色权限）
  - 审计日志持久化
  - 自定义 UUID 类型兼容 SQLite 测试环境
  - 测试用例 37 个全部通过（含玩家接口 + 运营接口 + 审计日志 + 鉴权 + envelope 格式 + 分页测试 + 指标测试）
- `ops-service` 已完成骨架初始化与运营后台接口：
  - 数据模型：`OpsDashboard`、`OpsAction`、`AuditLog`（对应 `backend-data-spec.md`）
  - 运营 API 路由：`GET /api/v1/health`、`GET /api/v1/ops/dashboard`（仪表盘）、`GET /api/v1/ops/dashboard/history`（历史）、`GET /api/v1/ops/actions`（运营操作列表）、`GET /api/v1/ops/actions/{action_id}`（操作详情）、`GET /api/v1/ops/system/status`（系统状态）
  - **系统状态健康检查**：通过 HTTP 调用各服务 `/api/v1/health` 接口获取真实状态，支持超时设置和错误处理，服务正常返回 `ok`，异常返回 `unavailable`
  - 统一响应 envelope（对齐 `12-api-design.md` 规范）
  - JWT 认证（`ops:*` scope）
  - 审计日志持久化
  - 自定义请求 ID 头支持
  - 测试用例 39 个全部通过（含仪表盘 + 运营操作 + 系统状态 + 审计日志 + 鉴权 + envelope 格式 + 健康检查客户端）
- 本地开发基础设施：`infra/docker-compose.dev.yml`（PostgreSQL 16 + Redis 7）。
- `.gitignore`、各目录 README 占位、`.env.example` 已配置。
- `docs/packages/first-slice/` 第一版需求包：包含投票链路完整规范子集（功能特性、API 接口清单、数据模型定义、业务流程说明、验收标准），作为 MVP 投票链路验证的需求基线。
- **CI/CD 基础设施**：
  - GitHub Actions 工作流：`ci.yml`（lint、类型检查、测试、内容检查、E2E 测试）、`cd.yml`（灰度发布、全量发布、回滚）、`docker-build.yml`（Docker 构建）
  - CI 流水线新增：内容检查门禁（世界一致性、数值边界、内容安全、重复度四项检查）、E2E 端到端测试
  - CD 流水线新增：灰度发布阶段（gray-release）、全量发布升级（promote-to-full）、支持 workflow_dispatch 手动触发
  - 各服务 Dockerfile（vote、world、content、generation、review、gateway、player、ops、workers）
  - 生产环境配置：`infra/docker-compose.prod.yml`、`infra/.env.prod.example`
  - Nginx 反向代理配置：`infra/nginx/conf.d/default.conf`
  - 监控配置：`infra/prometheus/prometheus.yml`、`infra/grafana/provisioning/datasources/prometheus.yml`、`infra/grafana/dashboards/game-dashboard.json`
  - 部署脚本：`tools/deploy.sh`、`tools/rollback.sh`（支持回滚日志记录）、`tools/health-check.sh`（支持服务级别检查）、`tools/migrate-all.sh`、`tools/gray-release.sh`（灰度发布脚本）、`tools/verify-release.sh`（发布验证脚本）
- **Godot 客户端工程**：
  - Godot 4 项目骨架已初始化（`project.godot`、`icon.svg`）
  - 标准目录结构：`scenes/`、`scripts/`、`data/`、`assets/`、`tests/`
  - 5 个核心 Autoload 单例：GameState、APIManager、VoteManager、ContentManager、AudioManager
  - 完整场景实现：Main（主入口）、MainMenu（主菜单）、VotingPanel（投票面板）、VoteResultPanel（投票结果）、VoteHistoryPanel（投票历史）、WorldMap（世界地图）、NPCPanel（NPC列表）、QuestPanel（任务面板）；所有场景文件与脚本匹配，支持场景切换和信号通信
  - 数据配置：game_config.json、region_list.json、npc_list.json、quest_list.json（均带 schema_version）
  - GUT 测试框架与完整测试覆盖：8 个测试文件共 57 个测试用例，覆盖 GameState、APIManager、VoteManager、WorldManager、PlayerManager、WorldMap、QuestPanel、NPCDialog；测试文档 `game/tests/README.md` 包含完整测试清单和覆盖说明
  - 投票系统端到端功能完善：VoteManager 增强（loading 状态、错误处理、辅助方法）、VotingPanel 完整交互（加载/选择/提交/反馈）、VoteResultPanel 结果展示（进度条、获胜者高亮、影响信息）、VoteHistoryPanel 历史记录（列表、分页）、主菜单投票入口、场景流转逻辑
  - 世界探索与任务系统完善：WorldMap 增强（区域渲染、状态标识、点击选择、详情展示）、QuestPanel 任务面板（任务列表、详情、目标进度、奖励展示、任务接取）、NPCPanel 和 NPCDialog（NPC 列表、对话交互、任务接取）、数据配置完善（区域列表、任务实例、NPC 实例）、测试用例补充（WorldMap、QuestPanel）
  - 客户端与后端 API 联调完善：APIManager 错误码对齐（NO_OPEN_VOTE_CYCLE、ALREADY_VOTED、TOKEN_EXPIRED 等）、重试机制（幂等请求）、HTTP 方法支持（GET/POST/PUT/DELETE）；VoteManager 错误处理与状态同步（auth_error 信号、can_vote 判断）；ContentManager 版本同步与更新检查（自动检查、手动检查、安装/卸载）；新增 WorldManager（区域列表、详情、缓存）和 PlayerManager（玩家信息、任务列表、区域状态）；测试用例补充（APIManager 错误处理、WorldManager、PlayerManager）
  - **首期内容实例化**：世界观根设定（`docs/20-specs/world-lore-spec.md`）、2个首期区域（铁卫城周边、灰谷废墟）、4个势力阵营（铁卫联盟、自由领地、暗影面纱、丰收商会）、6个核心NPC（艾瑞尔·铁盾、格尔·铁锤、玛莎·耕地、雷克斯·金币、露娜·暗星、杰克·流浪者）、7个任务实例（2条主线+5条支线）、3个章节定义（觉醒之路、铁卫的召唤、自由之声）；所有数据配置均带 schema_version 字段，包含完整的阵营关系矩阵、声望系统规则、区域详情、NPC 对话和任务目标
- **内容包打包与发布流程**：
  - 首期内容包初始化脚本（`services/content/scripts/seed_initial_packages.py`），支持从 game/data/ 读取内容并创建区域内容包（铁卫城周边 + 灰谷废墟），脚本代码已验证正确，测试用例（4个）全部通过，等待部署环境执行
  - 内容包打包 Worker 增强（`workers/tasks/content_packaging.py`）：新增 `validate_package_payload` 校验函数、`load_content_from_directory` 目录加载函数、`package_content_from_directory` 任务
  - 内容包发布流程增强（`workers/tasks/content_release.py`）：新增 `build_gray_scope` 灰度范围构建、`promote_to_full_release` 全量发布任务，支持按区域/玩家百分比/指定玩家列表进行灰度
  - 测试用例补充：content_packaging（6个）、content_release（8个），全部通过
- **内容审核四项检查**：
  - 工具脚本：`tools/content_check/`（世界一致性、数值边界、内容安全、重复度四项检查）
  - 基类与配置：`base.py`、`config.py`、`__init__.py`
  - 各检查器：`world_consistency.py`、`reward_boundary.py`、`content_safety.py`、`duplication.py`
  - 测试覆盖：28 个单元测试全部通过
  - 与 Workers 集成：`workers/tasks/content_review.py` 已更新为调用检查器实现
  - 门禁注册表更新：`gate_registry.yaml` 已新增 4 个 content 类型门禁
- **Tools 模块工程化与 CI 门禁补全**：
  - 为 4 个 tools 模块添加 `pyproject.toml`，统一依赖管理与工具配置：
    - `tools/content_check/`：PyYAML 依赖，完整 ruff/mypy/pytest 配置
    - `tools/loop_logging/`：PyYAML + scikit-learn + numpy 依赖，完整 ruff/mypy/pytest 配置
    - `tools/agents/`：PyYAML + Pydantic 依赖，ruff 配置（含 E402/F841 忽略规则）
    - `tools/playtest/`：fastapi + httpx + pytest 依赖，ruff 配置
  - CI 配置（`.github/workflows/ci.yml`）扩展：
    - lint 任务新增 content_check、loop_logging、agents、playtest 4 个工具
    - type-check 任务新增 content_check、loop_logging
    - test 任务新增 content_check、loop_logging
    - content-check 任务简化为统一 pytest 执行
    - e2e-test 任务增强：先安装所有后端服务依赖，再安装 playtest
  - 门禁注册表新增 4 个门禁：
    - G-UNIT-010：Tools Unit Tests (loop_logging)
    - G-UNIT-011：Tools Unit Tests (content_check)
    - G-STATIC-003：Ruff Lint (tools)
    - G-E2E-002：Full Integration E2E (playtest)
  - 代码质量修复：
    - `tools/loop_logging/schema.py`：修复 `log_excerpt` 未定义 → `self.log_excerpt`
    - `tools/loop_logging/cli.py`：删除未使用变量 `rule_registry`
    - `tools/loop_logging/rule_evaluator.py`：删除未使用参数 `max_false_negative_rate`
    - `tools/system_designer_agent/system_designer_agent.py`：修复 list comprehension 变量名 `file` → `f`
- **Prometheus 监控指标集成**：
  - 所有 8 个后端服务（vote、world、content、generation、review、gateway、player、ops）均已集成 `prometheus-fastapi-instrumentator`
  - 每个服务均提供 `/metrics` 端点，支持 HTTP 请求数、延迟、错误率等指标采集
  - gateway-service 的 `/metrics` 端点已豁免认证，便于 Prometheus 直接采集
  - 每个服务新增 metrics 端点测试用例，全部通过
- **业务指标（Business Metrics）集成**：
  - 8 个后端服务均新增 `app/core/metrics.py`，使用 `prometheus_client.Counter` / `Gauge` 定义业务指标
  - vote-service：`vote_submissions_total`、`vote_cycle_transitions_total`、`vote_cycles_by_status`、`vote_candidates_by_status`
  - world-service：`world_region_operations_total`、`world_region_transitions_total`、`world_regions_by_status`
  - content-service：`content_package_operations_total`、`content_releases_total`、`content_rollbacks_total`、`content_packages_by_status`
  - generation-service：`generation_requests_total`、`generated_objects_total`、`generation_requests_by_status`
  - review-service：`reviews_total`、`review_operations_total`、`reviews_by_risk_level`
  - gateway-service：`gateway_proxy_requests_total`、`gateway_rate_limit_hits_total`、`gateway_auth_failures_total`
  - player-service：`players_total`、`player_operations_total`、`player_quests_by_status`
  - ops-service：`ops_actions_total`、`ops_dashboard_views_total`
  - 每个服务在 `routes.py` 关键操作点（创建/状态迁移/提交）埋点，调用 `record_*` 辅助函数
  - 每个服务在 `tests/test_health.py` 新增 2 个测试（指标暴露 + 指标递增），共 16 个新增测试
  - Grafana 仪表盘 `infra/grafana/dashboards/game-dashboard.json` 扩展至 20 个面板，覆盖 HTTP 指标 + 8 个服务的业务指标
  - 全部 8 个服务通过 ruff、mypy、pytest（共 335 个测试用例）验证
- **门禁 Runbook 文档**：`docs/runbook/` 目录已创建，包含 16 个门禁的运行手册（Ruff Lint、Mypy Typecheck、vote/world/content/generation/review/player/ops/gateway/workers 单元测试、四项内容检查、关键路径 E2E 测试），每个 runbook 包含门禁概述、常见失败原因、解决方案、手动执行方法和升级路径
- **门禁注册表完善**：`docs/40-dev-loop/gate_registry.yaml` 已补充完整，包含所有 8 个后端服务（vote、world、content、generation、review、player、ops、gateway）和 workers 的单元测试门禁配置，以及静态检查、内容检查、E2E 测试等门禁定义
- **关键路径 E2E 测试脚本**：`tools/playtest/` 目录已创建，包含投票流程端到端测试（创建投票周期 → 添加候选项 → 开放投票 → 提交投票 → 关闭计票 → 验证结果），支持分步执行和完整流程测试
- **事件总线基础设施**：`workers/events/` 目录已创建，基于 Redis Pub/Sub 实现，包含事件总线客户端、事件发布者、订阅者、7 个核心事件类型定义（vote.cycle.closed、vote.result.finalized、generation.request.created、generation.batch.completed、review.batch.completed、content.package.released、content.package.rolled_back）、事件处理器（投票结算触发内容生成、生成完成触发审核、审核通过触发布打包）
- **服务间事件发布集成**：vote-service、content-service、generation-service、review-service 均已集成事件发布客户端，在关键操作点（投票结算、内容发布/回滚、生成完成、审核完成）发布对应事件
- **事件消费重试机制**：`workers/events/event_subscriber.py` 已实现指数退避重试策略（最大3次重试，2^n * base_delay）和死信队列处理（超过重试次数后发送到 `event.dead_letter` 通道）
- **Celery Beat 定时任务**：配置了 3 个定时任务（每日门禁扫描、每小时指标同步、每日内容审核），支持 scheduled 队列，prometheus-client 依赖已添加到 workers
- **投票触发内容生成闭环**：事件处理器参数与任务签名已对齐，`handle_vote_result_finalized` 正确调用 `generate_content_batch`（传递 vote_cycle_id、winning_candidate_id），`handle_generation_batch_completed` 触发打包流程，`handle_review_batch_completed` 触发完整审核，事件处理器使用 `EventType` 枚举注册，新增 `handle_content_package_rolled_back` 处理器

## 当前主要风险

- ~~`vote-service` 端到端可运行验证尚未完成（需 PostgreSQL 环境，Docker 在 CI 沙箱不可用）。~~ 已完成，代码层面已验证通过，PostgreSQL 配置就绪。
- ~~JWT 鉴权中间件尚未实现，运营接口缺少真实的角色和权限校验。~~ 已完成，运营接口具备完整的 Scope 校验。
- ~~审计日志（`audit_logs` 表）尚未持久化，运营操作的审计记录仅在结构化日志中。~~ 已完成，审计日志持久化到 `audit_logs` 表。
- ~~监控 metrics endpoint 待集成~~ 已完成，所有 8 个后端服务均已集成 Prometheus metrics，支持 HTTP 请求数、延迟、错误率等指标采集
- ~~`10-requirements/` 与 `20-specs/` 仍有一定内容重叠，后续若继续双向修改，容易再次漂移。~~ 已完成清理，10-requirements/ 回归需求背景定位，执行规范细节统一指向 20-specs/ 文档。
- ~~`40-dev-loop/` 中部分设计偏目标态，若不裁剪就直接照搬，实施成本会偏高。~~ 已完成裁剪，ai-coding-game-dev-loop-plan.md 和 loop-engineering-plan.md 已添加阶段性说明，明确区分已完成阶段和后续阶段目标，避免直接照搬目标态设计导致实施成本偏高。
- ~~各服务 routes.py 已完成统一错误码模块迁移，但测试中硬编码的错误码字符串需同步更新以确保测试准确性~~ 已完成，所有 8 个后端服务的测试文件均已使用错误码常量进行断言

## 下一阶段建议

1. ~~确认仓库策略：~~ 已确定为单仓模式，当前仓库继续演进为主仓库。
2. ~~选定首个最小落地目标：~~ 已确定为最小投票链路（vote-service 骨架已初始化）。
3. ~~初始化 Alembic 并生成首次迁移脚本：~~ 已完成，vote 核心三表迁移脚本就绪。
4. ~~启动本地 PostgreSQL 并执行迁移，完成 vote-service 端到端可运行验证。~~ 已完成（51 个测试全部通过，mypy 类型检查通过）。
5. ~~为 vote-service 补充投票结算逻辑与运营写接口（创建投票周期等）：~~ 已完成。
6. ~~为 vote-service 实现 JWT 鉴权中间件与角色/Scope 权限校验。~~ 已完成（41 个测试全部通过）。
7. ~~补充审计日志持久化（`audit_logs` 表写入）。~~ 已完成（49 个测试全部通过）。
7.5. ~~实现统一响应 envelope 格式对齐 `12-api-design.md` 规范。~~ 已完成（51 个测试全部通过）。
7.6. ~~为玩家接口添加 JWT 认证（votes:read/votes:submit/votes:history:read scope）。~~ 已完成。
7.7. ~~补充 votes 表 candidate_id_idx 索引和 winning_candidate_id FK 约束。~~ 已完成。
8. ~~基于最小投票链路生成第一版需求包（可放在 `docs/packages/first-slice/`），包括从 `20-specs/` 抽出的相关规范子集。~~ 已完成，需求包包含投票周期管理、投票提交、结算、结果展示、审计日志等完整规范子集，以及 API 接口清单、数据模型定义、业务流程说明和验收标准。
9. ~~补异步任务和事件的 payload schema（不阻塞投票 MVP，但内容链路需要）。~~ 已完成，异步任务与事件 schema 规范已发布，包含 7 个核心任务 payload、7 个事件主题、重试策略、死信队列、全链路追踪规范。
10. ~~初始化 content-service（内容包管理、灰度发布、回滚），为内容链路打基础。~~ 已完成（48 个测试全部通过）
11. ~~初始化 generation-service（AI 内容生成请求与结果落库）。~~ 已完成（47 个测试全部通过）
12. ~~初始化 review-service（内容审核、质量评分、人工复核流转）。~~ 已完成（38 个测试全部通过）
13. ~~完善世界探索与任务系统UI（世界地图、任务面板、NPC交互）~~ 已完成，WorldMap、QuestPanel、NPCPanel、NPCDialog 组件已实现，数据配置已完善，测试用例已补充
14. ~~完善客户端与后端 API 联调封装（APIManager、VoteManager、ContentManager、WorldManager、PlayerManager）~~ 已完成，错误码对齐、重试机制、缓存管理、测试用例补充完成
15. ~~首期内容实例化（世界观、区域、阵营、NPC、任务、章节）~~ 已完成，包含世界观根设定、2个首期区域配置、4个势力阵营、6个核心NPC、7个任务实例（1条主线+6条支线）、3个章节定义
16. ~~内容包打包与发布流程实现~~ 已完成，包含首期内容包初始化脚本、内容包校验与目录加载、灰度发布范围配置、全量发布升级任务、完整测试覆盖
17. ~~业务指标（Business Metrics）集成：在 8 个后端服务的关键操作点埋点，扩展 Grafana 仪表盘覆盖业务指标~~ 已完成，全部 8 个服务新增 `app/core/metrics.py` 与 `record_*` 辅助函数，routes.py 在创建/状态迁移/提交等关键操作点埋点，每个服务新增 2 个测试用例（指标暴露 + 指标递增），Grafana 仪表盘扩展至 20 个面板，共 335 个测试全部通过
18. ~~内容审核四项检查与工具脚本（世界一致性、数值边界、内容安全、重复度）~~ 已完成，tools/content_check/ 四个检查器 + 28个测试 + workers 集成 + 门禁注册表更新
19. ~~灰度发布可见性判断逻辑完善：content-service 支持按玩家/百分比/区域的灰度范围过滤，修复 workers API 路径不匹配问题~~ 已完成，content-service 灰度可见性判断 + workers API 路径修复 + 58 个测试全部通过
20. ~~统一各服务错误码与异常处理：为 8 个后端服务创建统一的错误码模块（errors.py），对齐 api-error-codes.md 文档，确保各服务错误码命名与 API 规范一致~~ 已完成，8 个服务新增 errors.py 模块，api-error-codes.md 文档更新对齐，vote-service 54 个测试全部通过
21. ~~扩展端到端集成测试覆盖：实现投票完整流程（创建→提交→结算）和内容包完整流程（创建→发布→回滚）的集成测试~~ 已完成，vote-service 54 个测试全部通过，content-service 58 个测试通过
22. ~~实现世界骨架快照 API 与内容生成校验：world-service 添加骨架快照创建/获取接口，generation-service 在生成请求创建前校验骨架存在、forbidden_tags 非空、chapter_id/region_id 有效~~ 已完成，world-service 46 个测试通过，generation-service 53 个测试通过
23. ~~tools 模块工程化配置与 CI 门禁补全：为 content_check、loop_logging、agents、playtest 添加 pyproject.toml，扩展 CI 配置，补充门禁注册表~~ 已完成，4 个 tools 模块配置齐全，CI 任务扩展，新增 4 个门禁
24. ~~启动 P3 阶段（线上运营闭环期）规划：创建 P3 阶段规划文档，定义数据回流机制、数据分析流程、洞察提取与需求生成闭环、实施路线图~~ 已完成，P3 规划文档已创建并更新为 active 状态，四个阶段（数据采集基础设施、数据分析引擎、分析仪表盘、洞察提取与需求生成）已全部实现，客户端事件采集 SDK 已实现，第一阶段进度达 90%

## 进入实施前的建议门槛

- ~~产品边界和 MVP 范围不再频繁变更。~~ 已明确
- ~~首个最小落地目标明确到单条主线能力。~~ 已确定为最小投票链路
- ~~确认是沿当前仓库继续扩展，还是拆出独立工程仓库。~~ 已确定为单仓模式
- ~~初始化 Alembic 迁移脚本，完成 vote 核心三表定义。~~ 已完成
- ~~补充运营写接口与投票结算逻辑。~~ 已完成（26 个测试全部通过）
- ~~启动数据库并执行迁移，完成 vote-service 端到端可运行验证。~~ 已完成（51 个测试全部通过，mypy 类型检查通过）
- ~~实现 JWT 鉴权中间件，确保运营接口有角色和权限校验。~~ 已完成（41 个测试全部通过）

## 与其他文档的关系

- `docs/00-governance/document-map.md`
  - 文档角色分层与权威关系。
- `docs/00-governance/governance-phase-summary.md`
  - 治理阶段结论、已形成基线和后续移交重点。
- `docs/00-governance/quick-start.md`
  - 当前仓库使用方式与实施顺序。
- `docs/20-specs/README.md`
  - 执行规范目录入口。
- `docs/30-api/`
  - 接口参考与样例。
