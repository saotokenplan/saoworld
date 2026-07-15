"""用户反馈 API 测试。"""

import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.auth import create_test_token
from app.core.errors import OpsErrorCodes
from app.schemas.auth import Role


@pytest_asyncio.fixture
def ops_token() -> str:
    """运营角色 Token。"""
    return create_test_token(
        user_id="test_ops_user",
        role=Role.OPS,
    )


@pytest.mark.asyncio
async def test_submit_feedback_success(async_client: AsyncClient, player_token: str) -> None:
    """测试成功提交反馈。"""
    response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "bug",
            "title": "测试Bug反馈",
            "content": "发现一个Bug",
            "priority": "medium",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_test_001",
            "X-Trace-Id": "trace_test_001",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert data["data"]["feedback_type"] == "bug"
    assert data["data"]["title"] == "测试Bug反馈"
    assert data["data"]["content"] == "发现一个Bug"
    assert data["data"]["priority"] == "medium"
    assert data["data"]["status"] == "pending"
    assert "feedback_id" in data["data"]


@pytest.mark.asyncio
async def test_submit_feedback_with_optional_fields(async_client: AsyncClient, player_token: str) -> None:
    """测试提交带可选字段的反馈。"""
    response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "suggestion",
            "title": "新功能建议",
            "content": "希望增加新功能",
            "priority": "low",
            "region_id": "region_wasteland_01",
            "chapter_id": "chapter_01",
            "attachment_urls": ["https://example.com/image.png"],
            "metadata": {"platform": "windows"},
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_test_002",
            "X-Trace-Id": "trace_test_002",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["data"]["region_id"] == "region_wasteland_01"
    assert data["data"]["chapter_id"] == "chapter_01"
    assert data["data"]["attachment_urls"] == ["https://example.com/image.png"]
    assert data["data"]["metadata_jsonb"] == {"platform": "windows"}


@pytest.mark.asyncio
async def test_submit_feedback_invalid_type(async_client: AsyncClient, player_token: str) -> None:
    """测试无效的反馈类型。"""
    response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "invalid_type",
            "title": "测试",
            "content": "内容",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_test_003",
        },
    )

    assert response.status_code == 400
    data = response.json()
    # FastAPI HTTPException wraps error in "detail"
    assert "code" in data or ("detail" in data and "code" in data["detail"])
    if "detail" in data:
        assert data["detail"]["code"] == OpsErrorCodes.INVALID_FEEDBACK_TYPE
    else:
        assert data["code"] == OpsErrorCodes.INVALID_FEEDBACK_TYPE


@pytest.mark.asyncio
async def test_submit_feedback_invalid_priority(async_client: AsyncClient, player_token: str) -> None:
    """测试无效的优先级。"""
    response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "bug",
            "title": "测试",
            "content": "内容",
            "priority": "invalid_priority",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_test_004",
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert "code" in data or ("detail" in data and "code" in data["detail"])
    if "detail" in data:
        assert data["detail"]["code"] == OpsErrorCodes.INVALID_ARGUMENT
    else:
        assert data["code"] == OpsErrorCodes.INVALID_ARGUMENT


