from __future__ import annotations

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Optional, Any


@dataclass
class ThresholdConfig:
    gate_improvement: Dict[str, float] = field(default_factory=dict)
    rule_improvement: Dict[str, float] = field(default_factory=dict)
    clustering: Dict[str, float] = field(default_factory=dict)
    drift_detection: Dict[str, float] = field(default_factory=dict)


class ThresholdManager:
    def __init__(self, thresholds_file: str) -> None:
        self.thresholds_file: str = thresholds_file
        self.config: ThresholdConfig = ThresholdConfig()
        self._load_thresholds()

    def _load_thresholds(self) -> None:
        if not os.path.exists(self.thresholds_file):
            self._create_default_thresholds()
            return

        with open(self.thresholds_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if isinstance(data, dict):
            self.config = ThresholdConfig(
                gate_improvement=data.get("gate_improvement", {}),
                rule_improvement=data.get("rule_improvement", {}),
                clustering=data.get("clustering", {}),
                drift_detection=data.get("drift_detection", {}),
            )

    def _create_default_thresholds(self) -> None:
        default_data = {
            "gate_improvement": {
                "min_confidence": 0.7,
                "min_cluster_size": 3,
                "max_false_positive_rate": 0.3,
                "max_recurrence_days": 7,
            },
            "rule_improvement": {
                "min_issue_adoption_rate": 0.6,
                "max_false_positive_rate": 0.35,
                "max_false_negative_rate": 0.2,
                "min_precision_improvement": 0.1,
                "max_latency_hours": 24,
            },
            "clustering": {
                "min_similarity_score": 0.8,
                "max_cluster_count": 50,
                "min_samples_per_cluster": 2,
            },
            "drift_detection": {
                "alert_threshold": 0.2,
                "window_days": 30,
                "min_samples_for_trend": 10,
            },
        }
        self.config = ThresholdConfig(**default_data)
        self._save_thresholds(default_data)

    def _save_thresholds(self, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(self.thresholds_file), exist_ok=True)
        with open(self.thresholds_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def get_threshold(self, category: str, key: str) -> Optional[float]:
        category_dict = getattr(self.config, category, None)
        if category_dict is None:
            return None
        return category_dict.get(key)

    def set_threshold(self, category: str, key: str, value: float) -> None:
        category_dict = getattr(self.config, category, None)
        if category_dict is not None:
            category_dict[key] = value
            self._persist()

    def _persist(self) -> None:
        data = {
            "gate_improvement": self.config.gate_improvement,
            "rule_improvement": self.config.rule_improvement,
            "clustering": self.config.clustering,
            "drift_detection": self.config.drift_detection,
        }
        self._save_thresholds(data)

    def get_all_thresholds(self) -> Dict[str, Dict[str, float]]:
        return {
            "gate_improvement": self.config.gate_improvement,
            "rule_improvement": self.config.rule_improvement,
            "clustering": self.config.clustering,
            "drift_detection": self.config.drift_detection,
        }