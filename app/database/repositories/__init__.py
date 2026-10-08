"""
Registro Central de Repositorios (app/database/repositories/__init__.py)
"""

from app.database.repositories.base_repository import BaseRepository
from app.database.repositories.seguridad import UsuarioRepository, RolRepository
from app.database.repositories.inventario import (
    CategoriaRepository,
    MarcaRepository,
    UnidadRepository,
    ProductoRepository,
    StockRepository,
    MovimientoRepository,
)
from app.database.repositories.compras import (
    ProveedorRepository,
    CompraRepository,
)
from app.database.repositories.ventas import (
    ClienteRepository,
    VentaRepository,
)

__all__ = [
    "BaseRepository",
    "UsuarioRepository",
    "RolRepository",
    "CategoriaRepository",
    "MarcaRepository",
    "UnidadRepository",
    "ProductoRepository",
    "StockRepository",
    "MovimientoRepository",
    "ProveedorRepository",
    "CompraRepository",
    "ClienteRepository",
    "VentaRepository",
]
