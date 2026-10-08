"""
Repositorio de Inventario y Control de Stock (app/database/repositories/inventario/stock_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las existencias físicas en 'inventario.inventario'.
Implementa BLOQUEO PESIMISTA ('with_for_update()') para prevenir condiciones de carrera
en operaciones concurrentes de ventas o despachos, asegurando la Regla N° 1 (Stock No Negativo).
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import InsufficientStockException
from app.database.models.inventario.inventario import Inventario
from app.database.repositories.base_repository import BaseRepository


class StockRepository(BaseRepository[Inventario, int]):
    """
    Repositorio para el control de existencias en 'inventario.inventario'.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Inventario, session)

    def obtener_por_id_producto(self, id_producto: int) -> Optional[Inventario]:
        """Consulta el balance de stock actual sin bloqueo."""
        return self.session.get(Inventario, id_producto)

    def obtener_con_bloqueo(self, id_producto: int) -> Optional[Inventario]:
        """
        Bloquea la fila del producto en PostgreSQL con 'SELECT ... FOR UPDATE'.
        Garantiza que ninguna otra transacción concurrentemente modifique el stock
        hasta que la transacción actual termine (commit o rollback).
        """
        stmt = (
            select(Inventario)
            .where(Inventario.id_producto == id_producto)
            .with_for_update()
        )
        return self.session.scalars(stmt).first()

    def inicializar_stock(self, id_producto: int, stock_inicial: int = 0) -> Inventario:
        """Crea el registro de balance en 'inventario.inventario' para un nuevo producto."""
        if stock_inicial < 0:
            raise InsufficientStockException(
                id_producto=id_producto,
                stock_disponible=0,
                cantidad_solicitada=abs(stock_inicial),
            )

        registro = self.obtener_por_id_producto(id_producto)
        if registro is None:
            registro = Inventario(id_producto=id_producto, stock_actual=stock_inicial)
            self.session.add(registro)
        else:
            registro.stock_actual = stock_inicial

        self.session.flush()
        self.session.refresh(registro)
        return registro

    def modificar_stock(self, id_producto: int, delta_cantidad: int) -> Inventario:
        """
        Modifica el stock actual sumando (delta positivo) o restando (delta negativo).
        Utiliza bloqueo pesimista y valida que no quede en negativo.
        """
        registro = self.obtener_con_bloqueo(id_producto)
        if registro is None:
            # Si no existía fila en inventario, se inicializa
            registro = self.inicializar_stock(id_producto, 0)

        nuevo_stock = registro.stock_actual + delta_cantidad
        if nuevo_stock < 0:
            raise InsufficientStockException(
                id_producto=id_producto,
                stock_disponible=registro.stock_actual,
                cantidad_solicitada=abs(delta_cantidad),
            )

        registro.stock_actual = nuevo_stock
        self.session.flush()
        self.session.refresh(registro)
        return registro
