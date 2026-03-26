# config/settings.py
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./wholesale.db")

    # Naver API
    NAVER_CLIENT_ID: str = os.getenv("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET: str = os.getenv("NAVER_CLIENT_SECRET", "")
    NAVER_DATALAB_CLIENT_ID: str = os.getenv("NAVER_DATALAB_CLIENT_ID", "")
    NAVER_DATALAB_CLIENT_SECRET: str = os.getenv("NAVER_DATALAB_CLIENT_SECRET", "")
    NAVER_SHOPPING_API_KEY: str = os.getenv("NAVER_SHOPPING_API_KEY", "")

    # Coupang API
    COUPANG_ACCESS_KEY: str = os.getenv("COUPANG_ACCESS_KEY", "")
    COUPANG_SECRET_KEY: str = os.getenv("COUPANG_SECRET_KEY", "")
    COUPANG_VENDOR_ID: str = os.getenv("COUPANG_VENDOR_ID", "")

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CEO_CHAT_ID: str = os.getenv("TELEGRAM_CEO_CHAT_ID", "")

    # Google Cloud Storage
    GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "wholesale-products")
    GCS_CREDENTIALS_PATH: str = os.getenv("GCS_CREDENTIALS_PATH", "credentials/gcs-key.json")

    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_PATH: str = os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH", "credentials/sheets-key.json")
    GOOGLE_SHEETS_SPREADSHEET_ID: str = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "")

    # OpenAI (for AI features)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Celery / Redis
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

    # Application
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")

    # Sourcing
    DAILY_SOURCING_TARGET: int = int(os.getenv("DAILY_SOURCING_TARGET", "500"))
    GOLDEN_KEYWORD_THRESHOLD: float = float(os.getenv("GOLDEN_KEYWORD_THRESHOLD", "10.0"))
    MIN_MARGIN_PERCENT: float = float(os.getenv("MIN_MARGIN_PERCENT", "20.0"))

    # Budget
    INITIAL_DAILY_BUDGET: int = int(os.getenv("INITIAL_DAILY_BUDGET", "1000000"))  # 1M KRW

    # Wholesaler credentials
    DAEMAETOPIA_USERNAME: str = os.getenv("DAEMAETOPIA_USERNAME", "")
    DAEMAETOPIA_PASSWORD: str = os.getenv("DAEMAETOPIA_PASSWORD", "")
    EASYMARKET_USERNAME: str = os.getenv("EASYMARKET_USERNAME", "")
    EASYMARKET_PASSWORD: str = os.getenv("EASYMARKET_PASSWORD", "")
    DAEMAEPARTNER_USERNAME: str = os.getenv("DAEMAEPARTNER_USERNAME", "")
    DAEMAEPARTNER_PASSWORD: str = os.getenv("DAEMAEPARTNER_PASSWORD", "")
    SINSANG_USERNAME: str = os.getenv("SINSANG_USERNAME", "")
    SINSANG_PASSWORD: str = os.getenv("SINSANG_PASSWORD", "")
    MURRAYKOREA_USERNAME: str = os.getenv("MURRAYKOREA_USERNAME", "")
    MURRAYKOREA_PASSWORD: str = os.getenv("MURRAYKOREA_PASSWORD", "")
    DALGOLMART_USERNAME: str = os.getenv("DALGOLMART_USERNAME", "")
    DALGOLMART_PASSWORD: str = os.getenv("DALGOLMART_PASSWORD", "")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
