import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def mock_settings():
    with patch("workers.config.settings") as mock:
        mock.broker_url = "redis://localhost:6379/0"
        mock.result_backend = "redis://localhost:6379/1"
        mock.result_expires = 86400
        mock.task_serializer = "json"
        mock.accept_content = ["json"]
        mock.result_serializer = "json"
        mock.timezone = "UTC"
        mock.enable_utc = True
        mock.worker_prefetch_multiplier = 1
        mock.worker_max_tasks_per_child = 1000
        mock.generation_service_url = "http://localhost:8003"
        mock.review_service_url = "http://localhost:8004"
        mock.content_service_url = "http://localhost:8002"
        mock.world_service_url = "http://localhost:8001"
        mock.database_url = "sqlite+aiosqlite:///:memory:"
        mock.jwt_secret = "test-secret"
        mock.jwt_algorithm = "HS256"
        mock.log_level = "DEBUG"
        mock.debug = False
        mock.access_token_expire_minutes = 30
        yield mock


@pytest.fixture(autouse=True)
def celery_eager_mode():
    from workers.celery_app import app
    original_always_eager = app.conf.task_always_eager
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    yield
    app.conf.task_always_eager = original_always_eager
    app.conf.task_eager_propagates = False


@pytest.fixture
def mock_http_client():
    mock_client = MagicMock()
    mock_client.post = AsyncMock()
    mock_client.get = AsyncMock()
    mock_client.put = AsyncMock()
    mock_client.patch = AsyncMock()
    mock_client.delete = AsyncMock()
    return mock_client


@pytest.fixture
def mock_audit_log():
    with patch("workers.clients.db_client.write_audit_log") as mock:
        yield mock
