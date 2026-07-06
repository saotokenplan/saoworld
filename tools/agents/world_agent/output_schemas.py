from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime, timezone


class NPCConfig(BaseModel):
    npc_id: str = Field(..., description="NPC ID")
    name: str = Field(..., description="NPC名称")
    title: str = Field("", description="NPC称号")
    faction_id: str = Field("", description="所属阵营ID")
    region_id: str = Field("", description="所在区域ID")
    personality: str = Field("neutral", description="性格特征")
    skills: List[str] = Field(default_factory=list, description="技能列表")
    dialogs: Dict[str, str] = Field(default_factory=dict, description="对话模板")
    schema_version: int = Field(1, description="数据版本")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="生成时间")


class Objective(BaseModel):
    type: str = Field(..., description="目标类型（explore/defeat/collect/talk）")
    target: str = Field(..., description="目标描述")
    count: int = Field(1, description="目标数量")


class QuestConfig(BaseModel):
    quest_id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    type: str = Field("side", description="任务类型（main/side）")
    region_id: str = Field("", description="所属区域ID")
    npc_id: str = Field("", description="关联NPC ID")
    objectives: List[Objective] = Field(default_factory=list, description="任务目标")
    rewards: Dict[str, int | List[str]] = Field(default_factory=dict, description="奖励")
    prerequisites: List[str] = Field(default_factory=list, description="前置条件")
    schema_version: int = Field(1, description="数据版本")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="生成时间")


class RegionScope(BaseModel):
    biome: str = Field(..., description="地貌类型")
    climate: str = Field("", description="气候特征")
    resources: List[str] = Field(default_factory=list, description="资源列表")
    dangers: List[str] = Field(default_factory=list, description="危险列表")


class RegionConfig(BaseModel):
    region_id: str = Field(..., description="区域ID")
    name: str = Field(..., description="区域名称")
    description: str = Field("", description="区域描述")
    status: str = Field("locked", description="区域状态")
    level_range: Dict[str, int] = Field(default_factory=lambda: {"min": 1, "max": 10}, description="等级范围")
    region_scope: Optional[RegionScope] = Field(None, description="区域范围信息")
    schema_version: int = Field(1, description="数据版本")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="生成时间")


class EventConfig(BaseModel):
    event_id: str = Field(..., description="事件ID")
    name: str = Field(..., description="事件名称")
    type: str = Field(..., description="事件类型（raid/discovery/trade/conflict）")
    region_id: str = Field("", description="所属区域ID")
    description: str = Field("", description="事件描述")
    impact: str = Field("minor", description="影响程度（minor/major/critical）")
    duration: str = Field("temporary", description="持续类型（temporary/permanent）")
    schema_version: int = Field(1, description="数据版本")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="生成时间")


class ContentPackageOutput(BaseModel):
    content_package_id: str = Field(..., description="内容包ID")
    version: str = Field("1.0", description="版本号")
    chapter_id: str = Field("", description="章节ID")
    region_id: str = Field("", description="区域ID")
    type: str = Field(..., description="内容类型")
    content: Dict[str, List] = Field(default_factory=dict, description="内容数据")
    schema_version: int = Field(1, description="数据版本")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="生成时间")


class ReviewRequest(BaseModel):
    request_id: str = Field(..., description="审核请求ID")
    content_package_id: str = Field("", description="内容包ID")
    type: str = Field("content_review", description="审核类型")
    checks: List[str] = Field(
        default_factory=lambda: ["world_consistency", "reward_boundary", "content_safety", "duplication"],
        description="检查项",
    )
    priority: str = Field("normal", description="优先级（normal/high/critical）")


class WorldGenerationResult(BaseModel):
    result_id: str = Field(..., description="结果ID")
    task_type: str = Field(..., description="任务类型（npc/quest/region/event/full）")
    npc_configs: List[NPCConfig] = Field(default_factory=list, description="NPC配置列表")
    quest_configs: List[QuestConfig] = Field(default_factory=list, description="任务配置列表")
    region_configs: List[RegionConfig] = Field(default_factory=list, description="区域配置列表")
    event_configs: List[EventConfig] = Field(default_factory=list, description="事件配置列表")
    content_package: Optional[ContentPackageOutput] = Field(None, description="内容包")
    review_request: Optional[ReviewRequest] = Field(None, description="审核请求")
    status: str = Field("completed", description="执行状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="创建时间")
