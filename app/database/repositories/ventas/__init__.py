"""
Repositorios del Esquema de Ventas
"""

from app.database.repositories.ventas.cliente_repository import ClienteRepository
from app.database.repositories.ventas.venta_repository import VentaRepository

__all__ = [
    "ClienteRepository",
    "VentaRepository",
]
