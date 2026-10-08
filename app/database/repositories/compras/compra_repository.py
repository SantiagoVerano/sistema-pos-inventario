"""
Repositorio de Compras (app/database/repositories/compras/compra_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las transacciones de compras y sus detalles en 'compras.compras' y 'compras.detalle_compras'.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database.models.compras.compra import Compra, DetalleCompra
from app.database.repositories.base_repository import BaseRepository


class CompraRepository(BaseRepository[Compra, int]):
    """
    Repositorio para el manejo de compras y sus líneas de detalle.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Compra, session)

    def obtener_por_id_con_detalles(self, id_compra: int) -> Optional[Compra]:
        """Obtiene una compra por ID con proveedor, usuario y detalles pre-cargados."""
        stmt = (
            select(Compra)
            .options(
                joinedload(Compra.proveedor),
                joinedload(Compra.usuario),
                joinedload(Compra.detalles).joinedload(DetalleCompra.producto),
            )
            .where(Compra.id_compra == id_compra)
        )
        return self.session.scalars(stmt).unique().first()

    def crear_compra(
        self,
        id_proveedor: int,
        id_usuario: int,
        subtotal: Decimal,
        impuestos: Decimal,
        total: Decimal,
        detalles_data: List[Dict],
        estado: str = "PENDIENTE",
    ) -> Compra:
        """
        Crea la cabecera de la compra y agrega sus detalles de forma atómica en la sesión.
        """
        nueva_compra = Compra(
            id_proveedor=id_proveedor,
            id_usuario=id_usuario,
            subtotal=subtotal,
            impuestos=impuestos,
            total=total,
            estado=estado,
        )
        self.session.add(nueva_compra)
        self.session.flush()

        # Agregar los detalles vinculados
        for item in detalles_data:
            detalle = DetalleCompra(
                id_compra=nueva_compra.id_compra,
                id_producto=item["id_producto"],
                cantidad=item["cantidad"],
                costo_unitario=item["costo_unitario"],
                subtotal=item["subtotal"],
            )
            self.session.add(detalle)

        self.session.flush()
        self.session.refresh(nueva_compra)
        return nueva_compra

    def listar_por_estado(self, estado: str) -> Sequence[Compra]:
        """Retorna las compras filtradas por su estado (PENDIENTE, COMPLETADA, ANULADA)."""
        stmt = (
            select(Compra)
            .options(joinedload(Compra.proveedor), joinedload(Compra.usuario))
            .where(Compra.estado == estado)
            .order_by(Compra.fecha_compra.desc())
        )
        return self.session.scalars(stmt).all()

    def listar_por_rango_fechas(
        self, fecha_inicio: datetime, fecha_fin: datetime
    ) -> Sequence[Compra]:
        """Retorna compras registradas en un intervalo temporal."""
        stmt = (
            select(Compra)
            .options(joinedload(Compra.proveedor), joinedload(Compra.usuario))
            .where(
                Compra.fecha_compra >= fecha_inicio,
                Compra.fecha_compra <= fecha_fin,
            )
            .order_by(Compra.fecha_compra.desc())
        )
        return self.session.scalars(stmt).all()

    def cambiar_estado(self, id_compra: int, nuevo_estado: str) -> Optional[Compra]:
        """Actualiza el estado de una compra."""
        compra = self.get_by_id(id_compra)
        if compra:
            compra.estado = nuevo_estado
            self.session.flush()
            self.session.refresh(compra)
        return compra
