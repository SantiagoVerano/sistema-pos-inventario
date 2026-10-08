"""
Repositorio de Marcas (app/database/repositories/inventario/marca_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las operaciones de persistencia de marcas en el esquema 'inventario'.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.inventario.marca import Marca
from app.database.repositories.base_repository import BaseRepository


class MarcaRepository(BaseRepository[Marca, int]):
    """
    Repositorio para la entidad Marca.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Marca, session)

    def obtener_por_nombre(self, nombre: str) -> Optional[Marca]:
        """Busca una marca por su nombre comercial."""
        stmt = select(Marca).where(Marca.nombre == nombre.strip())
        return self.session.scalars(stmt).first()

    def listar_activas(self) -> Sequence[Marca]:
        """Retorna todas las marcas activas (estado = True)."""
        stmt = select(Marca).where(Marca.estado.is_(True)).order_by(Marca.nombre.asc())
        return self.session.scalars(stmt).all()

    def cambiar_estado(self, id_marca: int, estado: bool) -> Optional[Marca]:
        """Habilita o deshabilita una marca."""
        marca = self.get_by_id(id_marca)
        if marca:
            marca.estado = estado
            self.session.flush()
            self.session.refresh(marca)
        return marca
