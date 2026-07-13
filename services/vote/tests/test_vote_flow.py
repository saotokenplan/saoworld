import uuid

import pytest
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.core.config import settings
from app.core.content_client import ContentPackageInfo
from app.core.errors import VoteErrorCodes
from app.domain.models import VoteCycle
from app.schemas.auth import Role


def _player_headers(player_id: str | None = None) -> dict[str, str]:
    """创建玩家请求头（含 JWT Token）。"""
    if player_id is None:
        player_id = str(uuid.uuid4())
    token = create_test_token(user_id=player_id, role=Role.PLAYER)
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_current_vote_returns_open_cycle(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert body["request_id"]
    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["chapter_id"] == "ch_prologue_01"
    assert data["status"] == "open"
    assert data["has_voted"] is False
    assert data["my_vote_candidate_id"] is None
    assert len(data["candidates"]) == 3
    candidate_titles = [c["title"] for c in data["candidates"]]
    assert "探索迷雾森林" in candidate_titles
    assert "重建边境哨所" in candidate_titles
    assert "追踪暗影盗贼" in candidate_titles


@pytest.mark.asyncio
async def test_get_current_vote_shows_my_vote(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    first_candidate = open_vote_cycle.candidates[0]

    submit_resp = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-vote-1",
        },
        json={
            "candidate_id": str(first_candidate.candidate_id),
            "device_fingerprint_hash": "device_hash_abc123",
            "weight": 1.0,
        },
    )
    assert submit_resp.status_code == 201

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["has_voted"] is True
    assert data["my_vote_candidate_id"] == str(first_candidate.candidate_id)


@pytest.mark.asyncio
async def test_submit_vote_success(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[1]

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-vote-2",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "device_hash_def456",
            "weight": 2.5,
        },
    )
    assert response.status_code == 201
    body = response.json()
    data = body["data"]
    assert "vote_id" in data
    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["candidate_id"] == str(candidate.candidate_id)
    assert data["request_id"]
    assert "submitted_at" in data
    assert data["weight"] == 2.75
    assert data["weight_multiplier"] == 1.1
    assert data["contribution_points"] == 1000
    assert body["request_id"]
    assert "X-Request-Id" in response.headers


@pytest.mark.asyncio
async def test_submit_vote_insufficient_contribution(
    client: AsyncClient, open_vote_cycle: VoteCycle, monkeypatch
):
    """测试贡献度不足时投票被拒绝。"""
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    async def mock_get_contribution(*args: object, **kwargs: object) -> int:
        return 50

    monkeypatch.setattr(
        "app.core.player_client.PlayerContributionClient.get_contribution",
        mock_get_contribution,
    )

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-insufficient-contribution",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash_test",
            "weight": 1.0,
        },
    )
    assert response.status_code == 403
    data = response.json()
    assert data["code"] == VoteErrorCodes.INSUFFICIENT_CONTRIBUTION
    assert "贡献度不足" in data["message"]


@pytest.mark.asyncio
async def test_submit_vote_high_contribution_weight_multiplier(
    client: AsyncClient, open_vote_cycle: VoteCycle, monkeypatch
):
    """测试高贡献度玩家投票权重按倍率放大并受上限约束。"""
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[1]

    async def mock_get_contribution(*args: object, **kwargs: object) -> int:
        return 2500

    monkeypatch.setattr(
        "app.core.player_client.PlayerContributionClient.get_contribution",
        mock_get_contribution,
    )

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-high-contribution",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash_high",
            "weight": 2.5,
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["weight"] == 3.0
    assert data["weight_multiplier"] == 1.2
    assert data["contribution_points"] == 2500


@pytest.mark.asyncio
async def test_submit_vote_duplicate_rejected(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    first = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-vote-3a",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash1",
            "weight": 1.0,
        },
    )
    assert first.status_code == 201

    second = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-vote-3b",
        },
        json={
            "candidate_id": str(open_vote_cycle.candidates[1].candidate_id),
            "device_fingerprint_hash": "hash2",
            "weight": 1.0,
        },
    )
    assert second.status_code == 409
    data = second.json()
    assert data["code"] == VoteErrorCodes.ALREADY_VOTED


