"""
Registro Central de Controladores (app/controllers/__init__.py)
"""

from app.controllers.seguridad.auth_controller import AuthController
from app.controllers.inventario.inventario_controller import InventarioController
from app.controllers.compras.compras_controller import ComprasController
from app.controllers.ventas.pos_controller import POSController, ItemCarrito

__all__ = [
    "AuthController",
    "InventarioController",
    "ComprasController",
    "POSController",
    "ItemCarrito",
]
