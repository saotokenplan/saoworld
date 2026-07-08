"""Agent Dispatcher: 负责将任务分发给具体的 Agent 执行。

支持两种调度模式：
1. 直接调用（in-process）：直接实例化 Agent 类并调用其核心方法
2. 子进程调用（subprocess）：通过 CLI 命令行调用 Agent

默认使用直接调用模式，因为更高效且便于测试。
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentExecutionResult(BaseModel):
    """Agent 执行结果"""

    task_id: str = ""
    agent: str = ""
    success: bool = False
    output: Dict[str, Any] = {}
    error: Optional[str] = None
    duration_ms: int = 0


class AgentDispatcher:
    """Agent 调度器：将任务分发给对应的 Agent 执行"""

    # Agent 名称到模块路径的映射
    AGENT_REGISTRY: Dict[str, Dict[str, str]] = {
        "product-agent": {
            "module": "tools.agents.product_agent.product_agent",
            "class": "ProductAgent",
            "method": "run",
        },
        "system-designer-agent": {
            "module": "tools.agents.system_designer_agent.system_designer_agent",
            "class": "SystemDesignerAgent",
            "method": "execute_design_flow",
        },
        "backend-agent": {
            "module": "tools.agents.backend_agent.backend_agent",
            "class": "BackendAgent",
            "method": "run_workflow",
        },
        "gameplay-agent": {
            "module": "tools.agents.gameplay_agent.gameplay_agent",
            "class": "GameplayAgent",
            "method": "execute_gameplay_flow",
        },
        "world-agent": {
            "module": "tools.agents.world_agent.world_agent",
            "class": "WorldAgent",
            "method": "execute_world_generation_flow",
        },
        "world-agent-requirement": {
            "module": "tools.agents.world_agent.world_agent",
            "class": "WorldAgent",
            "method": "execute_requirement_driven_generation",
        },
        "qa-agent": {
            "module": "tools.agents.qa_agent.qa_agent",
            "class": "QAAgent",
            "method": "run_workflow",
        },
        "build-agent": {
            "module": "tools.agents.build_agent.build_agent",
            "class": "BuildAgent",
            "method": "execute_build_workflow",
        },
        "ops-agent": {
            "module": "tools.agents.ops_agent.ops_agent",
            "class": "OpsAgent",
            "method": "execute_ops_workflow",
        },
        "ops-agent-insight": {
            "module": "tools.agents.ops_agent.ops_agent",
            "class": "OpsAgent",
            "method": "execute_insight_extraction",
        },
        "ops-agent-requirement": {
            "module": "tools.agents.ops_agent.ops_agent",
            "class": "OpsAgent",
            "method": "execute_requirement_generation",
        },
    }

    def __init__(self) -> None:
        self._agent_instances: Dict[str, Any] = {}
        self._agent_classes: Dict[str, Type] = {}

    def _get_agent_class(self, agent_name: str) -> Optional[Type]:
        """动态导入并获取 Agent 类"""
        if agent_name in self._agent_classes:
            return self._agent_classes[agent_name]

        registry_entry = self.AGENT_REGISTRY.get(agent_name)
        if not registry_entry:
            logger.error("agent_not_registered: %s", agent_name)
            return None

        try:
            import importlib

            module = importlib.import_module(registry_entry["module"])
            agent_class: Type = getattr(module, registry_entry["class"])
            self._agent_classes[agent_name] = agent_class
            return agent_class
        except (ImportError, AttributeError) as e:
            logger.error("agent_import_failed: %s, error: %s", agent_name, str(e))
            return None

    def _get_agent_instance(self, agent_name: str) -> Optional[Any]:
        """获取或创建 Agent 实例"""
        if agent_name in self._agent_instances:
            return self._agent_instances[agent_name]

        agent_class = self._get_agent_class(agent_name)
        if not agent_class:
            return None

        try:
            instance = agent_class()
            self._agent_instances[agent_name] = instance
            return instance
        except Exception as e:
            logger.error("agent_instantiation_failed: %s, error: %s", agent_name, str(e))
            return None

    def dispatch(
        self,
        agent_name: str,
        task_input: Optional[Dict[str, Any]] = None,
        task_id: str = "",
    ) -> AgentExecutionResult:
        """将任务分发给指定 Agent 执行

        Args:
            agent_name: Agent 名称（如 "product-agent"）
            task_input: 任务输入数据
            task_id: 任务 ID（用于日志追踪）

        Returns:
            AgentExecutionResult: 执行结果
        """
        start_time = datetime.now(timezone.utc)

        if task_input is None:
            task_input = {}

        registry_entry = self.AGENT_REGISTRY.get(agent_name)
        if not registry_entry:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return AgentExecutionResult(
                task_id=task_id,
                agent=agent_name,
                success=False,
                error=f"Agent {agent_name} 未注册",
                duration_ms=int(elapsed),
            )

        instance = self._get_agent_instance(agent_name)
        if not instance:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return AgentExecutionResult(
                task_id=task_id,
                agent=agent_name,
                success=False,
                error=f"Agent {agent_name} 实例化失败",
                duration_ms=int(elapsed),
            )

        method_name = registry_entry["method"]
        method = getattr(instance, method_name, None)
        if not method:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            return AgentExecutionResult(
                task_id=task_id,
                agent=agent_name,
                success=False,
                error=f"Agent {agent_name} 没有方法 {method_name}",
                duration_ms=int(elapsed),
            )

        try:
            result = method(**task_input) if task_input else method()

            # 统一处理不同类型的返回值
            output: Dict[str, Any] = {}
            if isinstance(result, BaseModel):
                output = result.model_dump()
            elif isinstance(result, dict):
                output = result
            elif result is not None:
                output = {"result": str(result)}

            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            logger.info(
                "agent_dispatch_success: agent=%s task=%s duration=%dms",
                agent_name,
                task_id,
                int(elapsed),
            )
            return AgentExecutionResult(
                task_id=task_id,
                agent=agent_name,
                success=True,
                output=output,
                duration_ms=int(elapsed),
            )
        except Exception as e:
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            logger.error(
                "agent_dispatch_failed: agent=%s task=%s error=%s duration=%dms",
                agent_name,
                task_id,
                str(e),
                int(elapsed),
            )
            return AgentExecutionResult(
                task_id=task_id,
                agent=agent_name,
                success=False,
                error=str(e),
                duration_ms=int(elapsed),
            )

    def is_agent_registered(self, agent_name: str) -> bool:
        """检查 Agent 是否已注册"""
        return agent_name in self.AGENT_REGISTRY

    def get_registered_agents(self) -> list[str]:
        """获取所有已注册的 Agent 名称"""
        return list(self.AGENT_REGISTRY.keys())

    def reset(self) -> None:
        """重置调度器状态（清除缓存的 Agent 实例）"""
        self._agent_instances.clear()
        self._agent_classes.clear()
