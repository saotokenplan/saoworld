"""
Backend Agent - 负责编写后端服务代码

Backend Agent 负责编写投票服务、生成服务、审核服务和运营后台接口。
它将 System Designer Agent 的设计方案转化为可运行的后端代码。

核心流程：
1. 分析设计文档
2. 检查现有代码
3. 实现数据模型
4. 实现数据访问层
5. 实现 Pydantic Schemas
6. 实现 API 路由
7. 生成迁移脚本
8. 编写测试用例
9. 运行测试验证
10. 交付成果
"""

from .backend_agent import BackendAgent
from .input_schemas import DesignTask, APISpec, DataStructure, ExistingCode
from .output_schemas import ImplementationOutput, TestResult, BackendResult

__all__ = [
    "BackendAgent",
    "DesignTask",
    "APISpec",
    "DataStructure",
    "ExistingCode",
    "ImplementationOutput",
    "TestResult",
    "BackendResult",
]