@pytest.mark.asyncio
async def test_submit_feedback_unauthorized(async_client: AsyncClient) -> None:
    """测试未授权提交反馈。"""
    response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "bug",
            "title": "测试",
            "content": "内容",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_feedback_success(async_client: AsyncClient, ops_token: str, player_token: str) -> None:
    """测试运营列表查询反馈。"""
    # 先提交一个反馈
    await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "bug",
            "title": "测试反馈",
            "content": "测试内容",
            "priority": "high",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_list_001",
        },
    )

    # 查询列表
    response = await async_client.get(
        "/api/v1/ops/feedback",
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "data" in data
    assert "feedbacks" in data["data"]
    assert "total" in data["data"]
    assert "limit" in data["data"]
    assert "offset" in data["data"]


@pytest.mark.asyncio
async def test_list_feedback_with_filters(async_client: AsyncClient, ops_token: str, player_token: str) -> None:
    """测试带过滤条件的反馈列表查询。"""
    # 提交不同类型的反馈
    await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "bug",
            "title": "Bug反馈",
            "content": "Bug内容",
            "priority": "high",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_filter_001",
        },
    )

    await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "suggestion",
            "title": "建议反馈",
            "content": "建议内容",
            "priority": "medium",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_filter_002",
        },
    )

    # 按类型过滤
    response = await async_client.get(
        "/api/v1/ops/feedback?feedback_type=bug",
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert all(f["feedback_type"] == "bug" for f in data["data"]["feedbacks"])


@pytest.mark.asyncio
async def test_get_feedback_success(async_client: AsyncClient, ops_token: str, player_token: str) -> None:
    """测试运营查询反馈详情。"""
    # 先提交一个反馈
    submit_response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "question",
            "title": "问题反馈",
            "content": "问题描述",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_detail_001",
        },
    )
    feedback_id = submit_response.json()["data"]["feedback_id"]

    # 查询详情
    response = await async_client.get(
        f"/api/v1/ops/feedback/{feedback_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["feedback_id"] == feedback_id
    assert data["data"]["title"] == "问题反馈"


@pytest.mark.asyncio
async def test_get_feedback_not_found(async_client: AsyncClient, ops_token: str) -> None:
    """测试查询不存在的反馈。"""
    fake_id = str(uuid.uuid4())
    response = await async_client.get(
        f"/api/v1/ops/feedback/{fake_id}",
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    assert response.status_code == 404
    data = response.json()
    assert "code" in data or ("detail" in data and "code" in data["detail"])
    if "detail" in data:
        assert data["detail"]["code"] == OpsErrorCodes.FEEDBACK_NOT_FOUND
    else:
        assert data["code"] == OpsErrorCodes.FEEDBACK_NOT_FOUND


@pytest.mark.asyncio
async def test_update_feedback_status(async_client: AsyncClient, ops_token: str, player_token: str) -> None:
    """测试更新反馈状态。"""
    # 先提交一个反馈
    submit_response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "bug",
            "title": "待处理Bug",
            "content": "待处理内容",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_update_001",
        },
    )
    feedback_id = submit_response.json()["data"]["feedback_id"]

    # 更新状态为处理中
    response = await async_client.patch(
        f"/api/v1/ops/feedback/{feedback_id}",
        json={
            "status": "in_progress",
        },
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_feedback_resolve(async_client: AsyncClient, ops_token: str, player_token: str) -> None:
    """测试解决反馈。"""
    # 先提交一个反馈
    submit_response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "bug",
            "title": "待解决Bug",
            "content": "待解决内容",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_resolve_001",
        },
    )
    feedback_id = submit_response.json()["data"]["feedback_id"]

    # 更新状态为已解决
    response = await async_client.patch(
        f"/api/v1/ops/feedback/{feedback_id}",
        json={
            "status": "resolved",
            "resolution_note": "问题已修复",
        },
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "resolved"
    assert data["data"]["resolution_note"] == "问题已修复"
    assert data["data"]["resolved_by"] is not None


@pytest.mark.asyncio
async def test_update_feedback_priority(async_client: AsyncClient, ops_token: str, player_token: str) -> None:
    """测试更新反馈优先级。"""
    # 先提交一个反馈
    submit_response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "bug",
            "title": "优先级测试",
            "content": "优先级测试内容",
            "priority": "medium",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_priority_001",
        },
    )
    feedback_id = submit_response.json()["data"]["feedback_id"]

    # 更新优先级
    response = await async_client.patch(
        f"/api/v1/ops/feedback/{feedback_id}",
        json={
            "priority": "critical",
        },
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data"]["priority"] == "critical"


@pytest.mark.asyncio
async def test_update_feedback_invalid_status(async_client: AsyncClient, ops_token: str, player_token: str) -> None:
    """测试无效的状态更新。"""
    # 先提交一个反馈
    submit_response = await async_client.post(
        "/api/v1/feedback",
        json={
            "feedback_type": "bug",
            "title": "状态测试",
            "content": "状态测试内容",
        },
        headers={
            "Authorization": f"Bearer {player_token}",
            "X-Player-Id": "player_status_001",
        },
    )
    feedback_id = submit_response.json()["data"]["feedback_id"]

    # 更新为无效状态
    response = await async_client.patch(
        f"/api/v1/ops/feedback/{feedback_id}",
        json={
            "status": "invalid_status",
        },
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    assert response.status_code == 400
    data = response.json()
    assert "code" in data or ("detail" in data and "code" in data["detail"])
    if "detail" in data:
        assert data["detail"]["code"] == OpsErrorCodes.INVALID_FEEDBACK_STATUS
    else:
        assert data["code"] == OpsErrorCodes.INVALID_FEEDBACK_STATUS


@pytest.mark.asyncio
async def test_get_feedback_stats(async_client: AsyncClient, ops_token: str, player_token: str) -> None:
    """测试查询反馈统计。"""
    # 提交不同类型的反馈
    for ft in ["bug", "suggestion", "question", "other"]:
        await async_client.post(
            "/api/v1/feedback",
            json={
                "feedback_type": ft,
                "title": f"{ft}反馈",
                "content": f"{ft}内容",
            },
            headers={
                "Authorization": f"Bearer {player_token}",
                "X-Player-Id": f"player_stats_{ft}",
            },
        )

    # 查询统计
    response = await async_client.get(
        "/api/v1/ops/feedback/stats",
        headers={"Authorization": f"Bearer {ops_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "total" in data["data"]
    assert "pending" in data["data"]
    assert "in_progress" in data["data"]
    assert "resolved" in data["data"]
    assert "closed" in data["data"]
    assert "by_type" in data["data"]
    assert "by_priority" in data["data"]


@pytest.mark.asyncio
async def test_list_feedback_unauthorized(async_client: AsyncClient) -> None:
    """测试未授权查询反馈列表。"""
    response = await async_client.get("/api/v1/ops/feedback")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_feedback_forbidden(async_client: AsyncClient, player_token: str) -> None:
    """测试普通玩家无权查询运营接口。"""
    response = await async_client.get(
        "/api/v1/ops/feedback",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert response.status_code == 403