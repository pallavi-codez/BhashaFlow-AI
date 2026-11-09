"""
Application configuration — reads from environment / .env file.
Secrets are NEVER exposed to the frontend.
"""
from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # ── Gnani AI ──────────────────────────────────────────────────────────────
    gnani_api_key: str = ""

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'bhashaflow.db').as_posix()}"

    @field_validator("database_url", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if v.startswith("sqlite:///") and not v.startswith("sqlite:///:memory:"):
            rel_part = v[len("sqlite:///"):]
            p = Path(rel_part)
            if not p.is_absolute():
                abs_p = (PROJECT_ROOT / p).resolve()
                return f"sqlite:///{abs_p.as_posix()}"
        return v

    # ── App ───────────────────────────────────────────────────────────────────
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # ── Limits ────────────────────────────────────────────────────────────────
    max_audio_size_mb: int = 10
    gnani_timeout_seconds: int = 30

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(
        # Use an absolute path so this works regardless of the working directory
        # from which uvicorn / pytest is launched.
        env_file=str(Path(__file__).resolve().parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
