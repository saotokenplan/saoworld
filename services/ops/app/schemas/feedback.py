"""用户反馈 Schema 定义。"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FeedbackSubmit(BaseModel):
    """反馈提交请求。"""

    feedback_type: str = Field(..., min_length=1, max_length=32, description="反馈类型：bug/suggestion/question/other")
    title: str = Field(..., min_length=1, max_length=256, description="反馈标题")
    content: str = Field(..., min_length=1, max_length=5000, description="反馈内容")
    priority: str = Field(default="medium", description="优先级：low/medium/high/critical")
    region_id: str | None = Field(None, description="相关区域ID")
    chapter_id: str | None = Field(None, description="相关章节ID")
    attachment_urls: list[str] | None = Field(None, description="附件URL列表")
    metadata: dict[str, Any] | None = Field(None, description="元数据")


class FeedbackUpdate(BaseModel):
    """反馈更新请求（运营侧）。"""

    status: str | None = Field(None, description="状态：pending/in_progress/resolved/closed")
    priority: str | None = Field(None, description="优先级：low/medium/high/critical")
    resolution_note: str | None = Field(None, max_length=5000, description="处理备注")


class FeedbackResponse(BaseModel):
    """反馈响应。"""

    model_config = ConfigDict(from_attributes=True)

    feedback_id: uuid.UUID
    player_id: str
    feedback_type: str
    priority: str
    status: str
    title: str
    content: str
    region_id: str | None
    chapter_id: str | None
    attachment_urls: list[str] | None
    metadata_jsonb: dict[str, Any] | None
    resolved_by: str | None
    resolved_at: datetime | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime


class FeedbackListResponse(BaseModel):
    """反馈列表响应。"""

    model_config = ConfigDict(from_attributes=True)

    feedbacks: list[FeedbackResponse]
    total: int
    limit: int
    offset: int


class FeedbackStatsResponse(BaseModel):
    """反馈统计响应。"""

    total: int
    pending: int
    in_progress: int
    resolved: int
    closed: int
    by_type: dict[str, int]
    by_priority: dict[str, int]