import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    PROJECT_NAME: str = "Veyra Voice"
    API_V1_STR: str = "/api/v1"

    # Server Host and CORS
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3003",
        "http://localhost:8000",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return []

    # Auth & JWT
    JWT_SECRET: str = "dev_secret_key_change_in_production_veyra_voice_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Database
    # Uses SQLite by default for zero-friction setup, PostgreSQL in production
    DATABASE_URL: str = "sqlite+aiosqlite:///./veyra_voice.db"

    # Redis / Queue
    REDIS_URL: str = ""

    # AI Provider: 'mock' or 'gemini'
    AI_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEY_1: str = ""
    GEMINI_API_KEY_2: str = ""
    GEMINI_API_KEY_3: str = ""
    GEMINI_API_KEY_4: str = ""
    GEMINI_MODEL: str = "gemini-3.1-flash-live-preview"
    GEMINI_VOICE_NAME: str = "Zephyr"

    def get_gemini_keys(self) -> List[str]:
        keys = [
            self.GEMINI_API_KEY,
            self.GEMINI_API_KEY_1,
            self.GEMINI_API_KEY_2,
            self.GEMINI_API_KEY_3,
            self.GEMINI_API_KEY_4,
        ]
        return [k.strip() for k in keys if k and len(k.strip()) > 5]

    # Telephony Provider: 'mock', 'exotel', or 'twilio'
    TELEPHONY_PROVIDER: str = "mock"
    EXOTEL_ACCOUNT_SID: str = ""
    EXOTEL_API_KEY: str = ""
    EXOTEL_API_TOKEN: str = ""
    EXOTEL_SUB_DOMAIN: str = "api.exotel.com"
    EXOTEL_CALLER_ID: str = "+918012345678"
    EXOTEL_WEBHOOK_SECRET: str = ""
    TELEPHONY_WEBHOOK_BASE_URL: str = "http://localhost:8000"

    # Twilio Telephony Settings
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Call Defaults
    CALL_MAX_DURATION_SECONDS: int = 600
    SILENCE_TIMEOUT_SECONDS: int = 10
    RECORD_CALLS: bool = False
    DEFAULT_PRIMARY_LANGUAGE: str = "en"
    DEFAULT_FALLBACK_LANGUAGE: str = "en"

    model_config = SettingsConfigDict(
        env_file=(".env", "apps/api/.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
