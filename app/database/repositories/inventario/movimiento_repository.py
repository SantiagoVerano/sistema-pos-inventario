"""
Repositorio de Movimientos de Inventario / Kardex (app/database/repositories/inventario/movimiento_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Registrar y consultar los movimientos de Kardex en 'inventario.movimientos_inventario'.
Proporciona auditoría histórica de entradas, salidas, ajustes y devoluciones.
"""

from datetime import datetime
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.models.inventario.movimiento_inventario import MovimientoInventario
from app.database.repositories.base_repository import BaseRepository


class MovimientoRepository(BaseRepository[MovimientoInventario, int]):
    """
    Repositorio para el libro de movimientos en 'inventario.movimientos_inventario'.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(MovimientoInventario, session)

    def registrar_movimiento(
        self,
        id_producto: int,
        tipo_movimiento: str,
        cantidad: int,
        id_usuario: int,
        referencia: Optional[str] = None,
        observacion: Optional[str] = None,
    ) -> MovimientoInventario:
        """
        Inserta un nuevo movimiento en el historial de Kardex.
        """
        movimiento = MovimientoInventario(
            id_producto=id_producto,
            tipo_movimiento=tipo_movimiento,
            cantidad=cantidad,
            id_usuario=id_usuario,
            referencia=referencia,
            observacion=observacion,
        )
        self.session.add(movimiento)
        self.session.flush()
        self.session.refresh(movimiento)
        return movimiento

    def obtener_historial_por_producto(
        self, id_producto: int, skip: int = 0, limit: int = 100
    ) -> Sequence[MovimientoInventario]:
        """Obtiene el historial de movimientos de un producto ordenado cronológicamente."""
        stmt = (
            select(MovimientoInventario)
            .options(
                joinedload(MovimientoInventario.usuario),
                joinedload(MovimientoInventario.producto),
            )
            .where(MovimientoInventario.id_producto == id_producto)
            .order_by(MovimientoInventario.fecha_movimiento.desc())
            .offset(skip)
            .limit(limit)
        )
        return self.session.scalars(stmt).all()

    def listar_por_rango_fechas(
        self, fecha_inicio: datetime, fecha_fin: datetime
    ) -> Sequence[MovimientoInventario]:
        """Retorna todos los movimientos generados dentro de un rango temporal."""
        stmt = (
            select(MovimientoInventario)
            .options(
                joinedload(MovimientoInventario.usuario),
                joinedload(MovimientoInventario.producto),
            )
            .where(
                MovimientoInventario.fecha_movimiento >= fecha_inicio,
                MovimientoInventario.fecha_movimiento <= fecha_fin,
            )
            .order_by(MovimientoInventario.fecha_movimiento.desc())
        )
        return self.session.scalars(stmt).all()
