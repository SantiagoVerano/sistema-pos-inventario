"""
Repositorios del Esquema de Compras
"""

from app.database.repositories.compras.proveedor_repository import ProveedorRepository
from app.database.repositories.compras.compra_repository import CompraRepository

__all__ = [
    "ProveedorRepository",
    "CompraRepository",
]
