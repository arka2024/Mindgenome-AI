from __future__ import annotations

import json
from typing import Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    APP_ENV: str = "local"
    APP_DEBUG: bool = False
    APP_SECRET_KEY: str = "dev-secret-key-must-be-changed-in-production-minimum-64-characters-long"
    API_PUBLIC_URL: str = "http://localhost:8000"
    FRONTEND_PUBLIC_URL: str = "http://localhost:5173"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # Authentication & JWT
    JWT_ACCESS_TTL_SECONDS: int = 900  # 15 minutes
    JWT_REFRESH_TTL_SECONDS: int = 604800  # 7 days
    JWT_ALGORITHM: str = "HS256"
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_KIB: int = 65536
    ARGON2_PARALLELISM: int = 4

    # Google OAuth
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    GOOGLE_OAUTH_CLIENT_SECRET: str = ""
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_OCR_MODEL: str = "gemini-3.8-flash"
    GEMINI_TIMEOUT_SECONDS: int = 45
    GEMINI_MAX_RETRIES: int = 2

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://mindgenome:mindgenome@localhost:5432/mindgenome"
    DATABASE_URL_SYNC: str = "postgresql://mindgenome:mindgenome@localhost:5432/mindgenome"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # MongoDB Atlas activity/history store
    MONGODB_URI: str = ""
    MONGODB_DATABASE: str = "mindgenome"

    # Neo4j
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "changeme"
    NEO4J_DATABASE: str = "neo4j"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "mindgenome_chunks"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RATE_LIMIT_AUTH_PER_MINUTE: int = 5
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 120

    # SMTP / Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@mindgenome.ai"
    SMTP_TLS: bool = False
    EMAIL_VERIFICATION_TOKEN_TTL_SECONDS: int = 86400  # 24 hours
    PASSWORD_RESET_TOKEN_TTL_SECONDS: int = 3600  # 1 hour

    # Object storage (MinIO / S3)
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minio"
    S3_SECRET_KEY: str = "minio12345"
    S3_BUCKET: str = "mindgenome-uploads"
    S3_REGION: str = "us-east-1"
    UPLOAD_MAX_BYTES: int = 26214400

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        return ["http://localhost:5173"]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in ("production", "prod")


settings = Settings()
