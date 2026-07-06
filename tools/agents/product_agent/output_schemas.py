from datetime import date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Task(BaseModel):
    id: str
    title: str
    priority: Literal["P0", "P1", "P2", "P3"]
    size: Literal["small", "medium", "large", "xl"]
    dependencies: List[str] = Field(default_factory=list)
    estimated_hours: float
    assignee: str
    description: Optional[str] = None


class OutputMilestone(BaseModel):
    id: str
    name: str
    due_date: date
    tasks: List[str] = Field(default_factory=list)
    status: Literal["pending", "in_progress", "completed"] = "pending"


class PriorityMatrix(BaseModel):
    version: str
    tasks: List[Task] = Field(default_factory=list)


class MilestonePlan(BaseModel):
    version: str
    milestones: List[OutputMilestone] = Field(default_factory=list)


class VersionBrief(BaseModel):
    version: str
    goals: List[str] = Field(default_factory=list)
    not_goals: List[str] = Field(default_factory=list)
    core_metrics: List[str] = Field(default_factory=list)
    key_risks: List[str] = Field(default_factory=list)
    risk_mitigation: List[str] = Field(default_factory=list)
    acceptance_criteria: List[str] = Field(default_factory=list)
    created_at: date
