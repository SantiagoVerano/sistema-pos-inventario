"""
Repositorios del Esquema de Seguridad
"""

from app.database.repositories.seguridad.usuario_repository import UsuarioRepository
from app.database.repositories.seguridad.rol_repository import RolRepository

__all__ = [
    "UsuarioRepository",
    "RolRepository",
]
