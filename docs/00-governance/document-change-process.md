# 文档变更流程

## 目的

本文档用于约束后续文档的新增、修改、迁移、重命名和删除流程，确保目录结构、引用路径、入口文档和提交记录始终保持一致，避免文档体系在持续迭代中再次失序。

## 适用范围

- 适用于 `docs/` 目录下的全部文档和结构调整。
- 适用于 `.trae/skills/` 中引用 `docs/` 路径的同步修改。

## 基本原则

- 先判断文档职责，再决定落位目录。
- 先更新规范，再执行结构性变更。
- 先同步引用，再结束变更。
- 一个提交只表达一个清晰主题，不把无关文档改动混在一起。

## 变更类型

### 新增

- 新建一份此前不存在的文档。
- 例如新增接口样例、治理说明、OpenAPI 草案。

### 修订

- 在不改变文件路径的前提下更新已有内容。
- 例如补充章节、修正文案、更新说明。

### 迁移

- 把已有文档移动到新的目录层级。
- 例如从旧目录迁移到新的分层目录。

### 重命名

- 改变文件名但保留文档主题不变。
- 例如从临时命名调整为稳定命名。

### 删除

- 移除不再维护或被替代的文档。
- 删除前必须确认替代关系和引用清理方案。

## 新增流程

1. 判断文档属于哪一层：
   - `00-governance/`
   - `10-requirements/`
   - `20-specs/`
   - `30-api/`
   - `40-dev-loop/`
   - `50-research/`
2. 检查现有文档中是否已有同主题内容，避免重复造文档。
3. 确定文件名，优先使用稳定、可复用、可扩展的命名。
4. 创建文档并写清：
   - 目的
   - 当前定位
   - 与其他规范的关系
5. 如该文档是入口型或参考型文档，更新：
   - `docs/README.md`
   - 必要时更新 `docs/00-governance/document-map.md`
6. 按 Git 提交规范单独提交。

## 修订流程

1. 先确认本次修订属于：
   - 内容补充
   - 规则更新
   - 过期信息修正
   - 路径修复
2. 判断是否会影响其他文档：
   - 入口文档
   - 映射文档
   - `.trae/skills/`
3. 若影响范围跨多个文档，优先以“同一主题”批量修订。
4. 修订完成后做一次引用扫描，确认没有留下过期路径或旧描述。

## 迁移与重命名流程

1. 先更新：
   - `docs/00-governance/document-directory-spec.md`
   - 必要时更新 `docs/00-governance/document-map.md`
2. 再执行目录或文件迁移。
3. 迁移后必须同步更新：
   - `docs/README.md`
   - `README.md`
   - `docs/00-governance/project-status.md`
   - `docs/00-governance/quick-start.md`
   - `docs/00-governance/spec-skill-mapping.md`
   - `.trae/skills/` 中的引用路径
4. 执行一次全局扫描，确保旧路径不再残留。
5. 迁移与引用修正应尽量作为同一主题提交完成，避免中间状态长期存在。

## 删除流程

1. 先确认该文档是否被以下内容替代：
   - 新文档
   - 新目录
   - 更高权威级别的规范
2. 删除前必须清理所有入口和引用。
3. 若只是归档而非废弃，优先迁移到合适目录，而不是直接删除。
4. 删除提交信息中应说明删除原因，而不是只写“清理文件”。

## 引用同步清单

发生以下动作时，必须检查引用：

- 新增入口型文档
- 迁移目录
- 重命名文件
- 调整规范层级
- 更新 `.trae/skills/` 的规范来源

重点检查位置：

- `docs/README.md`
- `README.md`
- `docs/00-governance/document-map.md`
- `docs/00-governance/project-status.md`
- `docs/00-governance/quick-start.md`
- `docs/00-governance/spec-skill-mapping.md`
- `.trae/skills/README.md`
- `.trae/skills/*/SKILL.md`

## 提交前检查

提交前至少确认以下事项：

- 文档已放到正确目录
- 文档定位和标题与目录职责一致
- 相关入口文档已同步
- 旧路径或旧目录名未残留
- 提交信息准确概括“这一次改了什么”
- 提交未混入无关主题

## 提交规范对接

- 提交格式使用：
  - `<type>(<scope>): <summary>`
- 文档相关常用类型：
  - `docs`
- 常用 scope：
  - `governance`
  - `api`
  - `specs`
  - `requirements`
  - `dev-loop`

示例：

- `docs(governance): 新增文档变更流程`
- `docs(api): 新增投票接口样例`
- `docs(governance): 重组文档目录结构`

## 不应做的事

- 不在 `docs/` 根目录直接新增专题文档
- 不先移动目录再长期拖延引用修复
- 不把整个会话总结直接当作 commit message
- 不把多类无关文档改动混在同一次提交
- 不删除文档后保留悬空入口或失效路径

## 与其他文档的关系

- 目录分层与落位规则以 `docs/00-governance/document-directory-spec.md` 为准。
- 文档全局分层与权威关系以 `docs/00-governance/document-map.md` 为准。
- Git 提交规范以 `docs/20-specs/engineering-conventions.md` 为准。
