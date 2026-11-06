"""Configuración desde variables de entorno (12-Factor App)."""
from __future__ import annotations

import os
from dataclasses import dataclass


def normalizar_url(url: str) -> str:
    """Render/Railway entregan postgres:// o postgresql://; SQLAlchemy necesita el driver."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./edutech.db"
    seed_on_startup: bool = False
    app_env: str = "development"

    @classmethod
    def desde_entorno(cls) -> Settings:
        return cls(
            database_url=normalizar_url(os.getenv("DATABASE_URL", cls.database_url)),
            seed_on_startup=os.getenv("SEED_ON_STARTUP", "false").lower() in ("1", "true", "yes"),
            app_env=os.getenv("APP_ENV", "development"),
        )
