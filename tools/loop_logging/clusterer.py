from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from .signature_extractor import FailureSignatureExtractor


class FailureCluster:
    def __init__(self, signature: str, error_type: str) -> None:
        self.signature: str = signature
        self.error_type: str = error_type
        self.count: int = 0
        self.first_seen: Optional[datetime] = None
        self.last_seen: Optional[datetime] = None
        self.gate_ids: set[str] = set()
        self.gate_names: set[str] = set()
        self.examples: List[str] = []
        self.related_task_ids: set[str] = set()

    def add_failure(self, failure: dict[str, Any]) -> None:
        self.count += 1
        ts_str = failure.get("ts")
        if ts_str:
            ts = datetime.fromisoformat(ts_str)
            if self.first_seen is None or ts < self.first_seen:
                self.first_seen = ts
            if self.last_seen is None or ts > self.last_seen:
                self.last_seen = ts

        if "gate_id" in failure:
            self.gate_ids.add(failure["gate_id"])
        if "gate_name" in failure:
            self.gate_names.add(failure["gate_name"])
        if "related_task_id" in failure and failure["related_task_id"]:
            self.related_task_ids.add(failure["related_task_id"])

        log_excerpt = failure.get("log_excerpt", "")
        if log_excerpt and len(self.examples) < 5:
            self.examples.append(log_excerpt[:500])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signature": self.signature,
            "error_type": self.error_type,
            "count": self.count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "gate_ids": sorted(list(self.gate_ids)),
            "gate_names": sorted(list(self.gate_names)),
            "examples": self.examples,
            "related_task_ids": sorted(list(self.related_task_ids)),
        }


class FailureClusterer:
    def __init__(self, max_history_days: int = 30) -> None:
        self.max_history_days: int = max_history_days
        self._clusters: Dict[str, FailureCluster] = {}

    def cluster(
        self,
        failures: List[dict[str, Any]],
        time_window: Optional[timedelta] = None,
    ) -> List[FailureCluster]:
        self._clusters = {}
        cutoff_time = datetime.now() - (time_window or timedelta(days=self.max_history_days))

        for failure in failures:
            ts_str = failure.get("ts")
            if ts_str:
                ts = datetime.fromisoformat(ts_str)
                if ts < cutoff_time:
                    continue

            log_excerpt = failure.get("log_excerpt", "")
            gate_name = failure.get("gate_name", "")
            log_type = FailureSignatureExtractor.classify_log_type(log_excerpt, gate_name)
            signature, error_type = FailureSignatureExtractor.extract_signature(log_excerpt, log_type)

            if signature not in self._clusters:
                self._clusters[signature] = FailureCluster(signature, error_type)

            self._clusters[signature].add_failure(failure)

        return sorted(
            self._clusters.values(),
            key=lambda c: c.count,
            reverse=True,
        )

    def get_top_clusters(
        self,
        clusters: List[FailureCluster],
        top_n: int = 10,
        min_count: int = 2,
    ) -> List[FailureCluster]:
        return [
            c for c in clusters[:top_n]
            if c.count >= min_count
        ]

    def detect_repeated_failures(
        self,
        clusters: List[FailureCluster],
        repeat_threshold: int = 5,
    ) -> List[FailureCluster]:
        return [
            c for c in clusters
            if c.count >= repeat_threshold
        ]

    def analyze_cluster_trends(
        self,
        clusters: List[FailureCluster],
    ) -> List[Dict[str, Any]]:
        results = []
        now = datetime.now()

        for cluster in clusters:
            if cluster.first_seen and cluster.last_seen:
                age_days = (now - cluster.first_seen).days
                recurrence_interval = (cluster.last_seen - cluster.first_seen).days / cluster.count if cluster.count > 1 else 0
                is_chronic = age_days > 7 and cluster.count > 3
            else:
                age_days = 0
                recurrence_interval = 0
                is_chronic = False

            results.append({
                "signature": cluster.signature,
                "error_type": cluster.error_type,
                "count": cluster.count,
                "age_days": age_days,
                "recurrence_interval_days": round(recurrence_interval, 2),
                "is_chronic": is_chronic,
                "gate_names": sorted(list(cluster.gate_names)),
            })

        return sorted(results, key=lambda x: x["count"], reverse=True)