@pytest.mark.asyncio
async def test_submit_vote_idempotency_key(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]
    idempotency_key = "test-vote-idempotent-4"

    first = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": idempotency_key,
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash1",
        },
    )
    assert first.status_code == 201
    first_data = first.json()["data"]

    second = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": idempotency_key,
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash1",
        },
    )
    assert second.status_code == 200 or second.status_code == 201
    second_data = second.json()["data"]
    assert second_data["vote_id"] == first_data["vote_id"]


@pytest.mark.asyncio
async def test_submit_vote_candidate_not_found(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    fake_candidate_id = str(uuid.uuid4())

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-vote-5",
        },
        json={
            "candidate_id": fake_candidate_id,
            "device_fingerprint_hash": "hash",
        },
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == VoteErrorCodes.CANDIDATE_NOT_FOUND


@pytest.mark.asyncio
async def test_submit_vote_missing_token_returns_401(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试玩家接口缺少 JWT Token 返回 401。"""
    candidate = open_vote_cycle.candidates[0]

    response = await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            "Idempotency-Key": "test-vote-7",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_vote_history_empty(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["player_id"] == player_id
    assert data["total"] == 0
    assert data["votes"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_vote_history_returns_submitted_votes(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-history-1",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash_hist",
            "weight": 1.5,
        },
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["player_id"] == player_id
    assert data["total"] == 1
    assert len(data["votes"]) == 1
    vote = data["votes"][0]
    assert vote["candidate_id"] == str(candidate.candidate_id)
    assert vote["candidate_title"] == candidate.title
    assert vote["weight"] == 1.65
    assert "vote_id" in vote
    assert "created_at" in vote


@pytest.mark.asyncio
async def test_vote_history_missing_token_returns_401(client: AsyncClient):
    """测试投票历史接口缺少 JWT Token 返回 401。"""
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_vote_progress_returns_open_cycle(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试获取投票进度返回开放周期的进度数据。"""
    player_id = str(uuid.uuid4())
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current/progress",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert body["request_id"]
    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["chapter_id"] == "ch_prologue_01"
    assert data["status"] == "open"
    assert data["total_votes"] == 0
    assert data["total_weighted_votes"] == 0.0
    assert data["leading_candidate_id"] is None
    assert len(data["candidates"]) == 3


@pytest.mark.asyncio
async def test_get_vote_progress_after_votes_submitted(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试提交投票后获取进度数据。"""
    player_id1 = str(uuid.uuid4())
    player_id2 = str(uuid.uuid4())
    candidate1 = open_vote_cycle.candidates[0]
    candidate2 = open_vote_cycle.candidates[1]

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id1),
            "Idempotency-Key": "test-progress-1",
        },
        json={
            "candidate_id": str(candidate1.candidate_id),
            "device_fingerprint_hash": "hash_progress_1",
            "weight": 1.0,
        },
    )

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id2),
            "Idempotency-Key": "test-progress-2",
        },
        json={
            "candidate_id": str(candidate2.candidate_id),
            "device_fingerprint_hash": "hash_progress_2",
            "weight": 2.0,
        },
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current/progress",
        headers=_player_headers(player_id1),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_votes"] == 2
    assert data["total_weighted_votes"] > 0.0
    assert data["leading_candidate_id"] is not None


@pytest.mark.asyncio
async def test_get_vote_progress_no_open_cycle(client: AsyncClient):
    """测试没有开放投票周期时返回 404。"""
    player_id = str(uuid.uuid4())
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current/progress",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == VoteErrorCodes.NO_OPEN_VOTE_CYCLE


@pytest.mark.asyncio
async def test_get_vote_progress_missing_token_returns_401(client: AsyncClient):
    """测试投票进度接口缺少 JWT Token 返回 401。"""
    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current/progress",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_vote_progress_candidates_sorted_by_weighted_score(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试候选人按加权分数降序排列。"""
    player_id1 = str(uuid.uuid4())
    player_id2 = str(uuid.uuid4())
    player_id3 = str(uuid.uuid4())
    candidate1 = open_vote_cycle.candidates[0]
    candidate2 = open_vote_cycle.candidates[1]
    candidate3 = open_vote_cycle.candidates[2]

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id1),
            "Idempotency-Key": "test-sort-1",
        },
        json={
            "candidate_id": str(candidate1.candidate_id),
            "device_fingerprint_hash": "hash_sort_1",
            "weight": 1.0,
        },
    )

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id2),
            "Idempotency-Key": "test-sort-2",
        },
        json={
            "candidate_id": str(candidate2.candidate_id),
            "device_fingerprint_hash": "hash_sort_2",
            "weight": 3.0,
        },
    )

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id3),
            "Idempotency-Key": "test-sort-3",
        },
        json={
            "candidate_id": str(candidate3.candidate_id),
            "device_fingerprint_hash": "hash_sort_3",
            "weight": 2.0,
        },
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current/progress",
        headers=_player_headers(player_id1),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    candidates = data["candidates"]

    scores = [c["weighted_score"] for c in candidates]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_get_vote_progress_percentage_calculated_correctly(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试百分比计算正确。"""
    player_id1 = str(uuid.uuid4())
    player_id2 = str(uuid.uuid4())
    candidate1 = open_vote_cycle.candidates[0]
    candidate2 = open_vote_cycle.candidates[1]

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id1),
            "Idempotency-Key": "test-percent-1",
        },
        json={
            "candidate_id": str(candidate1.candidate_id),
            "device_fingerprint_hash": "hash_percent_1",
            "weight": 1.0,
        },
    )

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id2),
            "Idempotency-Key": "test-percent-2",
        },
        json={
            "candidate_id": str(candidate2.candidate_id),
            "device_fingerprint_hash": "hash_percent_2",
            "weight": 1.0,
        },
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/current/progress",
        headers=_player_headers(player_id1),
    )
    assert response.status_code == 200
    data = response.json()["data"]

    percentages = [c["percentage"] for c in data["candidates"] if c["vote_count"] > 0]
    assert abs(sum(percentages) - 100.0) < 0.01


# --- 图表数据接口测试 ---


@pytest.mark.asyncio
async def test_get_vote_result_chart_data_pie_success(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试获取饼图数据成功。"""
    player_id1 = str(uuid.uuid4())
    player_id2 = str(uuid.uuid4())
    candidate1 = open_vote_cycle.candidates[0]
    candidate2 = open_vote_cycle.candidates[1]

    # 提交投票
    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id1),
            "Idempotency-Key": "test-chart-1",
        },
        json={
            "candidate_id": str(candidate1.candidate_id),
            "device_fingerprint_hash": "hash_chart_1",
            "weight": 1.0,
        },
    )

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id2),
            "Idempotency-Key": "test-chart-2",
        },
        json={
            "candidate_id": str(candidate2.candidate_id),
            "device_fingerprint_hash": "hash_chart_2",
            "weight": 2.0,
        },
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{open_vote_cycle.vote_cycle_id}/chart-data",
        headers=_player_headers(player_id1),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]

    assert data["chart_type"] == "pie"
    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["total_votes"] == 2
    assert len(data["items"]) == 3  # 3个候选项

    # 检查颜色分配
    for item in data["items"]:
        assert "candidate_id" in item
        assert "candidate_name" in item
        assert "votes" in item
        assert "percentage" in item
        assert "color" in item
        assert item["color"].startswith("#")  # 颜色格式检查


