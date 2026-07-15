from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REVIEW_", case_sensitive=False)

    app_name: str = "review-service"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "local"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/review_db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    log_level: str = "INFO"
    request_id_header: str = "X-Request-Id"
    trace_id_header: str = "X-Trace-Id"
    idempotency_key_header: str = "Idempotency-Key"

    api_v1_prefix: str = "/api/v1"

    allowed_origins: list[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]


settings = Settings()

if settings.jwt_secret == "change-me-in-production" and settings.environment not in ("local", "test"):
    raise ValueError("REVIEW_JWT_SECRET 必须在环境变量中设置，禁止使用默认值")
