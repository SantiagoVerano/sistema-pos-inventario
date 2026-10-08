"""
Modelos del Esquema de Compras
"""

from app.database.models.compras.proveedor import Proveedor
from app.database.models.compras.compra import Compra, DetalleCompra

__all__ = [
    "Proveedor",
    "Compra",
    "DetalleCompra",
]
