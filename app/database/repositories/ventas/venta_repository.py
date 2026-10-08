"""
Repositorio de Ventas (app/database/repositories/ventas/venta_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las transacciones de ventas y sus líneas de detalle en 'ventas.ventas' y 'ventas.detalle_venta'.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.models.ventas.venta import Venta, DetalleVenta
from app.database.repositories.base_repository import BaseRepository


class VentaRepository(BaseRepository[Venta, int]):
    """
    Repositorio para el manejo de ventas POS y sus detalles.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Venta, session)

    def obtener_por_id_con_detalles(self, id_venta: int) -> Optional[Venta]:
        """Obtiene una venta por ID con cliente, cajero y productos en detalle pre-cargados."""
        stmt = (
            select(Venta)
            .options(
                joinedload(Venta.cliente),
                joinedload(Venta.usuario),
                joinedload(Venta.detalles).joinedload(DetalleVenta.producto),
            )
            .where(Venta.id_venta == id_venta)
        )
        return self.session.scalars(stmt).unique().first()

    def crear_venta(
        self,
        id_usuario: int,
        subtotal: Decimal,
        impuestos: Decimal,
        descuento: Decimal,
        total: Decimal,
        detalles_data: List[Dict],
        id_cliente: Optional[int] = None,
        estado: str = "COMPLETADA",
    ) -> Venta:
        """
        Crea la cabecera de la venta y sus detalles de forma atómica en la sesión.
        """
        nueva_venta = Venta(
            id_cliente=id_cliente,
            id_usuario=id_usuario,
            subtotal=subtotal,
            impuestos=impuestos,
            descuento=descuento,
            total=total,
            estado=estado,
        )
        self.session.add(nueva_venta)
        self.session.flush()

        # Agregar los detalles vinculados
        for item in detalles_data:
            detalle = DetalleVenta(
                id_venta=nueva_venta.id_venta,
                id_producto=item["id_producto"],
                cantidad=item["cantidad"],
                precio_unitario=item["precio_unitario"],
                subtotal=item["subtotal"],
            )
            self.session.add(detalle)

        self.session.flush()
        self.session.refresh(nueva_venta)
        return nueva_venta

    def listar_por_rango_fechas(
        self, fecha_inicio: datetime, fecha_fin: datetime
    ) -> Sequence[Venta]:
        """Retorna ventas registradas dentro de un periodo."""
        stmt = (
            select(Venta)
            .options(
                joinedload(Venta.cliente),
                joinedload(Venta.usuario),
                joinedload(Venta.detalles).joinedload(DetalleVenta.producto),
            )
            .where(
                Venta.fecha_venta >= fecha_inicio,
                Venta.fecha_venta <= fecha_fin,
            )
            .order_by(Venta.fecha_venta.desc(), Venta.id_venta.desc())
        )
        return self.session.scalars(stmt).unique().all()

    def listar_recientes(self, limit: int = 100) -> Sequence[Venta]:
        """Retorna las ventas más recientes registradas."""
        stmt = (
            select(Venta)
            .options(
                joinedload(Venta.cliente),
                joinedload(Venta.usuario),
                joinedload(Venta.detalles).joinedload(DetalleVenta.producto),
            )
            .order_by(Venta.fecha_venta.desc(), Venta.id_venta.desc())
            .limit(limit)
        )
        return self.session.scalars(stmt).unique().all()

    def listar_por_usuario(self, id_usuario: int) -> Sequence[Venta]:
        """Retorna las ventas realizadas por un cajero específico."""
        stmt = (
            select(Venta)
            .where(Venta.id_usuario == id_usuario)
            .order_by(Venta.fecha_venta.desc())
        )
        return self.session.scalars(stmt).all()

    def cambiar_estado(self, id_venta: int, nuevo_estado: str) -> Optional[Venta]:
        """Actualiza el estado de una venta (ej: ANULADA)."""
        venta = self.get_by_id(id_venta)
        if venta:
            venta.estado = nuevo_estado
            self.session.flush()
            self.session.refresh(venta)
        return venta
