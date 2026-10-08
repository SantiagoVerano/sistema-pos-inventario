"""
Servicio de Gestión de Inventarios y Catálogo (app/services/inventario/inventario_service.py)

Responsabilidad Arquitectónica:
-------------------------------
Orquestar el 100% de las reglas de negocio del dominio de inventario:
1. Validación de unicidad de SKU y códigos de barras.
2. Cumplimiento de la Regla N° 1: Prohibición de Stock Negativo.
3. Cumplimiento de la Regla N° 2: Registro estricto en Kardex Perpetuo para todo cambio de stock.
4. Bloqueos pesimistas para mutaciones concurrentes.
5. Transaccionalidad atómica mediante 'session_scope()'.
"""

from decimal import Decimal
from typing import Any, Dict, Optional, Sequence
from app.core.constants import TipoMovimiento
from app.core.exceptions import (
    DuplicateResourceException,
    InvalidOperationException,
    ResourceNotFoundException,
    ValidationException,
)
from app.core.logger import get_logger
from app.database.connection import session_scope
from app.database.models.inventario.categoria import Categoria
from app.database.models.inventario.producto import Producto
from app.database.models.inventario.movimiento_inventario import MovimientoInventario
from app.database.repositories.inventario.categoria_repository import CategoriaRepository
from app.database.repositories.inventario.marca_repository import MarcaRepository
from app.database.repositories.inventario.unidad_repository import UnidadRepository
from app.database.repositories.inventario.producto_repository import ProductoRepository
from app.database.repositories.inventario.stock_repository import StockRepository
from app.database.repositories.inventario.movimiento_repository import MovimientoRepository

logger = get_logger(__name__)


