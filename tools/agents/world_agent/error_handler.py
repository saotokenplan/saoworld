class WorldAgentError(Exception):
    """World Agent 基础错误类"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class MissingSkeletonError(WorldAgentError):
    """骨架快照缺失错误"""

    def __init__(self, message: str):
        super().__init__(message)


class TemplateMismatchError(WorldAgentError):
    """模板不匹配错误"""

    def __init__(self, message: str):
        super().__init__(message)


class ContentViolationError(WorldAgentError):
    """内容违规错误"""

    def __init__(self, message: str):
        super().__init__(message)


class ReviewFailedError(WorldAgentError):
    """审核失败错误"""

    def __init__(self, message: str):
        super().__init__(message)


class HighDuplicationError(WorldAgentError):
    """重复度过高错误"""

    def __init__(self, message: str):
        super().__init__(message)


def handle_missing_skeleton(error: MissingSkeletonError) -> None:
    """处理骨架快照缺失错误"""
    print(f"[World Agent] 骨架快照缺失: {error.message}")
    print("[World Agent] 建议: 等待骨架快照创建或使用默认值")


def handle_template_mismatch(error: TemplateMismatchError) -> None:
    """处理模板不匹配错误"""
    print(f"[World Agent] 模板不匹配: {error.message}")
    print("[World Agent] 建议: 使用通用模板或创建新模板")


def handle_content_violation(error: ContentViolationError) -> None:
    """处理内容违规错误"""
    print(f"[World Agent] 内容违规: {error.message}")
    print("[World Agent] 建议: 重新生成内容，避免违规元素")


def handle_review_failed(error: ReviewFailedError) -> None:
    """处理审核失败错误"""
    print(f"[World Agent] 审核失败: {error.message}")
    print("[World Agent] 建议: 分析失败原因，修改内容后重新提交")


def handle_high_duplication(error: HighDuplicationError) -> None:
    """处理重复度过高错误"""
    print(f"[World Agent] 重复度过高: {error.message}")
    print("[World Agent] 建议: 重新生成内容，增加多样性")
