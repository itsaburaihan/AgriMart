"""Application settings, loaded from environment / .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "AgriMart"
    # PostgreSQL in production (see .env.example / docker-compose.yml).
    # SQLite file is the local-dev default so the API runs without Postgres.
    database_url: str = "sqlite:///./agrimart.db"
    secret_key: str = "change-me-to-a-long-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours

    # Manual bKash / Nagad merchant numbers shown to customers at checkout.
    bkash_number: str = "01736439950"
    nagad_number: str = ""


settings = Settings()
