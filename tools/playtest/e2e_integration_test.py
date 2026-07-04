import asyncio
import json
import uuid
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone


async def test_vote_cycle_full_flow(mock_redis, mock_db_sessions):
    """测试完整投票周期流程：创建→计划→开放→提交→关闭→结算"""
    from services.vote.app.api.routes import create_vote_cycle, schedule_vote_cycle, open_vote_cycle, close_vote_cycle, finalize_vote_cycle
    from services.vote.app.api.routes import submit_vote, get_current_vote_cycle
    from services.vote.app.schemas.vote import VoteCycleCreate, VoteSubmit, VoteCandidateCreate
    from services.vote.app.core.deps import get_db, get_redis
    from fastapi.testclient import TestClient
    from services.vote.app.main import app
    
    client = TestClient(app)
    
    with patch("services.vote.app.core.deps.get_db", return_value=mock_db_sessions["vote"]):
        with patch("services.vote.app.core.deps.get_redis", return_value=mock_redis):
            cycle_data = {
                "chapter_id": "chapter_01",
                "title": "Test Vote Cycle",
                "description": "Test cycle for e2e integration",
                "start_time": (datetime.now(timezone.utc)).isoformat(),
                "end_time": (datetime.now(timezone.utc).replace(hour=datetime.now(timezone.utc).hour + 24)).isoformat(),
            }
            
            response = client.post("/api/v1/ops/vote-cycles", json=cycle_data)
            assert response.status_code == 200
            cycle_id = response.json()["data"]["vote_cycle_id"]
            
            assert response.json()["data"]["status"] == "draft"
            
            response = client.post(f"/api/v1/ops/vote-cycles/{cycle_id}/schedule")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "scheduled"
            
            response = client.post(f"/api/v1/ops/vote-cycles/{cycle_id}/open")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "open"
            
            response = client.get("/api/v1/votes/current")
            assert response.status_code == 200
            assert response.json()["data"]["vote_cycle_id"] == cycle_id
            
            candidate_data = {
                "vote_cycle_id": cycle_id,
                "title": "Candidate A",
                "description": "First candidate",
                "impact_summary": "Impact A",
                "estimated_effort": "low",
            }
            response = client.post(f"/api/v1/ops/vote-cycles/{cycle_id}/candidates", json=candidate_data)
            assert response.status_code == 200
            candidate_id = response.json()["data"]["candidate_id"]
            
            vote_data = {
                "candidate_id": candidate_id,
                "player_id": str(uuid.uuid4()),
                "weight": 1.0,
            }
            response = client.post("/api/v1/votes/submit", json=vote_data)
            assert response.status_code == 200
            
            response = client.post(f"/api/v1/ops/vote-cycles/{cycle_id}/close")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "closed"
            
            response = client.post(f"/api/v1/ops/vote-cycles/{cycle_id}/finalize")
            assert response.status_code == 200
            assert response.json()["data"]["status"] == "finalized"
            
            print(f"✓ 投票周期完整流程测试通过: {cycle_id}")


async def test_event_bus_integration(mock_redis):
    """测试事件总线发布/订阅集成"""
    from workers.events.event_bus import EventBus
    from workers.events.schemas import VoteResultFinalizedEvent
    
    event_bus = EventBus(mock_redis)
    
    received_events = []
    async def handler(event_data):
        received_events.append(event_data)
    
    await event_bus.subscribe("vote.result.finalized", handler)
    
    test_event = VoteResultFinalizedEvent(
        event_id=str(uuid.uuid4()),
        trace_id="trace_test",
        cycle_id=str(uuid.uuid4()),
        winning_candidate_id=str(uuid.uuid4()),
        total_votes=100,
        occurred_at=datetime.now(timezone.utc),
    )
    
    await event_bus.publish("vote.result.finalized", test_event.model_dump())
    
    await asyncio.sleep(0.1)
    
    assert len(received_events) == 1
    assert received_events[0]["event_id"] == test_event.event_id
    assert received_events[0]["cycle_id"] == test_event.cycle_id
    assert received_events[0]["winning_candidate_id"] == test_event.winning_candidate_id
    
    print("✓ 事件总线发布/订阅测试通过")


async def test_content_package_flow(mock_db_sessions):
    """测试内容包创建→发布→回滚流程"""
    from services.content.app.api.routes import create_content_package, release_content_package, rollback_content_package
    from services.content.app.schemas.content import ContentPackageCreate, ReleaseRequest, RollbackRequest
    from services.content.app.core.deps import get_db
    from fastapi.testclient import TestClient
    from services.content.app.main import app
    
    client = TestClient(app)
    
    with patch("services.content.app.core.deps.get_db", return_value=mock_db_sessions["content"]):
        package_data = {
            "chapter_id": "chapter_01",
            "title": "Test Content Package",
            "summary": "Test package for e2e",
            "package_version": "pkg_test_e2e_20260705_01",
            "payload": {
                "schema_version": 1,
                "package_type": "region",
                "release_notes": "Test release",
            },
        }
        
        response = client.post("/api/v1/ops/content-packages", json=package_data)
        assert response.status_code == 200
        package_id = response.json()["data"]["content_package_id"]
        
        assert response.json()["data"]["status"] == "packaged"
        
        release_data = {
            "release_mode": "gray",
            "gray_scope": {
                "player_percent": 10,
            },
        }
        response = client.post(f"/api/v1/ops/content-packages/{package_id}/release", json=release_data)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "gray"
        
        rollback_data = {"reason": "Test rollback"}
        response = client.post(f"/api/v1/ops/content-packages/{package_id}/rollback", json=rollback_data)
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "rolled_back"
        
        print(f"✓ 内容包创建→发布→回滚流程测试通过: {package_id}")


async def main():
    """端到端集成测试主入口"""
    print("=" * 60)
    print("端到端集成测试")
    print("=" * 60)
    
    mock_redis = MagicMock()
    mock_redis.publish = AsyncMock(return_value=1)
    mock_redis.subscribe = AsyncMock(return_value=AsyncMock())
    
    mock_db_sessions = {
        "vote": AsyncMock(),
        "content": AsyncMock(),
    }
    
    print("\n1. 测试投票周期完整流程...")
    await test_vote_cycle_full_flow(mock_redis, mock_db_sessions)
    
    print("\n2. 测试事件总线发布/订阅集成...")
    await test_event_bus_integration(mock_redis)
    
    print("\n3. 测试内容包创建→发布→回滚流程...")
    await test_content_package_flow(mock_db_sessions)
    
    print("\n" + "=" * 60)
    print("所有端到端集成测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())