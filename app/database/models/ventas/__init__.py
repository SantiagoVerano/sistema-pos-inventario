"""
Modelos del Esquema de Ventas
"""

from app.database.models.ventas.cliente import Cliente
from app.database.models.ventas.venta import Venta, DetalleVenta

__all__ = [
    "Cliente",
    "Venta",
    "DetalleVenta",
]
