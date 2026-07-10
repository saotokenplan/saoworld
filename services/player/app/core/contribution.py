CONTRIBUTION_POINTS_PER_TIER = 1000
MAX_VOTE_WEIGHT_MULTIPLIER = 1.2
BASE_VOTE_WEIGHT_MULTIPLIER = 1.0


def calculate_vote_weight_multiplier(contribution_points: int) -> float:
    """根据贡献度计算投票权重倍率。

    每 1000 贡献度增加 0.1 倍率，最高不超过 1.2 倍。
    """
    extra = min(contribution_points / CONTRIBUTION_POINTS_PER_TIER * 0.1, 0.2)
    return round(BASE_VOTE_WEIGHT_MULTIPLIER + extra, 2)
