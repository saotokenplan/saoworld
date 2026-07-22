# 验收视图

> 说明：本目录用于快速理解“最小投票链路”在产品、接口和安全视角下需要达到的验收目标；正式测试门禁、错误码、性能要求和实现细节以 `docs/20-specs/`、`docs/30-api/` 与测试规范为准。

## 本目录看什么

- `vote-acceptance.md`：投票链路在产品视角下的核心通过标准
- `api-acceptance.md`：接口视角的联调与验收重点
- `security-acceptance.md`：认证、幂等、风控与审计的验收重点

## 建议阅读顺序

1. 先看 `vote-acceptance.md`，理解整条链路至少要通过什么
2. 再看 `api-acceptance.md`，确认接口层的验收关注点
3. 最后看 `security-acceptance.md`，补齐安全与风控门槛

## 本目录的写法约束

- 以验收主题、通过标准和测试分组为主
- 不重复维护完整测试用例清单和第二套状态机文档
- 如需精确门禁和自动化测试要求，回到测试规范与源规范

## 源文档入口

- 产品规范：`docs/20-specs/product-spec.md`
- 后端与数据规范：`docs/20-specs/backend-data-spec.md`
- API 参考：`docs/30-api/`
- 测试规范：`.trae/rules/41-testing.md`
