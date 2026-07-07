from typing import List


class SystemDesignerError(Exception):
    def __init__(self, message: str, error_type: str):
        super().__init__(message)
        self.error_type = error_type


class RequirementAmbiguityError(SystemDesignerError):
    def __init__(self, message: str, missing_info: List[str] = None):
        super().__init__(message, "requirement_ambiguity")
        self.missing_info = missing_info or []


class TechnicalFeasibilityError(SystemDesignerError):
    def __init__(self, message: str, alternatives: List[str] = None):
        super().__init__(message, "technical_feasibility")
        self.alternatives = alternatives or []


class ModuleConflictError(SystemDesignerError):
    def __init__(self, message: str, conflicting_modules: List[str] = None):
        super().__init__(message, "module_conflict")
        self.conflicting_modules = conflicting_modules or []


class PerformanceRiskError(SystemDesignerError):
    def __init__(self, message: str, risk_level: str = "medium", recommendations: List[str] = None):
        super().__init__(message, "performance_risk")
        self.risk_level = risk_level
        self.recommendations = recommendations or []


def handle_requirement_ambiguity(task_title: str, missing_info: List[str]) -> RequirementAmbiguityError:
    message = f"需求不明确：任务 '{task_title}' 缺少关键信息"
    return RequirementAmbiguityError(message, missing_info)


def handle_technical_feasibility(task_title: str, reason: str, alternatives: List[str]) -> TechnicalFeasibilityError:
    message = f"技术不可行：任务 '{task_title}' 在现有技术栈下无法实现 - {reason}"
    return TechnicalFeasibilityError(message, alternatives)


def handle_module_conflict(task_title: str, conflicting_modules: List[str]) -> ModuleConflictError:
    message = f"模块冲突：任务 '{task_title}' 设计方案与现有模块存在冲突"
    return ModuleConflictError(message, conflicting_modules)


def handle_performance_risk(task_title: str, risk_level: str, recommendations: List[str]) -> PerformanceRiskError:
    message = f"性能风险：任务 '{task_title}' 设计方案存在 {risk_level} 级性能隐患"
    return PerformanceRiskError(message, risk_level, recommendations)