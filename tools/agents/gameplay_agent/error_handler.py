class GameplayError(Exception):
    """Gameplay Agent 基础错误类"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class IncompleteDesignError(GameplayError):
    """设计不完整错误"""

    def __init__(self, message: str):
        super().__init__(message)


class InvalidNodeReferenceError(GameplayError):
    """节点引用失效错误"""

    def __init__(self, message: str):
        super().__init__(message)


class ScriptSyntaxError(GameplayError):
    """脚本语法错误"""

    def __init__(self, message: str):
        super().__init__(message)


class MissingDataConfigError(GameplayError):
    """数据配置缺失错误"""

    def __init__(self, message: str):
        super().__init__(message)


class TestFailureError(GameplayError):
    """测试失败错误"""

    def __init__(self, message: str):
        super().__init__(message)


def handle_incomplete_design(error: IncompleteDesignError) -> None:
    """处理设计不完整错误"""
    print(f"[Gameplay Agent] 设计不完整: {error.message}")
    print("[Gameplay Agent] 建议: 向 System Designer Agent 请求补充设计文档")


def handle_invalid_node_reference(error: InvalidNodeReferenceError) -> None:
    """处理节点引用失效错误"""
    print(f"[Gameplay Agent] 节点引用失效: {error.message}")
    print("[Gameplay Agent] 建议: 修复节点引用或创建缺失节点")


def handle_script_syntax_error(error: ScriptSyntaxError) -> None:
    """处理脚本语法错误"""
    print(f"[Gameplay Agent] 脚本语法错误: {error.message}")
    print("[Gameplay Agent] 建议: 检查 GDScript 语法并修复")


def handle_missing_data_config(error: MissingDataConfigError) -> None:
    """处理数据配置缺失错误"""
    print(f"[Gameplay Agent] 数据配置缺失: {error.message}")
    print("[Gameplay Agent] 建议: 创建默认配置或等待配置完成")


def handle_test_failure(error: TestFailureError) -> None:
    """处理测试失败错误"""
    print(f"[Gameplay Agent] 测试失败: {error.message}")
    print("[Gameplay Agent] 建议: 分析失败原因，修复代码后重新运行测试")
