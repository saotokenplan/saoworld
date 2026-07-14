from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VOTE_", case_sensitive=False)

    app_name: str = "vote-service"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "local"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/vote_db"

    jwt_secret: str = "test-secret-key-for-testing-only"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    log_level: str = "INFO"
    request_id_header: str = "X-Request-Id"
    trace_id_header: str = "X-Trace-Id"
    idempotency_key_header: str = "Idempotency-Key"

    api_v1_prefix: str = "/api/v1"

    # 玩家服务与投票资格配置
    player_service_url: str = "http://localhost:8001"
    player_service_timeout_seconds: float = 3.0
    contribution_threshold: int = 100

    # 内容服务配置
    content_service_url: str = "http://localhost:8003"
    content_service_timeout_seconds: float = 5.0

    # CORS 配置
    allowed_origins: list[str] = ["http://localhost:8080", "http://127.0.0.1:8080"]

    # 异常检测配置
    anomaly_frequency_window_seconds: int = 300
    anomaly_frequency_threshold: int = 3
    anomaly_device_multi_player_threshold: int = 2
    anomaly_weight_high_threshold: float = 8.0
    anomaly_weight_critical_threshold: float = 9.5
    anomaly_time_window_seconds: int = 60
    anomaly_time_surge_threshold: int = 10


settings = Settings()

if settings.jwt_secret == "change-me-in-production":
    raise ValueError("JWT_SECRET 必须在环境变量中设置，禁止使用默认值")
