from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # Database
    database_url: str = Field(default="sqlite:///./wholesale.db", env="DATABASE_URL")
    postgres_url: str = Field(default="", env="POSTGRES_URL")

    # Naver API
    naver_client_id: str = Field(default="", env="NAVER_CLIENT_ID")
    naver_client_secret: str = Field(default="", env="NAVER_CLIENT_SECRET")
    naver_datalab_key: str = Field(default="", env="NAVER_DATALAB_KEY")

    # Coupang API
    coupang_access_key: str = Field(default="", env="COUPANG_ACCESS_KEY")
    coupang_secret_key: str = Field(default="", env="COUPANG_SECRET_KEY")
    coupang_vendor_id: str = Field(default="", env="COUPANG_VENDOR_ID")

    # Telegram
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", env="TELEGRAM_CHAT_ID")

    # Google Cloud
    gcs_bucket_name: str = Field(default="", env="GCS_BUCKET_NAME")
    google_application_credentials: str = Field(default="./service_account.json", env="GOOGLE_APPLICATION_CREDENTIALS")
    google_sheets_id: str = Field(default="", env="GOOGLE_SHEETS_ID")

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", env="CELERY_RESULT_BACKEND")

    # App Settings
    secret_key: str = Field(default="changeme-secret-key", env="SECRET_KEY")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")

    # Business Logic
    min_margin_percent: float = Field(default=20.0, env="MIN_MARGIN_PERCENT")
    daily_budget: int = Field(default=500000, env="DAILY_BUDGET")
    naver_fee_rate: float = Field(default=0.055, env="NAVER_FEE_RATE")
    coupang_fee_rate: float = Field(default=0.108, env="COUPANG_FEE_RATE")
    shipping_cost: int = Field(default=3000, env="SHIPPING_COST")
    golden_keyword_ratio: float = Field(default=10.0, env="GOLDEN_KEYWORD_RATIO")
    cash_warning_threshold: int = Field(default=100000, env="CASH_WARNING_THRESHOLD")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
