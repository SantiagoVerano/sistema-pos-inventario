"""
Repositorio de Productos (app/database/repositories/inventario/producto_repository.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar las consultas y operaciones del catálogo maestro de productos en 'inventario.productos'.
Soporta búsquedas por código de barras, SKU, término difuso y alertas de stock mínimo.
"""

from decimal import Decimal
from typing import Optional, Sequence
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.database.models.inventario.producto import Producto
from app.database.models.inventario.inventario import Inventario
from app.database.repositories.base_repository import BaseRepository


class ProductoRepository(BaseRepository[Producto, int]):
    """
    Repositorio para el catálogo de Productos.
    """

    def __init__(self, session: Session) -> None:
        super().__init__(Producto, session)

    def obtener_por_id(self, id_producto: int) -> Optional[Producto]:
        """Obtiene un producto por ID cargando sus relaciones maestras e inventario."""
        stmt = (
            select(Producto)
            .options(
                joinedload(Producto.categoria),
                joinedload(Producto.marca),
                joinedload(Producto.unidad),
                joinedload(Producto.inventario),
            )
            .where(Producto.id_producto == id_producto)
        )
        return self.session.scalars(stmt).unique().first()

    def obtener_por_sku(self, sku: str) -> Optional[Producto]:
        """Busca un producto por su SKU único."""
        stmt = (
            select(Producto)
            .options(
                joinedload(Producto.categoria),
                joinedload(Producto.marca),
                joinedload(Producto.unidad),
                joinedload(Producto.inventario),
            )
            .where(Producto.sku == sku.strip())
        )
        return self.session.scalars(stmt).unique().first()

    def obtener_por_codigo_barras(self, codigo_barras: str) -> Optional[Producto]:
        """Busca un producto por su código de barras (usado por el lector en el POS)."""
        stmt = (
            select(Producto)
            .options(
                joinedload(Producto.categoria),
                joinedload(Producto.marca),
                joinedload(Producto.unidad),
                joinedload(Producto.inventario),
            )
            .where(Producto.codigo_barras == codigo_barras.strip())
        )
        return self.session.scalars(stmt).unique().first()

    def listar_productos(
        self,
        id_categoria: Optional[int] = None,
        solo_activos: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Producto]:
        """
        Retorna el listado paginado de productos con filtros opcionales de categoría y estado.
        - id_categoria: Filtra por categoría específica (si se proporciona)
        - solo_activos = True: Solo activos
        - solo_activos = False: Solo inactivos (deshabilitados)
        - solo_activos = None: Todos sin filtrar por estado
        """
        stmt = (
            select(Producto)
            .options(
                joinedload(Producto.categoria),
                joinedload(Producto.marca),
                joinedload(Producto.unidad),
                joinedload(Producto.inventario),
            )
        )
        if id_categoria is not None:
            stmt = stmt.where(Producto.id_categoria == id_categoria)
        if solo_activos is not None:
            stmt = stmt.where(Producto.activo.is_(solo_activos))

        stmt = stmt.order_by(Producto.nombre.asc()).offset(skip).limit(limit)
        return self.session.scalars(stmt).unique().all()

    def listar_activos(
        self, id_categoria: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> Sequence[Producto]:
        """Retorna el listado paginado de productos activos."""
        return self.listar_productos(
            id_categoria=id_categoria, solo_activos=True, skip=skip, limit=limit
        )

    def buscar_por_termino(
        self,
        termino: str,
        id_categoria: Optional[int] = None,
        solo_activos: Optional[bool] = None,
        limit: int = 25,
    ) -> Sequence[Producto]:
        """Búsqueda rápida por nombre, SKU o código de barras para autocompletado en UI."""
        patron = f"%{termino.strip()}%"
        stmt = (
            select(Producto)
            .options(
                joinedload(Producto.categoria),
                joinedload(Producto.marca),
                joinedload(Producto.unidad),
                joinedload(Producto.inventario),
            )
            .where(
                or_(
                    Producto.nombre.ilike(patron),
                    Producto.sku.ilike(patron),
                    Producto.codigo_barras.ilike(patron),
                ),
            )
        )
        if id_categoria is not None:
            stmt = stmt.where(Producto.id_categoria == id_categoria)
        if solo_activos is not None:
            stmt = stmt.where(Producto.activo.is_(solo_activos))

        stmt = stmt.order_by(Producto.nombre.asc()).limit(limit)
        return self.session.scalars(stmt).unique().all()

    def listar_bajo_stock_minimo(self) -> Sequence[Producto]:
        """Obtiene productos cuyo stock actual es menor o igual al stock mínimo configurado."""
        stmt = (
            select(Producto)
            .join(Inventario, Producto.id_producto == Inventario.id_producto)
            .options(
                joinedload(Producto.categoria),
                joinedload(Producto.marca),
                joinedload(Producto.unidad),
                joinedload(Producto.inventario),
            )
            .where(
                Producto.activo.is_(True),
                Inventario.stock_actual <= Producto.stock_minimo,
            )
            .order_by(Inventario.stock_actual.asc())
        )
        return self.session.scalars(stmt).unique().all()

    def actualizar_precios(
        self, id_producto: int, precio_compra: Decimal, precio_venta: Decimal
    ) -> Optional[Producto]:
        """Actualiza los valores de precio_compra y precio_venta de un producto."""
        producto = self.get_by_id(id_producto)
        if producto:
            producto.precio_compra = precio_compra
            producto.precio_venta = precio_venta
            self.session.flush()
            self.session.refresh(producto)
        return producto

    def cambiar_activo(self, id_producto: int, activo: bool) -> Optional[Producto]:
        """Habilita o deshabilita un producto (borrado lógico)."""
        producto = self.get_by_id(id_producto)
        if producto:
            producto.activo = activo
            self.session.flush()
            self.session.refresh(producto)
        return producto
