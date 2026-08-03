# 项目状态

> 文档状态：active
> 适用阶段：当前
> 维护要求：持续维护
> 最后整理：2026-07-31（PM 每日评审）

## 目的

本文档用于维护项目级状态判断，只回答“当前处于什么阶段、已经形成了什么结论、当前阻塞是什么、下一步建议是什么”。

本文档**不再**承担按小时追加的状态流水、自动遥测堆叠或周度复盘角色。过程层材料统一下沉到 `docs/40-dev-loop/`。

## 当前阶段

- 当前阶段：M4 规模化内容生成实施期（跳过灰度阶段，直接抢跑实施）
- 当前判断：核心研发链路已完成；管理决策已明确：直接越过灰度发布阶段，全力推进 M4 实施；M4 规划期白名单五项已于 2026-07-23 全部落地，即日起 M4 进入正式实施
- 当前状态：灰度阶段已明确跳过，M4 实施正式启动；现状盘点/差距分析/工作包分解已完成，五项产出文档（模板细化/样本集/阈值预案/看板指标/运营流程草案）全部就位，按工作包顺序逐项推进。WP1 首个实施代码项（A2：`score_region` 字段口径对齐 danger_level/landmarks，修复 F1 缺陷）已于 2026-07-23 落地，场景评分维度恢复生效。2026-07-25，A3/A4/A5 提示词硬化（装备/怪物数值锚定、章节强度上限、输出格式硬化）已落地至 generation 服务 live prompt 构造函数（_build_item/monster/boss/region_prompt），生成测试 14 passed（含新增硬化落盘校验）。2026-07-26，WP2 首个代码项落地——`services/review` 的 `DuplicateDetectionRule.max_similarity` 死参数已接线为默认 0.8 生效（自相似度阈值口径），review 服务新增判定测试 14 passed，WP2 进入实施期。2026-07-26，WP3 审核效率监控首个代码批落地——`services/review` 新增 `review_duration_seconds` 耗时 Histogram（M1）、`reviews_total` 补 `review_type` 标签并修复 auto 路径全终局计数（M2）、`metrics.yaml` 标签同步（M3）、`review_rule_decisions_total` 规则归因 Counter（M4），并落 `review-efficiency-dashboard.json`（M5）与 review 告警/SLO（M6）；review 服务全量 pytest 87 passed，WP3 进入实施期；2026-07-26，WP3 收尾项落地——review 服务派生 `auto_pass_rate` / `manual_intervention_rate` / `review_p95_minutes` 并经 `GET /api/v1/review/stats` 暴露，ops 审核统计面板（`ReviewStatsResponse.review_efficiency`）与主看板模型（`DashboardMetrics.review_efficiency`）接入三项字段（auto-20260726-0856），WP3 全闭环。2026-07-26，WP5 首个代码批落地——generation 服务新增 `generate_batch` 批量入口与 `POST /api/v1/ops/generation/batch` 运营端点（失败隔离/并发上限/成本上限/可选持久化/事件发布），generation 全量 pytest 266 passed，WP5 进入实施期（auto-20260726-1029）。2026-07-27 起研发闭环进入节流/优雅结束常态——Docker/PostgreSQL/Redis/workers 运行时环境不可用，WP4 与 WP1-A1/WP2/WP5 剩余子任务共同前置阻塞，已连续多日无新代码合并；截至 2026-07-29 仍处此硬阻塞状态，M4 实施实质停滞，等待运行时环境就绪解锁（详见 `docs/40-dev-loop/daily-progress/daily-progress-2026-07-29.md`）。2026-07-30–07-31 研发循环仅触发周期性遥测收拢（auto-20260730-2253 / auto-20260731-1119），无新代码合并；运行时硬阻塞延续，M4 实施持续停滞，无解锁信号（详见 `docs/40-dev-loop/daily-progress/daily-progress-2026-07-31.md`）。

## 当前结论

### 已形成的项目级结论

- 核心研发能力已闭环：投票、世界、内容、生成、审核、玩家、运营、网关八个后端服务均已形成可运行骨架与自动化验证基础。
- 文档、门禁、运行手册和自动化归档体系已成型，研发流程具备持续维护条件。
- 项目当前的主要问题已从"何时进入灰度发布并完成真实环境验证"转变为"如何高质量推进 M4 五个工作包的逐项实施"，灰度阶段已被管理决策明确跳过。
- M4 规模化内容生成规划已于 2026-07-23 正式启动：现状盘点确认 M4 所需的 7 类生成器（NPC/任务/区域/聚落/怪物/Boss/装备）、质量评分器与 4 类自动审核规则（质量分数/内容安全/字段完整度/重复度）骨架已提前就位，M4 的主要差距集中在真实 LLM 下的质量稳定性验证、自动审核通过率调优与发布自动化，而非模板从零建设。规划全文见 `docs/10-requirements/M4-规模化内容生成规划.md`。即日起 M4 进入正式实施，按 WP1→WP5 顺序推进，"不抢跑"约束解除。

