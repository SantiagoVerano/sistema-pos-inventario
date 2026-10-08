"""
Repositorio de Clientes (app/database/repositories/ventas/cliente_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las consultas y operaciones del directorio de clientes en 'ventas.clientes'.
"""

from typing import Optional, Sequence
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database.models.ventas.cliente import Cliente
from app.database.repositories.base_repository import BaseRepository


class ClienteRepository(BaseRepository[Cliente, int]):
    """
    Repositorio para la entidad Cliente.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Cliente, session)

    def obtener_por_documento(self, numero_documento: str) -> Optional[Cliente]:
        """Busca un cliente por su número de documento (DNI/RUC/Cédula)."""
        stmt = select(Cliente).where(Cliente.numero_documento == numero_documento.strip())
        return self.session.scalars(stmt).first()

    def buscar_por_termino(self, termino: str, limit: int = 20) -> Sequence[Cliente]:
        """Busca clientes por coincidencia en nombre, apellido o número de documento."""
        patron = f"%{termino.strip()}%"
        stmt = (
            select(Cliente)
            .where(
                or_(
                    Cliente.nombre.ilike(patron),
                    Cliente.apellido.ilike(patron),
                    Cliente.numero_documento.ilike(patron),
                )
            )
            .order_by(Cliente.nombre.asc())
            .limit(limit)
        )
        return self.session.scalars(stmt).all()

    def listar_recientes(self, limit: int = 50) -> Sequence[Cliente]:
        """Retorna los últimos clientes registrados."""
        stmt = select(Cliente).order_by(Cliente.fecha_registro.desc()).limit(limit)
        return self.session.scalars(stmt).all()
