# 41 - 测试规范

> 适用角色：后端开发、客户端开发、QA
> 本文件定义服务端、客户端、内容三个维度的测试要求。

---

## 服务端测试规范

### 测试框架配置

- 测试框架：pytest + pytest-asyncio + httpx
- pytest 配置（pyproject.toml）：
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  asyncio_mode = "auto"
  pythonpath = ["."]
  ```

### 测试文件与函数命名

- 测试文件：`test_<module_name>.py`（如 `test_vote_flow.py`）
- 测试类（可选）：`Test<ClassName>`
- 测试函数：`test_<functionality>_<scenario>`（如 `test_submit_vote_success_when_cycle_open`）
- Fixture 定义在 `conftest.py` 中

### 测试环境

- 测试必须在独立的 `test` 环境下运行
- 可使用 aiosqlite（内存/文件 SQLite）替代 PostgreSQL 做快速单元测试
- 集成测试使用独立的测试数据库，测试后清理数据
- 测试配置通过环境变量 `VOTE_ENVIRONMENT=test` 加载

### 必须覆盖的场景

**核心接口必须有单元测试和集成测试：**
- 健康检查接口
- 投票查询接口
- 投票提交接口（包含幂等性验证）
- 投票历史接口

**业务流程必须覆盖：**
- 投票结算逻辑
- 内容发布流程
- 内容回滚流程
- 权限检查（不同Scope的访问控制）
- 错误码返回是否正确

**必须覆盖的异常场景：**
- 投票周期不存在或未开放
- 候选项不存在或已撤回
- 玩家重复投票
- 无效的玩家ID格式
- 幂等键重复提交

### 测试代码约定

- 测试使用 Arrange-Act-Assert (AAA) 模式
- 每个测试只测一个场景
- 测试数据尽量通过 fixture 创建，避免硬编码依赖
- 异步测试使用 `async def` + `await`
- 使用 httpx.AsyncClient 进行 API 集成测试

---

## 客户端测试规范（Godot）

### 必须覆盖的场景

关键玩法流程必须有最小回归脚本：
- 场景加载
- 任务触发与完成
- 投票入口打开、候选项展示、投票提交
- 投票结果展示
- 新内容区域加载
- 网络异常处理

### GUT (Godot Unit Testing)

- 推荐使用 GUT 框架编写单元测试
- 测试放在 `game/tests/` 目录
- UI 测试关注节点存在、信号连接、数据展示正确

---

## 内容测试规范

每次上线内容包之前，必须经过**四项自动化检查**：

### 1. 世界一致性检查

- 阵营关系不与骨架快照冲突
- NPC 身份不越过章节认知边界
- 聚落资源与地貌和势力匹配
- 事件影响不直接改写主线终局

### 2. 数值平衡检查

- 奖励不突破章节上限
- 敌人强度不超出区域允许区间
- 重复支线累计收益不形成刷取漏洞
- 资源刷新在服务器配置区间内

### 3. 内容安全检查

- 敏感词检测（命中直接驳回）
- 高风险主题识别（进入人工复核）
- 目标年龄层适配检查（不符合直接驳回）

### 4. 重复度检查

- 同章节 NPC 设定相似度阈值 ≤ 0.8
- 同区域支线骨架复用比例 ≤ 0.6
- 文案段落重复率 ≤ 0.3

---

## 测试门禁

- 代码合并前：所有单元测试必须通过
- 内容上线前：四项内容检查必须通过
- 发布前：代码流水线全绿 + 内容流水线全绿
- 性能要求：投票提交接口 p95 响应时间 < 300ms

---

## 相关规则

- Python 后端规范 → [10-python-backend.md](./10-python-backend.md)
- 发布与回滚规范 → [42-release-rollback.md](./42-release-rollback.md)
- AI 内容生成规范 → [51-ai-content-generation.md](./51-ai-content-generation.md)
