from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPS_", case_sensitive=False)

    app_name: str = "ops-service"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "local"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ops_db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    log_level: str = "INFO"
    request_id_header: str = "X-Request-Id"
    trace_id_header: str = "X-Trace-Id"
    idempotency_key_header: str = "Idempotency-Key"

    api_v1_prefix: str = "/api/v1"

    vote_service_url: str = "http://localhost:8000"
    world_service_url: str = "http://localhost:8001"
    content_service_url: str = "http://localhost:8002"
    generation_service_url: str = "http://localhost:8003"
    review_service_url: str = "http://localhost:8004"
    gateway_service_url: str = "http://localhost:8005"
    player_service_url: str = "http://localhost:8006"
    ops_service_url: str = "http://localhost:8007"

    health_check_timeout: int = 5


settings = Settings()
