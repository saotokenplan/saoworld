from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORKER_", case_sensitive=False)

    app_name: str = "game-workers"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "local"

    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"
    result_expires: int = 86400

    task_serializer: str = "json"
    accept_content: list[str] = ["json"]
    result_serializer: str = "json"
    timezone: str = "UTC"

    worker_prefetch_multiplier: int = 1
    worker_max_tasks_per_child: int = 1000

    vote_service_url: str = "http://localhost:8000"
    world_service_url: str = "http://localhost:8001"
    content_service_url: str = "http://localhost:8002"
    generation_service_url: str = "http://localhost:8003"
    review_service_url: str = "http://localhost:8004"
    player_service_url: str = "http://localhost:8005"
    ops_service_url: str = "http://localhost:8006"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/workers_db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    log_level: str = "INFO"
    trace_id_header: str = "X-Trace-Id"


settings = WorkerSettings()