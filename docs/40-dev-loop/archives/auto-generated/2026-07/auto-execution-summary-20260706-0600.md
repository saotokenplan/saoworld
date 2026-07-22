# 执行摘要：预留错误码 TOKEN_EXPIRED 落地

## 任务标识
- **task_id**: auto-20260706-0600
- **工作分支**: auto/auto-20260706-0600
- **执行时间**: 2026-07-06 06:00

## 本轮完成的工作清单

1. **OpenAPI 草案更新**：
   - 在 `GenericErrorCode` 枚举中添加 `TOKEN_EXPIRED` 错误码
   - 创建 `TokenExpiredErrorResponse` Schema 特化类型，用于 401 Token 过期场景

2. **API 错误码文档更新**：
   - 将 `TOKEN_EXPIRED` 从"预留"表移动到"已落地"表
   - 更新对应 Schema 为 `TokenExpiredErrorResponse`
   - 清理预留错误码表（当前无预留错误码）

3. **服务端错误码同步更新**：
   - 为所有 8 个后端服务（vote、world、content、generation、review、player、ops、gateway）添加 `TOKEN_EXPIRED` 错误码常量

4. **项目状态文档更新**：
   - 更新预留错误码落地状态描述，包含 `TOKEN_EXPIRED`

## 修改的文件清单

| 文件路径 | 修改类型 | 说明 |
|---|---|---|
| `docs/30-api/openapi-v1-draft.yaml` | 修改 | 添加 `TOKEN_EXPIRED` 到 GenericErrorCode 枚举，新增 `TokenExpiredErrorResponse` Schema |
| `docs/30-api/api-error-codes.md` | 修改 | 将 `TOKEN_EXPIRED` 从预留移到已落地，清理预留表 |
| `docs/00-governance/project-status.md` | 修改 | 更新预留错误码落地状态描述 |
| `services/vote/app/core/errors.py` | 修改 | 添加 `TOKEN_EXPIRED` 错误码常量 |
| `services/world/app/core/errors.py` | 修改 | 添加 `TOKEN_EXPIRED` 错误码常量 |
| `services/content/app/core/errors.py` | 修改 | 添加 `TOKEN_EXPIRED` 错误码常量 |
| `services/generation/app/core/errors.py` | 修改 | 添加 `TOKEN_EXPIRED` 错误码常量 |
| `services/review/app/core/errors.py` | 修改 | 添加 `TOKEN_EXPIRED` 错误码常量 |
| `services/player/app/core/errors.py` | 修改 | 添加 `TOKEN_EXPIRED` 错误码常量 |
| `services/ops/app/core/errors.py` | 修改 | 添加 `TOKEN_EXPIRED` 错误码常量 |
| `services/gateway/app/core/errors.py` | 修改 | 添加 `TOKEN_EXPIRED` 错误码常量 |
| `docs/40-dev-loop/auto-plan-20260706-0600.md` | 修改 | 任务状态更新为"已完成" |

## 验证结果

- vote-service 54 个测试用例全部通过
- OpenAPI 草案与服务端实现对齐
- 所有错误码定义一致

## 遗留问题与下一步建议

- 当前无遗留问题
- `TOKEN_EXPIRED` 错误码已就绪，可在接入 Refresh Token 机制时直接使用
- 建议后续在网关层实现 Token 过期检测逻辑，返回 `TOKEN_EXPIRED` 错误码

## 合并结果

待执行。