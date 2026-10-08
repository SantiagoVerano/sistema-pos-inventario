"""
Repositorio de Roles (app/database/repositories/seguridad/rol_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las operaciones de persistencia del catálogo de roles en el esquema 'seguridad'.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.seguridad.rol import Rol
from app.database.repositories.base_repository import BaseRepository


class RolRepository(BaseRepository[Rol, int]):
    """
    Repositorio para la entidad Rol.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Rol, session)

    def obtener_por_nombre(self, nombre: str) -> Optional[Rol]:
        """Busca un rol por su nombre único."""
        stmt = select(Rol).where(Rol.nombre == nombre.strip().upper())
        return self.session.scalars(stmt).first()

    def listar_todos(self) -> Sequence[Rol]:
        """Retorna todos los roles ordenados alfabéticamente."""
        stmt = select(Rol).order_by(Rol.nombre.asc())
        return self.session.scalars(stmt).all()
