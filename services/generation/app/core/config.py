from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GENERATION_", case_sensitive=False)

    app_name: str = "generation-service"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "local"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/generation_db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    log_level: str = "INFO"
    request_id_header: str = "X-Request-Id"
    trace_id_header: str = "X-Trace-Id"
    idempotency_key_header: str = "Idempotency-Key"

    api_v1_prefix: str = "/api/v1"

    template_dir: str = "templates"
    quality_threshold: float = 0.75

    # LLM 配置
    llm_provider: str = "mock"  # openai / mock
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str | None = None  # 可选的 API 基础 URL
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.7
    llm_timeout: int = 60  # 秒


settings = Settings()
