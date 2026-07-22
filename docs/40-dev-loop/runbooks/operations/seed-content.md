# Runbook: 首期内容包初始化

> operation_id: OP-CONTENT-001
> operation_name: Seed Initial Content Packages
> operation_type: content
> owner: World Agent

## 1. 操作概述

首期内容包初始化是在游戏上线前，将首期内容（区域、阵营、NPC、任务、章节等）从 `game/data/` 目录加载到 content-service 数据库中，创建初始内容包的操作。本 Runbook 描述首期内容包初始化的完整流程。

**操作基本信息**：
- **操作名称**：首期内容包初始化
- **操作 ID**：OP-CONTENT-001
- **操作类型**：content（内容）
- **负责人**：World Agent

**适用场景**：
- 新环境首次部署
- 数据库重置后重新初始化
- 测试环境数据刷新

**前置条件**：
- content-service 已部署并正常运行
- PostgreSQL 数据库已创建
- 数据库迁移已执行（Alembic upgrade head）
- `game/data/` 目录下内容配置文件完整
- 已确认内容配置的 schema_version

**预期耗时**：15 分钟

**风险等级**：medium（内容初始化错误会影响玩家体验，但可快速修复）

---

## 2. 操作步骤

### 2.1 初始化前检查

**步骤 1：验证内容配置文件完整性**

```bash
# 检查 data 目录结构
ls -la game/data/

# 检查各配置文件是否存在
ls game/data/regions/core_region.json
ls game/data/regions/expansion_region.json
ls game/data/factions/faction_list.json
ls game/data/npcs/npc_list.json
ls game/data/quests/quest_list.json
ls game/data/chapters/chapter_list.json
```

**检查项**：
- [ ] 区域配置文件存在（至少 2 个：核心区域 + 扩展区域）
- [ ] 阵营配置文件存在
- [ ] NPC 配置文件存在
- [ ] 任务配置文件存在
- [ ] 章节配置文件存在
- [ ] 所有文件都有 `schema_version` 字段

**步骤 2：验证内容配置格式**

```bash
# 检查 JSON 格式是否正确
python -c "import json; json.load(open('game/data/regions/core_region.json'))"
python -c "import json; json.load(open('game/data/regions/expansion_region.json'))"
python -c "import json; json.load(open('game/data/factions/faction_list.json'))"
python -c "import json; json.load(open('game/data/npcs/npc_list.json'))"
python -c "import json; json.load(open('game/data/quests/quest_list.json'))"
python -c "import json; json.load(open('game/data/chapters/chapter_list.json'))"
```

**检查项**：
- [ ] 所有 JSON 文件格式正确
- [ ] 关键字段存在（region_id, name, description 等）
- [ ] ID 命名符合规范（region_, npc_, quest_ 等前缀）

**步骤 3：检查数据库状态**

```bash
# 检查 content-service 健康状态
curl -X GET "http://content-service:8003/api/v1/health"

# 检查数据库连接
# 查看 content-service 日志
```

**检查项**：
- [ ] content-service 状态正常
- [ ] 数据库连接正常
- [ ] 内容包表为空（首次初始化）

**步骤 4：备份（如非首次）**

如果数据库中已有内容（非首次初始化）：
```bash
# 备份 content_packages 表
pg_dump -h <host> -U <user> -d <database> -t content_packages -F c -f content_packages_backup_$(date +%Y%m%d).dump
```

---

### 2.2 执行初始化

**步骤 5：运行初始化脚本**

```bash
# 进入 content-service 目录
cd services/content

# 运行初始化脚本
python scripts/seed_initial_packages.py
```

**脚本功能说明**：
1. 读取 `game/data/` 下的所有内容配置
2. 验证内容格式和 schema_version
3. 创建区域内容包（核心区域 + 扩展区域）
4. 设置内容包状态为 `packaged`
5. 记录初始化审计日志

**步骤 6：验证初始化结果**