@pytest.mark.asyncio
async def test_get_vote_result_chart_data_bar_success(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试获取柱状图数据成功。"""
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-chart-bar-1",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash_chart_bar_1",
            "weight": 1.0,
        },
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{open_vote_cycle.vote_cycle_id}/chart-data?chart_type=bar",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]

    assert data["chart_type"] == "bar"
    assert data["total_votes"] == 1


@pytest.mark.asyncio
async def test_get_vote_result_chart_data_not_found(client: AsyncClient):
    """测试投票周期不存在返回 404。"""
    player_id = str(uuid.uuid4())
    fake_cycle_id = uuid.uuid4()

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{fake_cycle_id}/chart-data",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == VoteErrorCodes.VOTE_CYCLE_NOT_FOUND


@pytest.mark.asyncio
async def test_get_vote_result_chart_data_permission_denied(client: AsyncClient):
    """测试权限校验失败返回 401。"""
    fake_cycle_id = uuid.uuid4()

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{fake_cycle_id}/chart-data",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_vote_result_chart_data_color_assignment(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试颜色数组正确分配。"""
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-chart-color-1",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash_chart_color_1",
            "weight": 1.0,
        },
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{open_vote_cycle.vote_cycle_id}/chart-data",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    data = response.json()["data"]

    # 检查每个候选项都分配了颜色
    colors = [item["color"] for item in data["items"]]
    assert len(colors) == len(data["items"])


