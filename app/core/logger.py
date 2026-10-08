"""
Módulo de Registro de Eventos y Logging Estructurado (app/core/logger.py)

Responsabilidad Arquitectónica:
-------------------------------
Configurar el sistema centralizado de bitácora (logging) de la aplicación.
Proporciona salida simultánea a la consola y a archivos rotativos en disco
('logs/app.log'), garantizando que cualquier anomalía, traza de error o evento
de auditoría quede registrado con timestamp, nivel y ubicación en código fuente.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from app.core.config import settings


def configurar_logger() -> None:
    """
    Inicializa los manejadores globales del logging raíz de Python.
    Crea el directorio de logs si no existe y define política de rotación.
    """
    # 1. Asegurar la existencia de la carpeta de logs
    log_dir: Path = settings.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file: Path = log_dir / "app.log"

    # 2. Formato estandarizado para observabilidad
    formato = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-8s] [%(name)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 3. Nivel de log obtenido de la configuración
    nivel_log = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # 4. Logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(nivel_log)

    # Evitar duplicar manejadores si se llama más de una vez
    if not root_logger.handlers:
        # Manejador 1: Consola estándar (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(nivel_log)
        console_handler.setFormatter(formato)
        root_logger.addHandler(console_handler)

        # Manejador 2: Archivo rotativo (10 MB por archivo, conserva hasta 5 copias)
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8"
        )
        file_handler.setLevel(nivel_log)
        file_handler.setFormatter(formato)
        root_logger.addHandler(file_handler)

    # Silenciar logs excesivamente verbosos de librerías externas si no estamos en DEBUG
    if not settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(nombre_modulo: str) -> logging.Logger:
    """
    Retorna una instancia configurada de Logger para el módulo solicitante.

    Uso recomendado:
        from app.core.logger import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(nombre_modulo)


# Ejecución automática de configuración al importar
configurar_logger()
