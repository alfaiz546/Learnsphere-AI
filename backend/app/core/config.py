from pathlib import Path
import os


# Import BaseSettings and SettingsConfigDict for Pydantic v2
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # Fallback for unexpected environments
    from pydantic import BaseSettings, ConfigDict as SettingsConfigDict

from pydantic import field_validator

# Resolve .env relative to project root regardless of the current working directory
# __file__ points to backend/app/core/config.py
# parents[3] resolves to the project root (learnsphere-ai-export)
ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://learnsphere:learnsphere@localhost:5432/learnsphere_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev-secret-key-change-in-production-use-32-chars-minimum"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    AI_MAX_RETRIES: int = 3
    AI_TIMEOUT_SECONDS: int = 30
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    ENVIRONMENT: str = "development"
    APP_NAME: str = "LearnSphere AI"
    AUTH_REQUIRE_REDIS_BLACKLIST: bool = False

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        insecure_keys = [
            "dev-secret-key-change-in-production-use-32-chars-minimum",
            "learnsphere-super-secret-jwt-key-32-chars-long-min",
            "secret",
            "changeme",
        ]
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env in ["production", "staging"]:
            if not v or v in insecure_keys or len(v) < 32:
                raise ValueError(
                    f"CRITICAL SECURITY ERROR: SECRET_KEY cannot be a default or weak key in {env}. Set a strong 64+ char random hex key."
                )
        elif v in insecure_keys or len(v) < 32:
            import logging

            logging.getLogger(__name__).warning(
                "SECURITY WARNING: SECRET_KEY is using a weak or default key. Rotate to a 64+ char random hex key."
            )
        return v

    # Pydantic v2 configuration: load environment variables from the .env file located at project root
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore"
    )

# Instantiate a single Settings object for the application to use
settings = Settings()