### 当前不再重复展开的内容

以下内容继续存在，但不再在本页逐条滚动展开：

- 小时级“项目就绪状态持续验证”流水
- 每次自动状态报告中的环境探测细节
- 历史里程碑完成清单的长列表
- 周报中的指标变化与偏差分析全文

如需查看这些材料，请转到 `docs/40-dev-loop/` 对应入口。

## 已确认完成的高层事项

### 研发与交付基线

- Sprint 0 至 Sprint 9 的核心研发链路已基本完成。
- M1 至 M3 相关核心能力已落地，M3 扩展能力已形成完整产品面。
- 公测准备资产已具备主体框架，包括版本管理、发布清单、公测文档、玩家反馈闭环、门禁与运维材料。

### 质量与治理基线

- 八个后端服务的自动化测试、`ruff` 与 `mypy` 校验长期维持稳定通过。
- 安全审计、Prometheus 指标、关键路径 E2E、内容审核四项检查与门禁体系已接入研发闭环。
- `docs/10-requirements/`、`docs/20-specs/`、`docs/30-api/` 与 `docs/40-dev-loop/` 的分层边界已完成一轮治理收口。

## 当前主要阻塞与风险

| 项目 | 类型 | 当前判断 | 说明 |
|------|------|----------|------|
| 运行时验证未闭环 | 交付风险 | 高 | 仍有约 15 项依赖 PostgreSQL / Redis / Docker / 客户端导出环境的验证未完成；自 2026-07-27 起已升级为硬阻塞——研发闭环因运行时不可用无新代码合并，M4 实施实质停滞，验证将在运行时就绪后内嵌推进 |
| 客户端构建验证缺失 | 交付风险 | 中 | 三平台导出验证未闭环，影响公测发布物可信度 |
| PostgreSQL 预发布迁移未实跑 | 技术风险 | 中 | Alembic 迁移链路已补齐，但仍需在预发布环境执行 |
| 数据库故障 runbook 缺口 | 运维风险 | 中 | 发布前回滚与故障应对材料还需补齐 |
| 热点文件治理待后置 | 结构风险 | 中 | `services/ops`、`services/player` 与部分客户端 UI 契约问题仍应在发布窗口后治理 |
| M4 排期需重基线 | 规划风险 | 低 | 需求迭代计划中 Sprint 10/11 名义日期（2026.12）与实际进度偏离；灰度阶段已跳过，M4 实施排期应基于当前工作包优先级独立重基线 |
| 需求迭代计划文档漂移 | 规划风险 | 中 | 需求迭代计划.md 已于 2026-07-24 重基线为"M4 实施期"、标记灰度跳过、校准 S9/S10/S11，并新增 §十五 固化 M1 验收绕过战略例外（见 auto-20260724-2245） |
| M1 验收口径被绕过 | 战略风险 | 中 | 灰度阶段经决策跳过，M1 原"灰度发布验证通过"验收口径不再成立，已作为产品战略例外正式记录（见 `需求迭代计划.md` §十五） |

## 下一阶段建议

1. 把工作重心从"完成发布闭环"切换到"M4 工作包逐项推进"，公测发布闭环后续按需补课。
2. M4 实施明确跳过灰度阶段：不再等待灰度发布决策，M4 五个工作包按优先级立即推进，真实环境验证在实施中内嵌完成。
3. 以 M4 工作包为主线推进：WP1 生成模板验收收口 → WP2 审核规则调优 → WP3 发布自动化串联 → WP4 批量生成与效率 → WP5 质量看板与运维，详见 `docs/10-requirements/M4-规模化内容生成规划.md` §四。
4. 运行时验证（PostgreSQL、Redis、Docker、workers、客户端导出）作为 M4 实施的并行前置条件推进，不再作为独立阻塞阶段。
5. 继续保留每周自动代码审查与低风险治理节奏，高风险重构按需穿插。

## 当前待办（活跃工作）

> 最近更新：2026-07-29（PM 每日评审）

