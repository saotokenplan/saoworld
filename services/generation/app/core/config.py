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

    allowed_origins: list[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]

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

    # 成本控制配置
    cost_daily_budget_tokens: int = 1000000  # 每日 Token 预算
    cost_monthly_budget_tokens: int = 30000000  # 每月 Token 预算
    cost_alert_threshold_ratio: float = 0.8  # 告警阈值比例（预算的百分比）
    cost_pause_threshold_ratio: float = 0.95  # 暂停生成阈值比例
    cost_model_price_per_1k_prompt_tokens: float = 0.00015  # 每1000个提示词Token的价格（美元）
    cost_model_price_per_1k_completion_tokens: float = 0.0006  # 每1000个完成Token的价格（美元）


settings = Settings()

if settings.jwt_secret == "change-me-in-production" and settings.environment not in ("local", "test"):
    raise ValueError("GENERATION_JWT_SECRET 必须在环境变量中设置，禁止使用默认值")
