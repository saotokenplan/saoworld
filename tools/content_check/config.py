from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "world_consistency": {
        "schema_version_required": True,
        "faction_relation_check": True,
        "chapter_boundary_check": True,
        "resource_matching_check": True,
        "mainline_protection": True,
    },
    "reward_boundary": {
        "chapter_exp_limits": {
            "chapter_01": 500,
            "chapter_02": 1500,
            "chapter_03": 3000,
        },
        "chapter_gold_limits": {
            "chapter_01": 100,
            "chapter_02": 300,
            "chapter_03": 600,
        },
        "region_level_ranges": {
            "region_core_ironward": [1, 10],
            "region_expansion_grayvalley": [5, 15],
            "region_west_forest": [10, 20],
            "region_east_ruins": [15, 25],
            "region_south_oasis": [10, 20],
        },
        "repeatable_reward_multiplier_cap": 0.5,
    },
    "content_safety": {
        "banned_words": [
            "违禁药品",
            "赌博",
            "色情",
            "暴力血腥",
            "恐怖主义",
            "分裂主义",
            "极端宗教",
        ],
        "high_risk_topics": [
            "自杀",
            "自残",
            "毒品制作",
            "武器制造",
        ],
        "target_age_rating": "teen",
        "max_banned_words_per_content": 0,
    },
    "duplication": {
        "npc_similarity_threshold": 0.8,
        "quest_skeleton_reuse_threshold": 0.6,
        "text_paragraph_repeat_threshold": 0.3,
        "min_text_length_for_check": 20,
    },
    "overall": {
        "pass_score": 75,
        "review_score": 50,
        "full_review_checks": [
            "world_consistency",
            "reward_boundary",
            "content_safety",
            "duplication",
        ],
    },
}


def get_default_config() -> dict[str, Any]:
    import copy
    return copy.deepcopy(DEFAULT_CONFIG)


def merge_config(base_config: dict[str, Any], override_config: dict[str, Any]) -> dict[str, Any]:
    result = dict(base_config)
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result
