# 第一版需求包 - 最小投票链路

> 版本：v1.0.0
> 创建时间：2026-07-04
> 适用阶段：MVP 投票链路验证
> 文档状态：active

## 目的

本需求包是基于已验证的最小投票链路生成的第一版需求基线，包含投票周期管理、投票提交、投票结算和投票结果展示的完整规范子集。

本需求包用于：
- 指导后续开发团队理解 MVP 投票链路的完整功能范围
- 为测试团队提供明确的验收标准
- 作为投票链路相关功能变更的参考基线
- 为产品团队提供功能说明文档

## 适用范围

- 适用于聚焦“最小投票链路”这一专题切片的协作、沟通和交付场景。
- 适用于把分散在多个规范中的内容重新组织成专题包时快速阅读。
- 不替代 `docs/20-specs/` 与 `docs/30-api/` 的源规范。

## 当前定位

- 本文档是 `docs/packages/first-slice/` 的入口说明，用于承载专题化的规范再包装结果。
- 本目录当前作为历史保留的专题需求包目录存在，不视为新的一级权威层。
- 如本目录与源规范冲突，以 `docs/20-specs/` 和 `docs/30-api/` 为准。

## 范围

本需求包聚焦于投票链路的核心功能，不包含世界探索、任务系统、内容生成等其他模块。

## 目录结构

```
docs/packages/first-slice/
├── README.md           # 本文件，需求包说明
├── scope.md            # 需求范围界定
├── features/           # 功能特性说明
│   ├── voting-cycle.md     # 投票周期管理
│   ├── vote-submission.md  # 投票提交
│   ├── vote-counting.md    # 投票结算
│   ├── vote-results.md     # 投票结果展示
│   └── audit-logging.md    # 审计日志
├── api/                # API 接口清单
│   ├── vote-endpoints.md   # 投票相关接口清单
│   ├── auth-requirements.md # 认证与权限要求
│   └── error-codes.md      # 错误码清单
├── data/               # 数据模型定义
│   ├── vote-models.md      # 投票核心数据模型
│   ├── audit-model.md      # 审计日志模型
│   └── enums.md            # 状态枚举定义
├── workflows/          # 业务流程说明
│   ├── vote-lifecycle.md       # 投票生命周期流程
│   ├── vote-submission-flow.md # 投票提交流程
│   ├── vote-finalization-flow.md # 投票结算流程
│   └── audit-trail.md          # 审计追踪流程
└── acceptance/         # 验收标准
    ├── vote-acceptance.md     # 投票功能验收标准
    ├── api-acceptance.md      # API 接口验收标准
    └── security-acceptance.md # 安全验收标准
```

## 参考来源

本需求包基于以下核心规范文档生成：

- `docs/20-specs/product-spec.md` - 产品详细规范
- `docs/20-specs/backend-data-spec.md` - 后端与数据详细规范
- `docs/30-api/api-overview.md` - API 总览
- `docs/30-api/api-permissions.md` - API 权限矩阵
- `docs/30-api/api-error-codes.md` - API 错误码

## 使用建议

1. 需要快速理解最小投票链路时，先阅读本需求包
2. 需要确认正式约束时，回到对应的 `20-specs/` 与 `30-api/` 源文档
3. 如本目录内容更新，应同步核对源规范是否已发生变化

## 版本记录

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0.0 | 2026-07-04 | 初始版本，包含最小投票链路完整规范子集 |

## 与其他文档的关系

- `docs/20-specs/`
  - 提供本需求包所依赖的正式执行基线
- `docs/30-api/`
  - 提供接口参考、权限和错误码源文档
- `docs/00-governance/document-map.md`
  - 说明本目录在整体文档体系中的过渡定位
