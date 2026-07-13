from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class Task(BaseModel):
    task_id: str
    title: str
    priority: str = Field(..., description="优先级：P0/P1/P2/P3")
    description: str
    requirements: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    assignee: str = Field(..., description="负责代理：world/backend/gameplay/qa")


class WorldRules(BaseModel):
    max_region_level: int = Field(default=10)
    npc_count_per_region: Dict[str, int] = Field(
        default_factory=lambda: {"min": 2, "max": 8}
    )
    quest_count_per_region: Dict[str, int] = Field(
        default_factory=lambda: {"min": 3, "max": 10}
    )


class Constraints(BaseModel):
    forbidden_tags: List[str] = Field(default_factory=list)
    reward_limits: Dict[str, Dict[str, int]] = Field(default_factory=dict)


class RuleLibrary(BaseModel):
    world_rules: WorldRules = Field(default_factory=WorldRules)
    constraints: Constraints = Field(default_factory=Constraints)


class VersionBrief(BaseModel):
    version: str
    title: str
    goals: List[str] = Field(default_factory=list)
    non_goals: List[str] = Field(default_factory=list)
    metrics: Dict[str, str] = Field(default_factory=dict)
    risks: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)


class TaskInput(BaseModel):
    task: Task
    rules: RuleLibrary
    existing_code_structure: Dict[str, List[str]] = Field(default_factory=dict)
    version_brief: Optional[VersionBrief] = None
