"""Settings come only from environment variables (or a local, git-ignored .env)."""

from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"  # development | test | production
    database_url: str = "postgresql+psycopg://bazaraf:dev-only-pw@localhost:5432/bazaraf"
    jwt_secret: str = Field(default="", repr=False)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"
    bcrypt_rounds: int = Field(default=12, ge=4, le=15)  # tests lower it for speed; production keeps 12
    lockout_threshold: int = 5
    lockout_minutes: int = 15

    @model_validator(mode="after")
    def _require_secret(self) -> "Settings":
        if not self.jwt_secret:
            if self.environment == "production":
                raise ValueError("JWT_SECRET must be set in production")
            # Ephemeral per-process secret for dev/test: tokens die on restart, nothing is hard-coded.
            import secrets

            self.jwt_secret = secrets.token_hex(32)
        elif self.environment == "production" and len(self.jwt_secret) < 32:
            raise ValueError("JWT_SECRET must be at least 32 characters in production")
        return self

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