class InventarioService:
    """
    Servicio para el Catálogo de Productos, Control de Stock y Kardex.
    """

    # ==========================================================================
    # 1. GESTIÓN DE PRODUCTOS Y REGISTRO INICIAL
    # ==========================================================================
    def registrar_producto_con_stock_inicial(
        self,
        datos_producto: Dict[str, Any],
        stock_inicial: int,
        id_usuario_operador: int,
    ) -> Producto:
        """
        Crea un artículo en el catálogo maestro, inicializa su balance en 'inventario'
        y genera el primer movimiento de Kardex (ENTRADA) de manera atómica.
        """
        # Validaciones de entrada
        sku = str(datos_producto.get("sku", "")).strip()
        nombre = str(datos_producto.get("nombre", "")).strip()
        codigo_barras = datos_producto.get("codigo_barras")
        if codigo_barras:
            codigo_barras = str(codigo_barras).strip()

        if not sku:
            raise ValidationException("El código SKU es obligatorio.")
        if not nombre:
            raise ValidationException("El nombre del producto es obligatorio.")
        if stock_inicial < 0:
            raise ValidationException("El stock inicial no puede ser negativo.")

        precio_compra = Decimal(str(datos_producto.get("precio_compra", "0.00")))
        precio_venta = Decimal(str(datos_producto.get("precio_venta", "0.00")))

        if precio_compra < 0 or precio_venta < 0:
            raise ValidationException("Los precios de compra y venta deben ser mayores o iguales a cero.")

        with session_scope() as session:
            repo_prod = ProductoRepository(session)
            repo_stock = StockRepository(session)
            repo_mov = MovimientoRepository(session)

            # 1. Validar unicidad de SKU
            if repo_prod.obtener_por_sku(sku):
                raise DuplicateResourceException("Producto", "sku", sku)

            # 2. Validar unicidad de Código de Barras (si se proporcionó)
            if codigo_barras and repo_prod.obtener_por_codigo_barras(codigo_barras):
                raise DuplicateResourceException("Producto", "codigo_barras", codigo_barras)

            # 3. Crear el producto en 'inventario.productos'
            nuevo_producto = Producto(
                codigo_barras=codigo_barras or None,
                sku=sku,
                nombre=nombre,
                descripcion=datos_producto.get("descripcion"),
                id_categoria=datos_producto.get("id_categoria"),
                id_marca=datos_producto.get("id_marca"),
                id_unidad=datos_producto.get("id_unidad"),
                precio_compra=precio_compra,
                precio_venta=precio_venta,
                stock_minimo=int(datos_producto.get("stock_minimo", 0)),
                activo=bool(datos_producto.get("activo", True)),
            )
            producto_guardado = repo_prod.create(nuevo_producto)

            # 4. Inicializar tabla 'inventario.inventario'
            repo_stock.inicializar_stock(producto_guardado.id_producto, stock_inicial)

            # 5. Si hay stock inicial > 0, registrar en el Kardex
            if stock_inicial > 0:
                repo_mov.registrar_movimiento(
                    id_producto=producto_guardado.id_producto,
                    tipo_movimiento=TipoMovimiento.ENTRADA.value,
                    cantidad=stock_inicial,
                    id_usuario=id_usuario_operador,
                    referencia="INVENTARIO_INICIAL",
                    observacion="Carga inicial de apertura de existencias en el sistema.",
                )

            logger.info(
                f"Producto '{producto_guardado.nombre}' (SKU: {sku}) creado con stock inicial: {stock_inicial}"
            )
            return producto_guardado

    def actualizar_producto(
        self, id_producto: int, datos_actualizacion: Dict[str, Any]
    ) -> Producto:
        """
        Actualiza los datos informativos y precios de un producto.
        """
        with session_scope() as session:
            repo_prod = ProductoRepository(session)
            producto = repo_prod.get_by_id(id_producto)

            if not producto:
                raise ResourceNotFoundException("Producto", id_producto)

            # Validar si cambió el SKU y si el nuevo ya existe
            nuevo_sku = datos_producto_sku = datos_actualizacion.get("sku")
            if nuevo_sku and nuevo_sku != producto.sku:
                if repo_prod.obtener_por_sku(nuevo_sku):
                    raise DuplicateResourceException("Producto", "sku", nuevo_sku)
                producto.sku = nuevo_sku

            # Validar si cambió el código de barras
            nuevo_barcode = datos_actualizacion.get("codigo_barras")
            if nuevo_barcode and nuevo_barcode != producto.codigo_barras:
                if repo_prod.obtener_por_codigo_barras(nuevo_barcode):
                    raise DuplicateResourceException("Producto", "codigo_barras", nuevo_barcode)
                producto.codigo_barras = nuevo_barcode

            # Actualizar campos editables
            if "nombre" in datos_actualizacion:
                producto.nombre = str(datos_actualizacion["nombre"]).strip()
            if "descripcion" in datos_actualizacion:
                producto.descripcion = datos_actualizacion["descripcion"]
            if "id_categoria" in datos_actualizacion:
                producto.id_categoria = datos_actualizacion["id_categoria"]
            if "id_marca" in datos_actualizacion:
                producto.id_marca = datos_actualizacion["id_marca"]
            if "id_unidad" in datos_actualizacion:
                producto.id_unidad = datos_actualizacion["id_unidad"]
            if "precio_compra" in datos_actualizacion:
                producto.precio_compra = Decimal(str(datos_actualizacion["precio_compra"]))
            if "precio_venta" in datos_actualizacion:
                producto.precio_venta = Decimal(str(datos_actualizacion["precio_venta"]))
            if "stock_minimo" in datos_actualizacion:
                producto.stock_minimo = int(datos_actualizacion["stock_minimo"])
            if "activo" in datos_actualizacion:
                producto.activo = bool(datos_actualizacion["activo"])

            logger.info(f"Producto ID {id_producto} actualizado correctamente.")
            return producto

    # ==========================================================================
    # 2. CONTROL DE STOCK Y MOVIMIENTOS MANUALES (KARDEX)
    # ==========================================================================
    def ajustar_stock_manual(
        self,
        id_producto: int,
        cantidad_ajuste: int,
        tipo_movimiento: str,
        motivo: str,
        id_usuario: int,
        referencia: Optional[str] = None,
    ) -> MovimientoInventario:
        """
        Permite a un bodeguero o administrador corregir el stock físico mediante
        un movimiento justificado de ENTRADA, SALIDA o AJUSTE con bloqueo pesimista.
        """
        tipos_validos = [t.value for t in TipoMovimiento]
        if tipo_movimiento not in tipos_validos:
            raise ValidationException(
                f"Tipo de movimiento inválido: '{tipo_movimiento}'. Válidos: {tipos_validos}"
            )

        if cantidad_ajuste <= 0:
            raise ValidationException("La cantidad a ajustar debe ser un número entero mayor a 0.")

        if not motivo or len(motivo.strip()) < 3:
            raise ValidationException("Debe proporcionar una justificación u observación para el ajuste.")

        with session_scope() as session:
            repo_prod = ProductoRepository(session)
            repo_stock = StockRepository(session)
            repo_mov = MovimientoRepository(session)

            producto = repo_prod.get_by_id(id_producto)
            if not producto:
                raise ResourceNotFoundException("Producto", id_producto)

            # Calcular delta: Salidas restan, Entradas suman
            delta = -cantidad_ajuste if tipo_movimiento in ["SALIDA", "DEVOLUCION"] else cantidad_ajuste

            # 1. Modificar stock con bloqueo pesimista y protección contra negativo
            repo_stock.modificar_stock(id_producto, delta)

            # 2. Registrar en el libro de Kardex
            movimiento = repo_mov.registrar_movimiento(
                id_producto=id_producto,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad_ajuste,
                id_usuario=id_usuario,
                referencia=referencia or "AJUSTE_MANUAL_BODEGA",
                observacion=motivo.strip(),
            )

            logger.info(
                f"Ajuste de inventario aplicado a producto ID {id_producto}: {tipo_movimiento} de {cantidad_ajuste} unid."
            )
            return movimiento

    # ==========================================================================
    # 3. CONSULTAS Y BÚSQUEDAS (Lecturas de Catálogo)
    # ==========================================================================
    def obtener_producto_por_id(self, id_producto: int) -> Producto:
        """Retorna el producto con sus relaciones o lanza ResourceNotFoundException."""
        with session_scope() as session:
            repo = ProductoRepository(session)
            producto = repo.obtener_por_id(id_producto)
            if not producto:
                raise ResourceNotFoundException("Producto", id_producto)
            return producto

    def buscar_productos(
        self,
        termino: str,
        id_categoria: Optional[int] = None,
        solo_activos: Optional[bool] = None,
        limit: int = 25,
    ) -> Sequence[Producto]:
        """Búsqueda rápida para autocompletado en UI con filtros opcionales."""
        with session_scope() as session:
            repo = ProductoRepository(session)
            return repo.buscar_por_termino(
                termino=termino,
                id_categoria=id_categoria,
                solo_activos=solo_activos,
                limit=limit,
            )

    def listar_productos(
        self,
        id_categoria: Optional[int] = None,
        solo_activos: Optional[bool] = True,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Producto]:
        """Listado paginado de productos según filtro de categoría y estado."""
        with session_scope() as session:
            repo = ProductoRepository(session)
            return repo.listar_productos(
                id_categoria=id_categoria,
                solo_activos=solo_activos,
                skip=skip,
                limit=limit,
            )

    def listar_productos_activos(
        self, id_categoria: Optional[int] = None, skip: int = 0, limit: int = 100
    ) -> Sequence[Producto]:
        """Listado paginado de productos activos."""
        return self.listar_productos(
            id_categoria=id_categoria, solo_activos=True, skip=skip, limit=limit
        )

    def listar_categorias_activas(self) -> Sequence[Categoria]:
        """Retorna todas las categorías habilitadas para poblar filtros y formularios."""
        with session_scope() as session:
            repo_cat = CategoriaRepository(session)
            return repo_cat.listar_activas()

    def obtener_alertas_stock_minimo(self) -> Sequence[Producto]:
        """Obtiene productos con existencias por debajo del umbral de stock mínimo."""
        with session_scope() as session:
            repo = ProductoRepository(session)
            return repo.listar_bajo_stock_minimo()

    def obtener_historial_kardex(
        self, id_producto: int, skip: int = 0, limit: int = 100
    ) -> Sequence[MovimientoInventario]:
        """Retorna los movimientos de Kardex del producto."""
        with session_scope() as session:
            repo_mov = MovimientoRepository(session)
            return repo_mov.obtener_historial_por_producto(id_producto, skip, limit)
