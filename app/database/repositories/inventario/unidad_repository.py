"""
Repositorio de Unidades (app/database/repositories/inventario/unidad_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las operaciones de persistencia de unidades en la tabla 'inventario.unidades'.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.inventario.unidad import Unidad
from app.database.repositories.base_repository import BaseRepository


class UnidadRepository(BaseRepository[Unidad, int]):
    """
    Repositorio para la entidad Unidad.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Unidad, session)

    def obtener_por_nombre(self, nombre: str) -> Optional[Unidad]:
        """Busca una unidad por su nombre descriptivo."""
        stmt = select(Unidad).where(Unidad.nombre == nombre.strip())
        return self.session.scalars(stmt).first()

    def obtener_por_abreviatura(self, abreviatura: str) -> Optional[Unidad]:
        """Busca una unidad por su abreviatura (ej: KG, UND)."""
        stmt = select(Unidad).where(Unidad.abreviatura == abreviatura.strip().upper())
        return self.session.scalars(stmt).first()

    def listar_todas(self) -> Sequence[Unidad]:
        """Retorna todas las unidades registradas."""
        stmt = select(Unidad).order_by(Unidad.nombre.asc())
        return self.session.scalars(stmt).all()
