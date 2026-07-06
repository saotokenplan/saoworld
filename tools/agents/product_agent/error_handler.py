from typing import Optional
import structlog

logger = structlog.get_logger()


class InputMissingError(Exception):
    def __init__(self, input_name: str, message: str = ""):
        self.input_name = input_name
        self.message = message or f"输入数据缺失: {input_name}"
        super().__init__(self.message)


class DataConflictError(Exception):
    def __init__(self, conflict_type: str, message: str = ""):
        self.conflict_type = conflict_type
        self.message = message or f"数据冲突: {conflict_type}"
        super().__init__(self.message)


class GoalUnreachableError(Exception):
    def __init__(self, goal: str, reason: str = ""):
        self.goal = goal
        self.reason = reason or f"目标无法实现: {goal}"
        super().__init__(self.reason)


class UrgentIssueInsertedError(Exception):
    def __init__(self, issue_id: str, issue_title: str):
        self.issue_id = issue_id
        self.issue_title = issue_title
        self.message = f"紧急问题插入: {issue_id} - {issue_title}"
        super().__init__(self.message)


class ErrorHandler:
    @staticmethod
    def handle_input_missing(input_name: str, default_value: Optional[any] = None) -> any:
        logger.warning("input_data_missing", input_name=input_name)
        if default_value is not None:
            logger.info("using_default_value", input_name=input_name, default=default_value)
            return default_value
        raise InputMissingError(input_name)

    @staticmethod
    def handle_data_conflict(conflict_type: str, vote_results_priority: bool = True) -> str:
        logger.warning("data_conflict_detected", conflict_type=conflict_type)
        resolution = "vote_results" if vote_results_priority else "online_data"
        logger.info("conflict_resolved", conflict_type=conflict_type, resolution=resolution)
        return resolution

    @staticmethod
    def handle_goal_unreachable(goal: str, reason: str = "") -> None:
        logger.error("goal_unreachable", goal=goal, reason=reason)
        raise GoalUnreachableError(goal, reason)

    @staticmethod
    def handle_urgent_issue(issue_id: str, issue_title: str) -> None:
        logger.warning("urgent_issue_inserted", issue_id=issue_id, issue_title=issue_title)
        raise UrgentIssueInsertedError(issue_id, issue_title)

    @staticmethod
    def validate_input_completeness(inputs: dict) -> bool:
        missing = []
        for key, value in inputs.items():
            if value is None:
                missing.append(key)
        if missing:
            logger.warning("input_validation_failed", missing_inputs=missing)
            return False
        logger.info("input_validation_passed")
        return True
