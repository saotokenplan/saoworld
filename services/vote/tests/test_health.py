import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.db import get_db
from app.main import app


async def override_get_db():
    yield None


@pytest.fixture
def client_without_db():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"{settings.api_v1_prefix}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == settings.app_name
    assert data["version"] == settings.app_version
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_get_current_vote_no_cycle_db_error(client_without_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"{settings.api_v1_prefix}/votes/current")
    assert response.status_code == 500
    data = response.json()
    assert data["code"] == "INTERNAL_ERROR"
