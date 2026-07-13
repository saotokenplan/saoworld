from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class DesignNoteMetadata(BaseModel):
    design_id: str
    task_id: str
    title: str
    version: str = "1.0"
    status: str = "draft"
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
    author: str = "system-designer-agent"


class FieldDefinition(BaseModel):
    name: str
    type: str
    primary_key: bool = False
    nullable: bool = False
    default: Optional[str] = None
    check: Optional[List[str]] = None


class DataStructure(BaseModel):
    model_name: str
    table_name: str
    fields: List[FieldDefinition] = Field(default_factory=list)
    constraints: List[Dict[str, List[str]]] = Field(default_factory=list)
    indexes: List[Dict[str, List[str]]] = Field(default_factory=list)


class RequestField(BaseModel):
    name: str
    type: str
    required: bool = True


class ResponseField(BaseModel):
    name: str
    type: str


class InterfaceDefinition(BaseModel):
    endpoint: str
    method: str
    scope: str
    request: Dict[str, List[RequestField]] = Field(default_factory=dict)
    response: Dict[str, List[ResponseField]] = Field(default_factory=dict)


class ModuleChange(BaseModel):
    type: str = Field(..., description="add/modify/delete")
    file: str
    description: str


class ModulePlan(BaseModel):
    name: str
    changes: List[ModuleChange] = Field(default_factory=list)


class ChangePlan(BaseModel):
    design_id: str
    modules: List[ModulePlan] = Field(default_factory=list)
    migrations: List[Dict[str, str]] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)


class ValidationResult(BaseModel):
    check: str
    passed: bool
    message: str


class ArchitectureValidationReport(BaseModel):
    design_id: str
    results: List[ValidationResult] = Field(default_factory=list)
    overall_status: str = "pending"
    risk_score: float = 0.0


class DesignNote(BaseModel):
    metadata: DesignNoteMetadata
    analysis_summary: str = ""
    architecture_overview: str = ""
    data_structures: List[DataStructure] = Field(default_factory=list)
    interfaces: List[InterfaceDefinition] = Field(default_factory=list)
    change_plan: Optional[ChangePlan] = None
    validation_report: Optional[ArchitectureValidationReport] = None
    risks: List[str] = Field(default_factory=list)
