"""投票资格与贡献度相关计算工具。

复用 player-service 的权重倍率算法，并在 vote-service 本地进行资格判断。
"""

CONTRIBUTION_POINTS_PER_TIER = 1000
MAX_VOTE_WEIGHT_MULTIPLIER = 1.2
BASE_VOTE_WEIGHT_MULTIPLIER = 1.0


def calculate_vote_weight_multiplier(contribution_points: int) -> float:
    """根据贡献度计算投票权重倍率。

    每 1000 贡献度增加 0.1 倍率，最高不超过 1.2 倍。

    Args:
        contribution_points: 玩家当前贡献度总分

    Returns:
        float: 投票权重倍率
    """
    extra = min(contribution_points / CONTRIBUTION_POINTS_PER_TIER * 0.1, 0.2)
    return round(BASE_VOTE_WEIGHT_MULTIPLIER + extra, 2)


def check_vote_eligibility(contribution_points: int, threshold: int) -> bool:
    """检查玩家贡献度是否达到投票资格门槛。

    Args:
        contribution_points: 玩家当前贡献度总分
        threshold: 投票资格门槛

    Returns:
        bool: 是否具备投票资格
    """
    return contribution_points >= threshold
