# 52 - 文档维护规则

> 适用角色：全员
> 本文件定义 docs/ 目录的分层结构、文档模板、维护更新要求。

---

## docs/ 六层文档结构

```
docs/
├── 00-governance/    # 文档治理、项目状态、快速开始
├── 10-requirements/  # 需求背景、PRD、功能设计、技术方案
├── 20-specs/         # 执行规范（最高权威）
├── 30-api/           # 接口总览、OpenAPI、权限、错误码
├── 40-dev-loop/      # AI Coding流程、门禁体系、日志schema
└── 50-research/      # 技术选型、方案比较、历史决策
```

### 各层定位

| 层级 | 定位 | 权威度 |
|------|------|--------|
| 00-governance | 文档治理规则、项目状态、阅读导航 | 治理层 |
| 10-requirements | 需求背景、方案讨论、立项上下文 | 背景层 |
| **20-specs** | **执行规范、实施约束、验收基线** | **最高（执行基线）** |
| 30-api | 接口参考索引、权限矩阵、错误码 | 接口参考 |
| 40-dev-loop | 研发治理、门禁、AI Coding 闭环 | 流程层 |
| 50-research | 技术选型依据、历史决策背景 | 参考层 |

### 权威优先级

当文档内容冲突时，按以下优先级执行：

```
20-specs/ > 本目录规则(.trae/rules/) > 30-api/ > 40-dev-loop/ > 00-governance/ > 10-requirements/ > 50-research/
```

进入工程实施阶段后，统一以 `docs/20-specs/` 为执行基线。

---

## 文档模板要求

### 所有 Markdown 文档必须包含的头部元信息

每个规范文档顶部必须包含：

```markdown
# 文档标题

> 文档状态：active（或 draft/deprecated）
> 适用阶段：当前（或具体阶段）
> 维护要求：持续维护
```

### 每个规范文档必须包含的章节

1. **适用范围** - 说明文档覆盖什么场景、不覆盖什么
2. **当前定位** - 说明本文档回答什么问题、不回答什么问题、与其他文档冲突时以谁为准
3. **核心内容** - 正文
4. **与其他文档的关系** - 列出上下游关联文档，说明本文档在整个体系中的位置

---

## 文档维护更新要求

### 修改规范文档后必须同步检查

修改 `20-specs/` 或其他核心文档后，必须检查以下文件是否需要同步更新：

- [ ] [docs/README.md](file:///docs/README.md) - 目录导航是否需要更新
- [ ] [docs/00-governance/document-map.md](file:///docs/00-governance/document-map.md) - 文档映射关系是否需要更新
- [ ] [docs/00-governance/project-status.md](file:///docs/00-governance/project-status.md) - 项目状态是否需要更新
- [ ] [docs/00-governance/spec-skill-mapping.md](file:///docs/00-governance/spec-skill-mapping.md) - spec 与 skill 的映射是否需要更新
- [ ] `.trae/rules/` 下的对应规则文件 - 如果规范变更涉及工程规则，必须同步更新规则
- [ ] `.trae/skills/` 下的对应 SKILL.md - 如果规范变更涉及技能引用源，必须同步更新

### 文档状态变更规则

- 新增文档初始状态为 `draft`
- 经过评审通过后更新为 `active`
- 被新文档替代后标记为 `deprecated`，并在头部说明替代文档
- 禁止直接删除有效文档，应使用 deprecated 状态标记

---

## 文档变更原则

1. **规范变更优先于实现提交**：如果代码改动依赖规范变更，先提交规范变更，再提交代码实现
2. **保持单一真实来源**：同一规则只在一处定义，避免多处重复导致不一致
3. **双向同步禁止**：不要同时双向修改 10-requirements 和 20-specs，以 20-specs 为准后可以回写背景但不要双向演进
4. **最小必要修改**：修改文档时保持聚焦，一次提交只改一个清晰主题（与代码提交要求一致）

---

## .trae/ 目录维护

.trae/ 目录包含 IDE 配置和 AI Agent 使用的技能与规则：

```
.trae/
├── rules/           # 项目工程规则（本目录）
│   ├── README.md
│   ├── 00-project-overview.md
│   ├── ...
│   └── 52-documentation.md
└── skills/          # AI Agent 技能定义
    ├── README.md
    ├── backend-service-builder/
    ├── content-review-gate/
    ├── godot-gameplay-implementer/
    ├── loop-gate-optimizer/
    ├── qa-acceptance-runner/
    ├── release-package-operator/
    ├── requirement-package-builder/
    ├── system-design-package-builder/
    └── world-content-generator/
```

### 规则文件维护

- `.trae/rules/` 下的规则文件必须与 `docs/20-specs/` 保持一致
- 规范变更涉及工程约束时，必须同步更新对应规则文件
- 规则文件命名使用数字前缀排序，便于按主题查找

### Skill 文件维护

- 每个 SKILL.md 必须声明对应的规范来源（spec 来源）
- Skill 属于执行层工具，不替代规范层
- 修改 spec 后需要检查对应 Skill 是否需要更新

---

## 相关规则

- 项目概览 → [00-project-overview.md](./00-project-overview.md)
- Git 提交规范 → [40-git-workflow.md](./40-git-workflow.md)