- **M4 WP1 模板验收收口（进行中）**：A2（F1 修复）已落地；A3/A4/A5 提示词硬化文本（3.1/3.2/3.3/3.4）已于 2026-07-25 落地至 live prompt（14 passed，含新增硬化落盘校验），few-shot 开关因依赖 WP2 样本内容推迟；A1 双源收口迁移依赖真实运行时环境；A6 需真实 LLM 实测。
- **M4 WP2 审核规则调优（进行中）**：首个代码项已于 2026-07-26 落地——`DuplicateDetectionRule.max_similarity=0.8` 死参数已接线为单对象自相似度阈值（默认 0.8 生效），并补充 `self_similarity`/`cross_similarity` 纯函数（WP2 场景 D 跨样本接线基础）；尚未做数值调优（需真实样本回放），跨样本语料接线待运行时验证。
- **M4 WP3 审核效率监控（已完成）**：指标埋点批（M1 耗时 Histogram / M2 `reviews_total` 补 `review_type` 标签并修复 auto 路径全终局计数 / M3 `metrics.yaml` 标签同步 / M4 规则归因 Counter）已于 2026-07-26 落地，review 服务全量 pytest 87 passed；M5 审核效率看板 JSON 与 M6 review 告警/SLO 已落盘；收尾项 ops 看板三字段（auto_pass_rate / review_p95_minutes / manual_intervention_rate）已于 2026-07-26 经 auto-20260726-0856 落地——review 服务派生并经 `GET /api/v1/review/stats` 暴露，ops 审核统计面板与主看板模型（DashboardMetrics）接入三项字段，WP3 全闭环。
- **M4 WP4 发布自动化与周更节奏（进行中）**：首个代码项「自动审核通过内容自动进入发布队列（审核→打包→发布串联）」已于 2026-08-03 落地（auto-20260803-2118，销项历史缺口 W1）——review 服务 `/api/v1/ops/review/auto` 在判定 `approved` 且携带 `content_package_id` 时发布 `review.auto.approved` 事件（新增 `EventPublisher.publish_review_auto_approved`，沿用发布失败不阻断审核主流程的容错惯例）；workers 侧新增 `EventType.REVIEW_AUTO_APPROVED` / `ReviewAutoApprovedEvent` 与 `handle_review_auto_approved` 处理器并注册至 `event_handlers`，触发 `release_content_package.delay(release_mode="gray")` 入队，`risk_level` 非 `low` 时留人工确认、不自动发布；同批修复 `workers/events/handlers.py` 中标准库 logger 误用 structlog 关键字参数导致的运行期 `TypeError` 隐患。review 全量 pytest 103 passed、workers 全量 pytest 全绿。剩余条目「每周区域更新运营流程」（规划期草案已就位）与「灰度环境首次周更演练」仍依赖真实运行时与运营决策。
- **M4 WP5 批量生成能力（进行中）**：首个可执行子任务「确认批量支持程度、补齐批量入口」已于 2026-07-26 落地——`ContentGenerator.generate_batch`（失败隔离 + 并发上限 + 成本上限）、批量 schema、`POST /api/v1/ops/generation/batch` 运营端点（校验 + 成本门禁 + 可选持久化 + 事件发布）均已实现，generation 全量 pytest 266 passed（auto-20260726-1029）；WP5 进入实施期。
- **运行时验证（并行前置）**：PostgreSQL / Redis / Docker / workers / 客户端三平台导出约 15 项验证，内嵌推进，不再作为独立阻塞阶段。
- ~~**文档重基线（已完成）**：`需求迭代计划.md` 重基线为"M4 实施期"、标记灰度跳过、校准 S9/S10/S11；M1 验收绕过作为产品战略例外正式记录（§十五）。（2026-07-24，auto-20260724-2245）~~

## 状态信息分层

为避免重复维护，项目状态相关信息按以下方式分层：

- `docs/00-governance/project-status.md`
  - 维护项目级结论、阻塞、风险和下一阶段建议
- `docs/40-dev-loop/weekly-report-*.md`
  - 维护周度成果、指标变化、偏差分析和趋势判断
- `docs/40-dev-loop/auto-progress-log.md`
  - 维护自动推进过程的累计摘要、近期快照与归档入口
- `docs/40-dev-loop/auto-status-report-*.md`
  - 保留最近自动状态快照，不再作为项目级主状态页
- `docs/40-dev-loop/archives/auto-generated/`
  - 维护自动规划、执行摘要和状态快照归档，作为审计与回溯材料

## 维护原则

- 本页只保留项目级信息，不按小时追加重复验证条目。
- 同一结论只在一个主入口页完整展开，其他位置以摘要或引用回链为主。
- 若当前状态没有本质变化，应更新过程层材料，而不是继续膨胀本页正文。

## 与其他文档的关系

- `docs/00-governance/document-map.md`
  - 提供文档分层与权威关系
- `docs/00-governance/governance-phase-summary.md`
  - 提供治理阶段结论与移交重点
- `docs/00-governance/quick-start.md`
  - 提供仓库启动与执行顺序
- `docs/10-requirements/M4-规模化内容生成规划.md`
  - 提供 M4 里程碑的现状盘点、差距分析、工作包分解与验收路径
- `docs/40-dev-loop/README.md`
  - 提供研发过程材料的目录入口与阅读顺序
- `docs/40-dev-loop/weekly-report-2026-07-21.md`
  - 提供最近一轮周度分析与偏差判断
- `docs/40-dev-loop/auto-progress-log.md`
  - 提供近期自动推进快照与归档索引
- `docs/20-specs/README.md`
  - 提供执行规范层入口
- `docs/30-api/`
  - 提供接口参考与样例
