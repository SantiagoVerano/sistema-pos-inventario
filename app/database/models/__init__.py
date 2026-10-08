"""
Registro Central de Modelos Declarativos (app/database/models/__init__.py)

Responsabilidad Arquitectónica:
-------------------------------
Importar todas las entidades de los 4 esquemas (seguridad, inventario, compras, ventas)
exactamente alineadas con el script DDL de PostgreSQL.
"""

# Esquema: Seguridad
from app.database.models.seguridad import (
    Usuario,
    Rol,
    UsuarioRol,
)

# Esquema: Inventario
from app.database.models.inventario import (
    Categoria,
    Marca,
    Unidad,
    Producto,
    Inventario,
    MovimientoInventario,
)

# Esquema: Compras
from app.database.models.compras import (
    Proveedor,
    Compra,
    DetalleCompra,
)

# Esquema: Ventas
from app.database.models.ventas import (
    Cliente,
    Venta,
    DetalleVenta,
)

__all__ = [
    # Seguridad
    "Usuario",
    "Rol",
    "UsuarioRol",
    # Inventario
    "Categoria",
    "Marca",
    "Unidad",
    "Producto",
    "Inventario",
    "MovimientoInventario",
    # Compras
    "Proveedor",
    "Compra",
    "DetalleCompra",
    # Ventas
    "Cliente",
    "Venta",
    "DetalleVenta",
]
