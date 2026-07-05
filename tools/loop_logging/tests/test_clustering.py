from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from ..signature_extractor import FailureSignatureExtractor
from ..clusterer import FailureClusterer, FailureCluster
from ..gap_classifier import GapClassifier


class TestSignatureExtractor:
    def test_extract_mypy_signature(self) -> None:
        log_message = "error TS2322: Type 'str' is not assignable to type 'int'"
        signature, error_type = FailureSignatureExtractor.extract_signature(log_message, "static")
        assert signature == "TS2322"
        assert error_type == "mypy"

    def test_extract_ruff_signature(self) -> None:
        log_message = "E501 line too long (120 > 79 characters)"
        signature, error_type = FailureSignatureExtractor.extract_signature(log_message, "static")
        assert signature == "E501"
        assert error_type == "ruff"

    def test_extract_test_signature(self) -> None:
        log_message = "test_vote_submit FAILED"
        signature, error_type = FailureSignatureExtractor.extract_signature(log_message, "test")
        assert signature == "test_vote_submit"
        assert error_type == "pytest"

    def test_extract_runtime_signature(self) -> None:
        log_message = "AttributeError: 'NoneType' object has no attribute 'id'"
        signature, error_type = FailureSignatureExtractor.extract_signature(log_message, "runtime")
        assert signature == "AttributeError"
        assert error_type == "attr-error"

    def test_classify_log_type_by_gate_name(self) -> None:
        log_type = FailureSignatureExtractor.classify_log_type("", "Mypy Typecheck")
        assert log_type == "static"

        log_type = FailureSignatureExtractor.classify_log_type("", "Unit Tests")
        assert log_type == "test"

        log_type = FailureSignatureExtractor.classify_log_type("", "Content Safety")
        assert log_type == "content"


class TestFailureClusterer:
    def test_cluster_failures(self) -> None:
        now = datetime.now()
        failures = [
            {"ts": now.isoformat(), "gate_name": "Mypy", "log_excerpt": "TS2322 type error"},
            {"ts": now.isoformat(), "gate_name": "Mypy", "log_excerpt": "TS2322 type error"},
            {"ts": now.isoformat(), "gate_name": "Pytest", "log_excerpt": "test_vote FAILED"},
        ]

        clusterer = FailureClusterer()
        clusters = clusterer.cluster(failures)

        assert len(clusters) == 2
        assert clusters[0].count >= clusters[1].count

    def test_get_top_clusters(self) -> None:
        now = datetime.now()
        failures = [
            {"ts": now.isoformat(), "gate_name": "Mypy", "log_excerpt": "TS2322 error"} for _ in range(10)
        ] + [
            {"ts": now.isoformat(), "gate_name": "Pytest", "log_excerpt": "test_a FAILED"} for _ in range(3)
        ] + [
            {"ts": now.isoformat(), "gate_name": "Pytest", "log_excerpt": "test_b FAILED"} for _ in range(1)
        ]

        clusterer = FailureClusterer()
        clusters = clusterer.cluster(failures)
        top_clusters = clusterer.get_top_clusters(clusters, top_n=2, min_count=2)

        assert len(top_clusters) == 2
        assert all(c.count >= 2 for c in top_clusters)

    def test_detect_repeated_failures(self) -> None:
        now = datetime.now()
        failures = [
            {"ts": now.isoformat(), "gate_name": "Mypy", "log_excerpt": "TS2322 error"} for _ in range(10)
        ] + [
            {"ts": now.isoformat(), "gate_name": "Pytest", "log_excerpt": "test_a FAILED"} for _ in range(3)
        ]

        clusterer = FailureClusterer()
        clusters = clusterer.cluster(failures)
        repeated = clusterer.detect_repeated_failures(clusters, repeat_threshold=5)

        assert len(repeated) == 1
        assert repeated[0].count >= 5


class TestGapClassifier:
    def test_classify_missing_gate(self) -> None:
        cluster = FailureCluster("TS2322", "mypy")
        cluster.count = 10
        cluster.gate_ids = {"G-UNKNOWN-001"}

        result = GapClassifier.classify_gap(cluster, ["G-STATIC-001", "G-STATIC-002"])
        assert result["gap_type"] == "missing_gate"

    def test_classify_coverage_gap(self) -> None:
        cluster = FailureCluster("test_vote", "pytest")
        cluster.count = 5
        cluster.gate_ids = {"G-UNIT-001"}

        result = GapClassifier.classify_gap(cluster, ["G-UNIT-001"])
        assert result["gap_type"] == "coverage_gap"

    def test_batch_classify_filters_low_confidence(self) -> None:
        cluster1 = FailureCluster("TS2322", "mypy")
        cluster1.count = 1

        clusters = [cluster1]
        results = GapClassifier.batch_classify(clusters, [])

        assert len(results) == 0