```bash
# 查看内容包列表
curl -X GET "http://content-service:8003/api/v1/ops/content-packages" \
  -H "Authorization: Bearer $TOKEN"

# 查看每个内容包详情
curl -X GET "http://content-service:8003/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**验证项**：
- [ ] 内容包数量正确（首期至少 2 个：铁卫城周边 + 灰谷废墟）
- [ ] 内容包状态均为 `packaged`
- [ ] 内容包 payload 数据完整
- [ ] schema_version 正确
- [ ] region_id / chapter_id 关联正确

**步骤 7：验证内容数据完整性**

```python
# 抽查数据完整性
# 1. 检查区域配置
# 2. 检查阵营关系矩阵
# 3. 检查 NPC 所属阵营
# 4. 检查任务关联区域和 NPC
# 5. 检查章节与任务关联
```

**数据完整性检查清单**：
- [ ] 区域数量和名称正确
- [ ] 阵营数量和关系矩阵正确
- [ ] NPC 数量和所属阵营正确
- [ ] 任务数量和关联正确
- [ ] 章节定义正确
- [ ] 所有引用的 ID 都存在（无悬空引用）

---

### 2.3 初始化后验证

**步骤 8：玩家端可见性验证**

```bash
# 验证玩家接口（此时应为 packaged 状态，玩家不可见）
curl -X GET "http://content-service:8003/api/v1/content/updates" \
  -H "Authorization: Bearer $PLAYER_TOKEN" \
  -H "X-Player-Id: $PLAYER_ID"

# 预期结果：返回空列表或只有已发布的内容包
```

**验证项**：
- [ ] `packaged` 状态的内容包玩家不可见
- [ ] API 返回格式正确（统一 envelope）

**步骤 9：准备灰度发布**

初始化完成后，内容包处于 `packaged` 状态，可进行灰度发布：

```bash
# 参考灰度发布 Runbook
# docs/40-dev-loop/runbooks/operations/gray-release.md
```

**步骤 10：记录初始化结果**

初始化完成后记录：
- 初始化时间
- 操作人
- 内容包数量
- 内容包列表（ID + 名称）
- schema_version
- 初始化结果（成功/失败）
- 数据完整性检查结果

---

## 3. 回滚方案

### 3.1 触发回滚的条件

初始化后发现以下问题应考虑回滚：
- 内容配置严重错误
- 数据完整性问题（大量悬空引用）
- 世界观设定冲突
- 初始化脚本 Bug 导致数据错误

### 3.2 回滚操作步骤

```bash
# 方式1：删除已创建的内容包（推荐，packaged 状态可删除）
curl -X DELETE "http://content-service:8003/api/v1/ops/content-packages/{package_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Trace-Id: $TRACE_ID"

# 方式2：从备份恢复（如果有备份）
pg_restore -h <host> -U <user> -d <database> -c content_packages_backup_<timestamp>.dump
```

> 注意：已发布（gray/live）的内容包不能直接删除，需要先走回滚流程。

### 3.3 回滚后处理

1. 检查问题原因
2. 修复内容配置或脚本
3. 重新执行初始化
4. 验证修复结果

---

## 4. 常见问题与解决方案

### 4.1 初始化脚本执行失败

**现象**：脚本报错退出。

**可能原因**：
1. 数据库连接失败
2. 配置文件格式错误
3. 缺少必填字段
4. ID 冲突

**解决方案**：
```bash
# 1. 查看错误日志
# 脚本输出的错误信息

# 2. 检查数据库连接
python -c "from app.core.db import engine; print('OK')"

# 3. 验证配置文件
python -c "
import json
data = json.load(open('game/data/regions/core_region.json'))
assert 'region_id' in data
assert 'name' in data
assert 'schema_version' in data
print('OK')
"
```

### 4.2 内容包创建了但数据不完整

**现象**：内容包存在，但 payload 中缺少部分数据。

**可能原因**：
1. 配置文件中部分数据缺失
2. 脚本加载逻辑有 Bug
3. 某些引用 ID 不存在被跳过

**解决方案**：
```bash
# 1. 检查配置文件完整性
# 对比预期和实际的 NPC/任务数量

# 2. 查看脚本日志
# 确认哪些数据被跳过，原因是什么

# 3. 修复后重新初始化
# 先删除有问题的内容包，再重新运行脚本
```

### 4.3 内容包状态错误

**现象**：内容包状态不是预期的 `packaged`。

**可能原因**：
1. 初始化脚本 Bug
2. 有其他流程在同时操作
3. 之前的初始化数据未清理干净

**解决方案**：
```bash
# 1. 查看内容包状态历史
# 查询审计日志

# 2. 如果是 packaged 之前的状态，可手动推进
# 如果是之后的状态，需要先回滚

# 3. 清理后重新初始化
```

---

## 5. 相关链接

- 初始化脚本：`services/content/scripts/seed_initial_packages.py`
- 内容配置目录：`game/data/`
- 灰度发布 Runbook：`gray-release.md`
- 内容服务 README：`services/content/README.md`
- 世界观设定：`docs/20-specs/world-lore-spec.md`
- 内容生成规范：`docs/20-specs/content-generation-spec.md`
