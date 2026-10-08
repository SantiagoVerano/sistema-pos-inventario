"""
Módulo de Configuración y Variables de Entorno (app/core/config.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar de manera segura y tipada todas las configuraciones globales del sistema mediante
'pydantic-settings'. Lee variables desde el archivo '.env' y valida sus tipos y restricciones
en tiempo de arranque, evitando fallos silenciosos por configuraciones faltantes o erróneas.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# Directorio raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Configuración central de la aplicación cargada desde variables de entorno y archivo .env.
    """
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Identificación del Sistema
    APP_NAME: str = Field(default="Sistema de Gestión de Inventarios y POS", description="Nombre de la aplicación")
    APP_VERSION: str = Field(default="1.0.0", description="Versión del software")
    ENVIRONMENT: str = Field(default="development", description="Entorno: development, testing, production")
    DEBUG: bool = Field(default=False, description="Modo depuración activo")

    # Base de Datos PostgreSQL
    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://postgres:postgres@localhost:5432/pos_db",
        description="Cadena de conexión a PostgreSQL con driver psycopg2"
    )
    DB_POOL_SIZE: int = Field(default=10, description="Tamaño base del pool de conexiones")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Conexiones adicionales máximas permitidas")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Segundos de espera para obtener conexión libre")
    DB_POOL_RECYCLE: int = Field(default=1800, description="Tiempo de vida en segundos antes de reciclar conexión")
    DB_ECHO: bool = Field(default=False, description="Imprimir consultas SQL en consola")

    # Seguridad y Criptografía
    SECRET_KEY: str = Field(
        default="pos_insecure_default_secret_key_change_in_production_32_bytes",
        description="Clave secreta para tokens de sesión y firma criptográfica"
    )
    HASH_ALGORITHM: str = Field(default="argon2", description="Algoritmo de hash de contraseñas: argon2 o bcrypt")
    SESSION_TIMEOUT_MINUTES: int = Field(default=480, description="Tiempo de expiración de sesión (8 horas de turno)")

    # Rutas y Logging
    LOG_LEVEL: str = Field(default="INFO", description="Nivel de log: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    LOG_DIR: Path = Field(default=BASE_DIR / "logs", description="Directorio para almacenamiento de archivos de log")

    @field_validator("DATABASE_URL")
    @classmethod
    def validar_database_url(cls, v: str) -> str:
        """Asegura que la URL especifique el motor PostgreSQL y el dialecto correspondiente."""
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL debe comenzar con 'postgresql' o 'postgresql+psycopg2://'")
        # Si el usuario escribió postgresql:// sin especificar driver, redirigir a psycopg2
        if v.startswith("postgresql://"):
            v = v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v


# Instancia singleton accesible desde cualquier módulo
settings = Settings()
