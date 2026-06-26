# 文档目录规范

## 目的

本文档用于统一 `docs/` 目录的分层方式、命名方式、归档原则和新增文档的落位规则，避免文档长期演进后再次出现“同层混放、入口分散、引用漂移”的问题。

## 适用范围

- 本规范适用于当前仓库下的全部 `docs/` 文档。
- `.trae/skills/` 中如引用 `docs/` 路径，也应遵循本规范中的目录结构。

## 目录设计原则

- `docs/` 根目录只保留总入口文件 `README.md`。
- 其余文档统一进入按主题划分的一级分类目录，不再把治理文档、接口文档和专题文档直接放在 `docs/` 根层。
- 一级分类目录统一使用：
  - 两位数字前缀
  - 英文小写
  - 短横线连接
- 数字前缀用于稳定排序和扩展预留，推荐按 `00`、`10`、`20`、`30` 递增。

## 标准目录结构

```text
docs/
├── README.md
├── 00-governance/
│   ├── document-directory-spec.md
│   ├── document-change-process.md
│   ├── document-review-checklist.md
│   ├── document-map.md
│   ├── project-status.md
│   ├── quick-start.md
│   └── spec-skill-mapping.md
├── 10-requirements/
├── 20-specs/
├── 30-api/
├── 40-dev-loop/
└── 50-research/
```

## 一级目录职责

### `00-governance/`

- 放置文档治理、项目状态、使用入口、映射关系等“帮助理解文档体系本身”的文档。
- 典型文档：
  - `document-directory-spec.md`
  - `document-change-process.md`
  - `document-review-checklist.md`
  - `document-map.md`
  - `project-status.md`
  - `quick-start.md`
  - `spec-skill-mapping.md`

### `10-requirements/`

- 放置需求背景、产品讨论、方案草案和立项语义文档。
- 这些文档用于回答“为什么做”“希望做成什么”。
- 若与 `20-specs/` 冲突，以 `20-specs/` 为准。

### `20-specs/`

- 放置执行规范、实施约束、验收基线和工程协作标准。
- 这些文档用于回答“按什么约束落地”“什么算完成”。
- 这是后续拆任务、建仓库、写代码和接入 CI 的首要基线目录。

### `30-api/`

- 放置接口总览、权限矩阵、错误码、请求响应样例等接口参考文档。
- 该目录承担实施索引角色，不替代 `20-specs/` 中的后端与数据规范。

### `40-dev-loop/`

- 放置 AI Coding、Loop Engineering、门禁、日志 schema、Issue 模板等研发闭环文档。
- 这些文档指导流程治理和持续改进，但不单独替代执行规范。

### `50-research/`

- 放置技术选型、方案比较和历史决策依据。
- 这些文档保留为归档参考，不直接承担实施约束。

## 文件命名规则

- 目录名统一使用英文小写和短横线。
- 文件名优先沿用现有稳定名称；若无历史兼容压力，优先使用英文小写和短横线。
- 中文文件名允许保留，但不建议新增过多不同风格的混合命名。
- 同一目录内不同时使用“主题前缀 + 无前缀”的两套风格，避免检索混乱。

## README 规则

- `docs/README.md` 作为整个文档体系唯一总入口，必须长期保留在 `docs/` 根目录。
- 当某个一级目录下文档数量较多且存在阅读顺序要求时，可在该目录下增加局部 `README.md`。
- 当前 `20-specs/README.md` 继续保留，作为执行规范入口。

## 新增文档落位规则

- 新文档创建前，先判断它属于哪一层：
  - 治理与入口 -> `00-governance/`
  - 需求与方案 -> `10-requirements/`
  - 执行规范 -> `20-specs/`
  - 接口参考 -> `30-api/`
  - 研发闭环 -> `40-dev-loop/`
  - 调研归档 -> `50-research/`
- 如果一个文档同时覆盖多层内容，应优先拆分，而不是放在模糊目录中。
- 不再在 `docs/` 根目录直接新增专题文档。

## 引用规则

- 文档中的路径引用应使用迁移后的规范路径，例如：
  - `docs/20-specs/product-spec.md`
  - `docs/00-governance/project-status.md`
  - `docs/30-api/api-overview.md`
- `.trae/skills/` 中的“规范来源”也应同步引用规范化后的路径。
- 目录迁移后，旧路径不再作为长期兼容路径保留。

## 维护规则

- 目录结构调整时，先更新本规范，再执行迁移。
- 批量迁移后，必须同步更新：
  - `docs/README.md`
  - `README.md`
  - `docs/00-governance/document-map.md`
  - `docs/00-governance/project-status.md`
  - `docs/00-governance/quick-start.md`
  - `docs/00-governance/spec-skill-mapping.md`
  - `.trae/skills/` 中的引用路径
- 新增 API 文档时，应优先进入 `30-api/`，避免再次散落到 `docs/` 根层。

## 当前采用的目录规范

当前仓库从本次整理开始，正式采用以下目录规范：

1. `docs/` 根目录只保留 `README.md`
2. 治理文档统一进入 `docs/00-governance/`
3. 需求文档统一进入 `docs/10-requirements/`
4. 执行规范统一进入 `docs/20-specs/`
5. 接口参考统一进入 `docs/30-api/`
6. 研发闭环统一进入 `docs/40-dev-loop/`
7. 调研资料统一进入 `docs/50-research/`
