"""DuplicateDetectionRule 死参数接线与相似度纯函数测试。

覆盖 WP2 阈值调优预案第二节登记的死参数改造前置项：
`DuplicateDetectionRule.max_similarity` 此前构造函数接收但 `evaluate` 从未使用，
本轮将其接线为单对象自相似度阈值（默认 0.8），并补充跨样本相似度纯函数能力。
"""

import pytest

from app.core.auto_review_engine import DuplicateDetectionRule


class TestSelfSimilarity:
    """自相似度纯函数：1 - 字符多样度，受控输入可精确断言。"""

    def test_single_repeated_char_is_zero_diversity(self):
        # "aaaa" -> diversity 1/4 -> self_similarity 0.75
        assert DuplicateDetectionRule.self_similarity("aaaa") == pytest.approx(0.75)

    def test_alternating_two_chars(self):
        # "abab" -> diversity 2/4 -> self_similarity 0.5
        assert DuplicateDetectionRule.self_similarity("abab") == pytest.approx(0.5)

    def test_single_char_string(self):
        assert DuplicateDetectionRule.self_similarity("a") == pytest.approx(0.0)

    def test_empty_string_is_zero(self):
        assert DuplicateDetectionRule.self_similarity("") == 0.0

    def test_coerces_non_string_input(self):
        # str(12345) = "12345" -> diversity 1.0 -> self_similarity 0.0
        assert DuplicateDetectionRule.self_similarity(12345) == pytest.approx(0.0)


class TestCrossSimilarity:
    """跨样本字符级 Jaccard 相似度纯函数。"""

    def test_identical_is_one(self):
        assert DuplicateDetectionRule.cross_similarity("abc", "abc") == pytest.approx(1.0)

    def test_disjoint_is_zero(self):
        assert DuplicateDetectionRule.cross_similarity("ab", "cd") == pytest.approx(0.0)

    def test_empty_operand_is_zero(self):
        assert DuplicateDetectionRule.cross_similarity("", "abc") == 0.0
        assert DuplicateDetectionRule.cross_similarity("abc", "") == 0.0

    def test_partial_overlap(self):
        # "abc" ∩ "abd" = {a,b}=2 ; union = {a,b,c,d}=4 -> 0.5
        assert DuplicateDetectionRule.cross_similarity("abc", "abd") == pytest.approx(0.5)


class TestDuplicateDetectionRuleEvaluate:
    """evaluate 必须真正使用 max_similarity 阈值，而非硬编码常量。"""

    def test_short_description_skipped_regardless_of_repetition(self):
        rule = DuplicateDetectionRule()
        # len < 20 -> 不触发重复度检测
        assert rule.evaluate("region", {"description": "血腥血腥血腥"}, None) is None

    def test_high_repetition_rejected_at_default_threshold(self):
        rule = DuplicateDetectionRule()
        # 仅由「血腥」两字堆砌，字符多样度 2/24 -> 自相似度 0.917 >= 0.8
        rep = "血腥血腥血腥血腥血腥血腥血腥血腥血腥血腥血腥血腥"
        assert len(rep) >= 20
        assert rule.evaluate("region", {"description": rep}, None) == "rejected"

    def test_diverse_long_description_not_rejected(self):
        rule = DuplicateDetectionRule()
        diverse = "宁静的湖畔小镇，商人贩卖着来自远方的香料与织物，旅人在酒馆交换冒险故事。"
        assert rule.evaluate("region", {"description": diverse}, None) is None

    def test_parameter_is_wired_looser_threshold_skips_high_repetition(self):
        # 自相似度 0.917：默认 0.8 拦截，放宽到 0.99 不拦截，证明阈值被实际使用
        rep = "血腥血腥血腥血腥血腥血腥血腥血腥血腥血腥血腥血腥"
        assert DuplicateDetectionRule().evaluate("region", {"description": rep}, None) == "rejected"
        assert DuplicateDetectionRule(max_similarity=0.99).evaluate("region", {"description": rep}, None) is None

    def test_default_threshold_value_is_eight(self):
        # 与 M4 阈值调优预案登记的默认起步值一致
        assert DuplicateDetectionRule().max_similarity == 0.8
