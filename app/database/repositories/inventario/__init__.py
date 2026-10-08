"""
Repositorios del Esquema de Inventario
"""

from app.database.repositories.inventario.categoria_repository import CategoriaRepository
from app.database.repositories.inventario.marca_repository import MarcaRepository
from app.database.repositories.inventario.unidad_repository import UnidadRepository
from app.database.repositories.inventario.producto_repository import ProductoRepository
from app.database.repositories.inventario.stock_repository import StockRepository
from app.database.repositories.inventario.movimiento_repository import MovimientoRepository

__all__ = [
    "CategoriaRepository",
    "MarcaRepository",
    "UnidadRepository",
    "ProductoRepository",
    "StockRepository",
    "MovimientoRepository",
]