# --- 投票复盘报告接口测试 ---


def _make_content_package_info(
    vote_cycle_id: uuid.UUID,
    payload: dict[str, object] | None = None,
) -> ContentPackageInfo:
    """构造用于 mock 的内容包信息对象。"""
    from datetime import datetime, timezone

    return ContentPackageInfo(
        content_package_id=uuid.uuid4(),
        vote_cycle_id=vote_cycle_id,
        chapter_id="ch_prologue_01",
        title="测试落地内容包",
        version="pkg_ch01_20260701_01",
        status="live",
        affected_regions=["region_wasteland_01"],
        payload=payload or {
            "npcs": [{"name": "测试NPC"}],
            "quests": [{"title": "测试任务"}],
            "regions": [{"name": "废土区域"}],
        },
        summary="测试内容包摘要",
        landed_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_get_vote_review_not_found(client: AsyncClient):
    """测试投票周期不存在时复盘报告返回 404。"""
    player_id = str(uuid.uuid4())
    fake_cycle_id = uuid.uuid4()

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{fake_cycle_id}/review",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == VoteErrorCodes.VOTE_CYCLE_NOT_FOUND


@pytest.mark.asyncio
async def test_get_vote_review_missing_token_returns_401(client: AsyncClient):
    """测试复盘报告接口缺少 JWT Token 返回 401。"""
    fake_cycle_id = uuid.uuid4()

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{fake_cycle_id}/review",
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_vote_review_open_cycle_without_votes(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试开放周期无投票时复盘报告返回基本数据。"""
    player_id = str(uuid.uuid4())

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{open_vote_cycle.vote_cycle_id}/review",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    body = response.json()
    data = body["data"]

    assert body["request_id"]
    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["chapter_id"] == "ch_prologue_01"
    assert data["status"] == "open"
    assert data["total_votes"] == 0
    assert data["total_weighted_votes"] == 0.0
    assert data["participation_rate"] == 0.0
    assert data["winning_candidate"] is None
    assert len(data["candidates"]) == 3
    for candidate in data["candidates"]:
        assert "candidate_id" in candidate
        assert "title" in candidate
        assert "vote_count" in candidate
        assert "weighted_score" in candidate
        assert "percentage" in candidate


@pytest.mark.asyncio
async def test_get_vote_review_after_votes_submitted(
    client: AsyncClient, open_vote_cycle: VoteCycle
):
    """测试提交投票后复盘报告返回正确的获胜候选与统计。"""
    player_id1 = str(uuid.uuid4())
    player_id2 = str(uuid.uuid4())
    candidate1 = open_vote_cycle.candidates[0]
    candidate2 = open_vote_cycle.candidates[1]

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id1),
            "Idempotency-Key": "test-review-1",
        },
        json={
            "candidate_id": str(candidate1.candidate_id),
            "device_fingerprint_hash": "hash_review_1",
            "weight": 1.0,
        },
    )

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id2),
            "Idempotency-Key": "test-review-2",
        },
        json={
            "candidate_id": str(candidate2.candidate_id),
            "device_fingerprint_hash": "hash_review_2",
            "weight": 3.0,
        },
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{open_vote_cycle.vote_cycle_id}/review",
        headers=_player_headers(player_id1),
    )
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["total_votes"] == 2
    assert data["total_weighted_votes"] > 0.0
    assert data["winning_candidate"] is not None
    assert data["winning_candidate"]["candidate_id"] == str(candidate2.candidate_id)
    assert data["winning_candidate"]["title"] == candidate2.title

    candidate_ids = {c["candidate_id"] for c in data["candidates"]}
    assert str(candidate1.candidate_id) in candidate_ids
    assert str(candidate2.candidate_id) in candidate_ids


@pytest.mark.asyncio
async def test_get_vote_review_with_content_package(
    client: AsyncClient, open_vote_cycle: VoteCycle, monkeypatch
):
    """测试复盘报告正确关联并展示内容包摘要。"""
    player_id = str(uuid.uuid4())
    candidate = open_vote_cycle.candidates[0]

    await client.post(
        f"{settings.api_v1_prefix}/votes/submit",
        headers={
            **_player_headers(player_id),
            "Idempotency-Key": "test-review-pkg-1",
        },
        json={
            "candidate_id": str(candidate.candidate_id),
            "device_fingerprint_hash": "hash_review_pkg_1",
            "weight": 2.0,
        },
    )

    mock_pkg = _make_content_package_info(
        vote_cycle_id=open_vote_cycle.vote_cycle_id,
        payload={
            "gray_scope": {"player_percent": 10},
            "npcs": [{"name": "测试NPC"}],
            "quests": [{"title": "测试任务"}],
        },
    )

    async def mock_get_content_package_by_vote_cycle(
        self: object, vote_cycle_id: uuid.UUID, authorization: str | None = None
    ) -> ContentPackageInfo:
        return mock_pkg

    monkeypatch.setattr(
        "app.core.content_client.ContentPackageClient.get_content_package_by_vote_cycle",
        mock_get_content_package_by_vote_cycle,
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{open_vote_cycle.vote_cycle_id}/review",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["content_package"] is not None
    content_package = data["content_package"]
    assert content_package["title"] == "测试落地内容包"
    assert content_package["package_version"] == "pkg_ch01_20260701_01"
    assert content_package["status"] == "live"
    assert "region_wasteland_01" in content_package["affected_regions"]
    assert "npcs" in content_package["payload"]

    # 参与率应基于 gray_scope 中的 player_percent=10% 估算（总玩家数 10000）
    assert data["participation_rate"] > 0.0


@pytest.mark.asyncio
async def test_get_vote_review_content_package_error_ignored(
    client: AsyncClient, open_vote_cycle: VoteCycle, monkeypatch
):
    """测试内容服务异常时复盘报告仍返回投票数据（内容包字段为 None）。"""
    player_id = str(uuid.uuid4())

    async def mock_raise_error(
        self: object, vote_cycle_id: uuid.UUID, authorization: str | None = None
    ) -> ContentPackageInfo:
        raise RuntimeError("content service unavailable")

    monkeypatch.setattr(
        "app.core.content_client.ContentPackageClient.get_content_package_by_vote_cycle",
        mock_raise_error,
    )

    response = await client.get(
        f"{settings.api_v1_prefix}/votes/history/{open_vote_cycle.vote_cycle_id}/review",
        headers=_player_headers(player_id),
    )
    assert response.status_code == 200
    data = response.json()["data"]

    assert data["vote_cycle_id"] == str(open_vote_cycle.vote_cycle_id)
    assert data["content_package"] is None
    assert data["participation_rate"] == 0.0
