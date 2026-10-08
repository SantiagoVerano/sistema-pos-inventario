"""
Repositorio de Categorías (app/database/repositories/inventario/categoria_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las operaciones de persistencia del catálogo de categorías en el esquema 'inventario'.
"""

from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.inventario.categoria import Categoria
from app.database.repositories.base_repository import BaseRepository


class CategoriaRepository(BaseRepository[Categoria, int]):
    """
    Repositorio para la entidad Categoria.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Categoria, session)

    def obtener_por_nombre(self, nombre: str) -> Optional[Categoria]:
        """Busca una categoría por su nombre exacto."""
        stmt = select(Categoria).where(Categoria.nombre == nombre.strip())
        return self.session.scalars(stmt).first()

    def listar_activas(self) -> Sequence[Categoria]:
        """Retorna todas las categorías activas (estado = True)."""
        stmt = select(Categoria).where(Categoria.estado.is_(True)).order_by(Categoria.nombre.asc())
        return self.session.scalars(stmt).all()

    def cambiar_estado(self, id_categoria: int, estado: bool) -> Optional[Categoria]:
        """Habilita o deshabilita una categoría."""
        categoria = self.get_by_id(id_categoria)
        if categoria:
            categoria.estado = estado
            self.session.flush()
            self.session.refresh(categoria)
        return categoria
