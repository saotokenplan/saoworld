from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlayerEvent(BaseModel):
    event_type: str = Field(..., description="事件类型")
    player_id: str = Field(..., description="玩家ID")
    region_id: str = Field("", description="区域ID")
    timestamp: datetime = Field(..., description="事件时间")
    payload: dict = Field(default_factory=dict, description="事件负载")
    trace_id: str = Field("", description="追踪ID")


class EventBatchRequest(BaseModel):
    events: list[PlayerEvent] = Field(..., description="事件列表")


class EventBatchResponse(BaseModel):
    request_id: str = Field(..., description="请求ID")
    data: dict = Field(default_factory=dict, description="响应数据")
    meta: dict = Field(default_factory=dict, description="元信息")
    trace_id: str = Field("", description="追踪ID")