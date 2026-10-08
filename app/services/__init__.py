"""
Registro Central de Servicios del Dominio (app/services/__init__.py)
"""

from app.services.seguridad.auth_service import AuthService, UsuarioAutenticado
from app.services.inventario.inventario_service import InventarioService
from app.services.compras.compra_service import CompraService
from app.services.ventas.venta_service import VentaService

__all__ = [
    "AuthService",
    "UsuarioAutenticado",
    "InventarioService",
    "CompraService",
    "VentaService",
]
