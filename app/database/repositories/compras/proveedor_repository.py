"""
Repositorio de Proveedores (app/database/repositories/compras/proveedor_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las operaciones de persistencia del directorio de proveedores en 'compras.proveedores'.
"""

from typing import Optional, Sequence
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.models.compras.proveedor import Proveedor
from app.database.repositories.base_repository import BaseRepository


class ProveedorRepository(BaseRepository[Proveedor, int]):
    """
    Repositorio para la entidad Proveedor.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Proveedor, session)

    def obtener_por_nit(self, nit: str) -> Optional[Proveedor]:
        """Busca un proveedor por su número de identificación tributaria (NIT/RUC)."""
        stmt = select(Proveedor).where(Proveedor.nit == nit.strip())
        return self.session.scalars(stmt).first()

    def listar_activos(self) -> Sequence[Proveedor]:
        """Retorna todos los proveedores con estado activo = True."""
        stmt = (
            select(Proveedor)
            .where(Proveedor.estado.is_(True))
            .order_by(Proveedor.razon_social.asc())
        )
        return self.session.scalars(stmt).all()

    def buscar_por_termino(self, termino: str) -> Sequence[Proveedor]:
        """Busca proveedores por coincidencia en razón social o NIT."""
        patron = f"%{termino.strip()}%"
        stmt = (
            select(Proveedor)
            .where(
                Proveedor.estado.is_(True),
                or_(
                    Proveedor.razon_social.ilike(patron),
                    Proveedor.nit.ilike(patron),
                ),
            )
            .order_by(Proveedor.razon_social.asc())
        )
        return self.session.scalars(stmt).all()

    def cambiar_estado(self, id_proveedor: int, estado: bool) -> Optional[Proveedor]:
        """Habilita o deshabilita un proveedor."""
        proveedor = self.get_by_id(id_proveedor)
        if proveedor:
            proveedor.estado = estado
            self.session.flush()
            self.session.refresh(proveedor)
        return proveedor
