from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class RegionInfo(BaseModel):
    region_id: str = Field(..., description="区域ID")
    name: str = Field(..., description="区域名称")
    status: str = Field("active", description="区域状态")


class FactionInfo(BaseModel):
    faction_id: str = Field(..., description="阵营ID")
    name: str = Field(..., description="阵营名称")
    alignment: str = Field("neutral", description="阵营倾向（lawful/neutral/chaotic）")


class RewardLimits(BaseModel):
    gold: Dict[str, int] = Field(default_factory=lambda: {"min": 10, "max": 1000}, description="金币奖励范围")
    exp: Dict[str, int] = Field(default_factory=lambda: {"min": 50, "max": 5000}, description="经验奖励范围")


class WorldRules(BaseModel):
    world_version: str = Field("1.0", description="世界版本")
    chapter_id: str = Field(..., description="章节ID")
    regions: List[RegionInfo] = Field(default_factory=list, description="区域列表")
    factions: List[FactionInfo] = Field(default_factory=list, description="阵营列表")
    forbidden_tags: List[str] = Field(default_factory=list, description="禁止标签")
    reserved_characters: List[str] = Field(default_factory=list, description="保留角色名")
    reward_limits: RewardLimits = Field(default_factory=RewardLimits, description="奖励限制")


class VoteResult(BaseModel):
    vote_cycle_id: str = Field(..., description="投票周期ID")
    winning_candidate_id: str = Field(..., description="获胜候选项ID")
    winning_direction: str = Field(..., description="获胜方向描述")
    voter_count: int = Field(0, description="投票人数")
    winning_percentage: float = Field(0.0, description="获胜百分比")


class TemplateField(BaseModel):
    name: str = Field(..., description="字段名称")
    type: str = Field(..., description="字段类型")
    options: Optional[List[str]] = Field(None, description="可选值列表")


class ContentTemplate(BaseModel):
    template_id: str = Field(..., description="模板ID")
    type: str = Field(..., description="模板类型（npc/quest/region/event）")
    schema_version: int = Field(1, description="模板版本")
    fields: List[TemplateField] = Field(default_factory=list, description="模板字段定义")


class SkeletonSnapshot(BaseModel):
    skeleton_id: str = Field(..., description="骨架快照ID")
    world_version: str = Field("1.0", description="世界版本")
    chapter_id: str = Field(..., description="章节ID")
    regions: List[dict] = Field(default_factory=list, description="区域列表")
    factions: List[dict] = Field(default_factory=list, description="阵营列表")
    forbidden_tags: List[str] = Field(default_factory=list, description="禁止标签")
    timestamp: str = Field("", description="时间戳")
    status: str = Field("active", description="状态")


class DesignNote(BaseModel):
    note_id: str = Field(..., description="设计文档ID")
    chapter_id: str = Field(..., description="章节ID")
    content_type: str = Field(..., description="内容类型（npc/quest/region/event）")
    description: str = Field("", description="设计说明")
    constraints: List[str] = Field(default_factory=list, description="约束条件")


class WorldTaskInput(BaseModel):
    world_rules: WorldRules = Field(..., description="世界规则")
    vote_result: Optional[VoteResult] = Field(None, description="投票结果")
    template: Optional[ContentTemplate] = Field(None, description="内容模板")
    skeleton_snapshot: Optional[SkeletonSnapshot] = Field(None, description="骨架快照")
    design_note: Optional[DesignNote] = Field(None, description="设计文档")
