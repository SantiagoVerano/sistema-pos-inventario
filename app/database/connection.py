"""
Módulo de Conexión y Gestión de Sesiones (app/database/connection.py)

Responsabilidad Arquitectónica:
-------------------------------
Administrar el ciclo de vida del Engine de SQLAlchemy 2.0 y proveer la fábrica
de sesiones 'SessionLocal' configurada con connection pooling robusto.
Ofrece un context manager 'session_scope()' para transacciones ACID atómicas
utilizado por la capa de servicios.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.logger import get_logger
from app.core.constants import DatabaseSchema

logger = get_logger(__name__)

# 1. Creación del Engine con pool de conexiones empresarial
engine = create_engine(
    url=Settings().DATABASE_URL,
    echo=Settings().DB_ECHO,
    pool_size=Settings().DB_POOL_SIZE,
    max_overflow=Settings().DB_MAX_OVERFLOW,
    pool_timeout=Settings().DB_POOL_TIMEOUT,
    pool_recycle=Settings().DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Comprueba que la conexión siga viva antes de usarla
)

# 2. Fábrica de Sesiones SQLAlchemy
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False  # Permite acceder a los atributos de las entidades después del commit
)


def get_session() -> Generator[Session, None, None]:
    """
    Generador de sesiones para ser consumido en controladores o inyectores de dependencias.
    Garantiza el cierre seguro de la sesión en el bloque finally.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager transaccional para la Capa de Servicios (Unit of Work).
    
    Uso:
        with session_scope() as session:
            repo.crear(...)
            # Hace commit automáticamente al salir del bloque sin errores.
            # En caso de excepción, ejecuta rollback automático.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Error en bloque transaccional: {exc}", exc_info=True)
        raise
    finally:
        session.close()


def inicializar_esquemas_db() -> None:
    """
    Crea los 4 esquemas requeridos ('seguridad', 'inventario', 'compras', 'ventas')
    en PostgreSQL si aún no existen.
    """
    esquemas = [
        DatabaseSchema.SEGURIDAD.value,
        DatabaseSchema.INVENTARIO.value,
        DatabaseSchema.COMPRAS.value,
        DatabaseSchema.VENTAS.value,
    ]
    with engine.begin() as conn:
        for esquema in esquemas:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {esquema};"))
            logger.info(f"Esquema '{esquema}' verificado/creado con éxito.")
