# 数据视图

> 说明：本目录用于快速理解“最小投票链路”涉及的数据对象、对象关系和状态阅读索引；正式字段、约束、索引和状态机以 `docs/20-specs/backend-data-spec.md` 为准。

## 本目录看什么

- `vote-models.md`：投票周期、候选项和投票记录的职责与关系
- `audit-model.md`：审计记录在投票链路中的作用与追踪价值
- `enums.md`：最常用状态组的阅读索引

## 建议阅读顺序

1. 先看 `vote-models.md`，理解最小链路有哪些核心对象
2. 再看 `enums.md`，了解这些对象大致会经历哪些状态
3. 最后看 `audit-model.md`，补齐追踪、排障和审计视角

## 不在这里维护什么

- 不重复维护字段表、SQL CHECK 约束、索引和外键细节
- 不重复维护完整状态机矩阵
- 不把本目录当成数据库设计权威来源

## 源文档入口

- 后端与数据规范：`docs/20-specs/backend-data-spec.md`
- 产品规范：`docs/20-specs/product-spec.md`
