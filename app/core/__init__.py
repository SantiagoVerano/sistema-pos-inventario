"""
Paquete Core del Sistema de Gestión de Inventarios y POS
"""

from app.core.config import settings
from app.core.logger import get_logger
from app.core.constants import (
    DatabaseSchema,
    TipoMovimiento,
    EstadoCompra,
    EstadoVenta,
)
from app.core.exceptions import (
    AppException,
    BusinessException,
    InsufficientStockException,
    DuplicateResourceException,
    ResourceNotFoundException,
    InvalidOperationException,
    SecurityException,
    AuthenticationException,
    AuthorizationException,
    DatabaseException,
    ConcurrentModificationException,
    ValidationException,
)

__all__ = [
    "settings",
    "get_logger",
    "DatabaseSchema",
    "TipoMovimiento",
    "EstadoCompra",
    "EstadoVenta",
    "AppException",
    "BusinessException",
    "InsufficientStockException",
    "DuplicateResourceException",
    "ResourceNotFoundException",
    "InvalidOperationException",
    "SecurityException",
    "AuthenticationException",
    "AuthorizationException",
    "DatabaseException",
    "ConcurrentModificationException",
    "ValidationException",
]
