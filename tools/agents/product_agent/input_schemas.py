from datetime import date
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class InputMilestone(BaseModel):
    id: str
    name: str
    due_date: date
    completed: bool


class VersionStatus(BaseModel):
    version: str
    status: Literal["in_progress", "completed", "pending"]
    completed_tasks: int
    total_tasks: int
    blockers: List[str] = Field(default_factory=list)
    milestones: List[InputMilestone] = Field(default_factory=list)


class VoteResult(BaseModel):
    candidate_id: str
    votes: int
    percentage: float


class VoteResults(BaseModel):
    vote_cycle_id: str
    winning_candidate_id: str
    results: List[VoteResult]
    total_voters: int


class TrendData(BaseModel):
    user_growth: Literal["up", "down", "stable"]
    engagement: Literal["up", "down", "stable"]
    content_consumption: Literal["up", "down", "stable"]


class OnlineMetrics(BaseModel):
    daily_active_users: int
    vote_participation_rate: float
    task_completion_rate: float
    new_content_stay_time: int
    crash_rate: float
    trends: TrendData


class Issue(BaseModel):
    id: str
    title: str
    severity: Literal["high", "medium", "low", "critical"]
    type: Literal["performance", "content", "bug", "feature", "security"]
    status: Literal["open", "in_progress", "resolved", "closed"]


class IssueList(BaseModel):
    issues: List[Issue] = Field(default_factory=list)


class Roadmap(BaseModel):
    phases: List[str] = Field(default_factory=list)
    current_phase: Optional[str] = None
    goals: List[str] = Field(default_factory=list)
    timeline: Optional[str] = None


class VisionDocument(BaseModel):
    vision: str
    core_values: List[str] = Field(default_factory=list)
    long_term_goals: List[str] = Field(default_factory=list)
