from pydantic import BaseModel, Field
from typing import List, Optional


class ScriptProperty(BaseModel):
    name: str = Field(..., description="属性名称")
    type: str = Field(..., description="属性类型（String、int、bool、float、Vector2等）")
    default: Optional[str] = Field(None, description="默认值")


class ScriptMethod(BaseModel):
    name: str = Field(..., description="方法名称")
    return_type: str = Field(..., description="返回类型")
    parameters: List[dict] = Field(default_factory=list, description="参数列表")


class SignalDefinition(BaseModel):
    name: str = Field(..., description="信号名称")
    parameters: List[dict] = Field(default_factory=list, description="信号参数")


class SceneNode(BaseModel):
    name: str = Field(..., description="节点名称")
    type: str = Field(..., description="节点类型（Node2D、Sprite2D、Marker2D等）")
    properties: dict = Field(default_factory=dict, description="节点属性")
    children: Optional[List["SceneNode"]] = Field(default=None, description="子节点")


class DesignTask(BaseModel):
    design_id: str = Field(..., description="设计文档ID")
    task_id: str = Field(..., description="任务ID")
    title: str = Field(..., description="任务标题")
    type: str = Field(..., description="任务类型（scene、script、ui等）")
    target_module: str = Field(..., description="目标模块（game、world、ui等）")
    requirements: List[str] = Field(default_factory=list, description="需求列表")
    data_config: Optional[str] = Field(None, description="数据配置文件路径")


class SceneConfig(BaseModel):
    scene_name: str = Field(..., description="场景名称")
    nodes: List[SceneNode] = Field(default_factory=list, description="节点列表")
    signals: List[SignalDefinition] = Field(default_factory=list, description="信号定义")


class ScriptInterface(BaseModel):
    script_name: str = Field(..., description="脚本名称")
    extends: str = Field(..., description="继承类（Node2D、Control等）")
    properties: List[ScriptProperty] = Field(default_factory=list, description="属性定义")
    methods: List[ScriptMethod] = Field(default_factory=list, description="方法定义")


class DataConfig(BaseModel):
    data_path: str = Field(..., description="数据文件路径")
    schema_version: int = Field(1, description="数据版本")
    data_type: str = Field(..., description="数据类型（region、quest、npc等）")


class GameplayTaskInput(BaseModel):
    design_task: DesignTask = Field(..., description="设计任务")
    scene_config: Optional[SceneConfig] = Field(None, description="场景配置")
    script_interface: Optional[ScriptInterface] = Field(None, description="脚本接口")
    data_config: Optional[DataConfig] = Field(None, description="数据配置")
