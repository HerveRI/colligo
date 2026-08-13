from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends
from pydantic import Field, PostgresDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"


class EmbedProvider(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"


KNOWN_EMBED_DIMS: dict[str, int] = {
    "nomic-embed-text": 768,
    "text-embedding-3-small": 1536,
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: PostgresDsn

    LLM_PROVIDER: LLMProvider = LLMProvider.OLLAMA
    EMBED_PROVIDER: EmbedProvider = EmbedProvider.OLLAMA

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "qwen3.5:9b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OLLAMA_NUM_CTX: int = Field(default=16384, ge=2048)

    OPENAI_API_KEY: str | None = None
    # OPENAI_EMBED_MODEL: str = "text-embedding-3-small"

    EMBED_DIM: int = Field(ge=1)

    LLM_TEMPERATURE: float = Field(default=0.1, ge=0.0, le=2.0)
    LLM_TOP_P: float = Field(default=0.9, gt=0.0, le=1.0)
    LLM_PRESENCE_PENALTY: float = Field(default=0.0, ge=-2.0, le=2.0)

    AGENT_MAX_ITERATIONS: int = Field(default=6, ge=1, le=20)
    RETRIEVAL_TOP_K: int = Field(default=12, ge=1, le=20)

    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def embed_model(self) -> str:
        if self.EMBED_PROVIDER is EmbedProvider.OLLAMA:
            return self.OLLAMA_EMBED_MODEL
        return self.OPENAI_EMBED_MODEL

    @property
    def sqlalchemy_url(self) -> str:
        return str(self.DATABASE_URL)

    @field_validator("DATABASE_URL")
    @classmethod
    def _require_psycopg_driver(cls, v: PostgresDsn) -> PostgresDsn:
        if v.scheme != "postgresql+psycopg":
            raise ValueError(f"DATABASE_URL scheme must be 'postgresql+psycopg', got {v.scheme!r}.")
        return v

    @model_validator(mode="after")
    def _require_provider_credentials(self) -> Settings:
        missing: list[str] = []
        for var, provider in (
            ("LLM_PROVIDER", self.LLM_PROVIDER),
            ("EMBED_PROVIDER", self.EMBED_PROVIDER),
        ):
            if provider == "openai" and not self.OPENAI_API_KEY:
                missing.append(f"OPENAI_API_KEY (needed by {var}={provider})")
        if missing:
            raise ValueError("Missing provider credentials: " + "; ".join(missing))
        return self

    @model_validator(mode="after")
    def _require_matching_embed_dim(self) -> Settings:
        expected = KNOWN_EMBED_DIMS.get(self.embed_model.split(":")[0])
        if expected is not None and expected != self.EMBED_DIM:
            raise ValueError(
                f"EMBED_DIM={self.EMBED_DIM} but {self.embed_model} emits {expected}-dim"
                "vectors. Fix the dim or re-embed"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


SettingsDep = Annotated[Settings, Depends(get_settings)]
