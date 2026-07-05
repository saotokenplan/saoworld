from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GATEWAY_", case_sensitive=False)

    app_name: str = "gateway-service"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "local"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    rate_limit_requests_per_minute: int = 60
    rate_limit_concurrent_requests: int = 100

    request_timeout: int = 30

    log_level: str = "INFO"
    request_id_header: str = "X-Request-Id"
    trace_id_header: str = "X-Trace-Id"
    idempotency_key_header: str = "Idempotency-Key"

    api_v1_prefix: str = "/api/v1"

    vote_service_url: str = "http://localhost:8001"
    world_service_url: str = "http://localhost:8002"
    content_service_url: str = "http://localhost:8003"
    generation_service_url: str = "http://localhost:8004"
    review_service_url: str = "http://localhost:8005"
    player_service_url: str = "http://localhost:8006"
    ops_service_url: str = "http://localhost:8007"


settings = Settings()