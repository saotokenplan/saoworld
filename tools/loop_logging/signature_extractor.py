from __future__ import annotations

import re
from typing import Optional, Tuple


class FailureSignatureExtractor:
    STATIC_ERROR_PATTERNS = [
        (r"(TS\d+)", "mypy"),
        (r"(E\d+)\s+", "ruff"),
        (r"(F\d+)\s+", "ruff"),
        (r"(W\d+)\s+", "ruff"),
        (r"(C\d+)\s+", "ruff"),
        (r"(N\d+)\s+", "ruff"),
        (r"(S\d+)\s+", "ruff"),
        (r"(E\d+\.\d+)\s+", "pylint"),
    ]

    TEST_FAILURE_PATTERNS = [
        (r"(test_\w+)\s*\[", "pytest-parametrized"),
        (r"(test_\w+)\s*FAILED", "pytest"),
        (r"AssertionError", "assertion"),
        (r"AssertionError:\s*(.+)", "assertion-detail"),
    ]

    RUNTIME_ERROR_PATTERNS = [
        (r"(AttributeError)\s*:", "attr-error"),
        (r"(TypeError)\s*:", "type-error"),
        (r"(ValueError)\s*:", "value-error"),
        (r"(KeyError)\s*:", "key-error"),
        (r"(IndexError)\s*:", "index-error"),
        (r"(RuntimeError)\s*:", "runtime-error"),
        (r"(ConnectionError)\s*:", "conn-error"),
        (r"(TimeoutError)\s*:", "timeout-error"),
    ]

    CONTENT_RULE_PATTERNS = [
        (r"(WORLD_RULE_\d+)", "world-rule"),
        (r"(REWARD_BUDGET_\d+)", "reward-budget"),
        (r"(SAFETY_RULE_\d+)", "safety-rule"),
        (r"(DUPLICATION_RULE_\d+)", "duplication-rule"),
    ]

    @classmethod
    def extract_signature(cls, log_message: str, log_type: str = "ci") -> Tuple[str, str]:
        if log_type == "static":
            return cls._extract_static_signature(log_message)
        elif log_type == "test":
            return cls._extract_test_signature(log_message)
        elif log_type == "runtime":
            return cls._extract_runtime_signature(log_message)
        elif log_type == "content":
            return cls._extract_content_signature(log_message)
        else:
            return cls._extract_generic_signature(log_message)

    @classmethod
    def _extract_static_signature(cls, log_message: str) -> Tuple[str, str]:
        for pattern, error_type in cls.STATIC_ERROR_PATTERNS:
            match = re.search(pattern, log_message)
            if match:
                return match.group(1), error_type
        return cls._extract_generic_signature(log_message)

    @classmethod
    def _extract_test_signature(cls, log_message: str) -> Tuple[str, str]:
        for pattern, error_type in cls.TEST_FAILURE_PATTERNS:
            match = re.search(pattern, log_message)
            if match:
                return match.group(1), error_type
        return cls._extract_generic_signature(log_message)

    @classmethod
    def _extract_runtime_signature(cls, log_message: str) -> Tuple[str, str]:
        for pattern, error_type in cls.RUNTIME_ERROR_PATTERNS:
            match = re.search(pattern, log_message)
            if match:
                return match.group(1), error_type
        return cls._extract_generic_signature(log_message)

    @classmethod
    def _extract_content_signature(cls, log_message: str) -> Tuple[str, str]:
        for pattern, error_type in cls.CONTENT_RULE_PATTERNS:
            match = re.search(pattern, log_message)
            if match:
                return match.group(1), error_type
        return cls._extract_generic_signature(log_message)

    @classmethod
    def _extract_generic_signature(cls, log_message: str) -> Tuple[str, str]:
        trimmed = log_message.strip()[:200]
        hash_val = abs(hash(trimmed)) % 10**8
        return f"GENERIC_{hash_val:08d}", "generic"

    @classmethod
    def classify_log_type(cls, log_message: str, gate_name: Optional[str] = None) -> str:
        if gate_name:
            gate_lower = gate_name.lower()
            if "lint" in gate_lower or "format" in gate_lower:
                return "static"
            if "typecheck" in gate_lower or "mypy" in gate_lower:
                return "static"
            if "test" in gate_lower or "pytest" in gate_lower:
                return "test"
            if "e2e" in gate_lower:
                return "test"
            if "content" in gate_lower:
                return "content"

        for pattern in cls.STATIC_ERROR_PATTERNS:
            if re.search(pattern[0], log_message):
                return "static"

        for pattern in cls.TEST_FAILURE_PATTERNS:
            if re.search(pattern[0], log_message):
                return "test"

        for pattern in cls.RUNTIME_ERROR_PATTERNS:
            if re.search(pattern[0], log_message):
                return "runtime"

        for pattern in cls.CONTENT_RULE_PATTERNS:
            if re.search(pattern[0], log_message):
                return "content"

        return "generic"