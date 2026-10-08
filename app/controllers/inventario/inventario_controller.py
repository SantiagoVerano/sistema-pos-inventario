"""
Controlador de Inventario y Catálogo (app/controllers/inventario/inventario_controller.py)

Responsabilidad Arquitectónica:
-------------------------------
Conectar la vista del catálogo, formularios de productos y diálogos de ajuste manual
con 'InventarioService'. Gestiona eventos de búsqueda, validaciones visuales y actualización
de tablas en PySide6.
"""

from typing import Any, Dict, List, Optional, Sequence
from PySide6.QtCore import QObject, Signal

from app.core.exceptions import AppException
from app.core.logger import get_logger
from app.database.models.inventario.categoria import Categoria
from app.database.models.inventario.producto import Producto
from app.database.models.inventario.movimiento_inventario import MovimientoInventario
from app.services.inventario.inventario_service import InventarioService

logger = get_logger(__name__)


class InventarioController(QObject):
    """
    Controlador para la gestión de productos, inventario físico y Kardex en PySide6.
    """
    # Señales Qt
    catalogo_actualizado = Signal(list)    # Emite lista de Producto para refrescar QTableView
    producto_creado = Signal(object)       # Emite Producto recién creado
    producto_actualizado = Signal(object)  # Emite Producto modificado
    ajuste_realizado = Signal(object)      # Emite MovimientoInventario recién asentado
    alerta_stock = Signal(list)            # Emite lista de productos bajo stock mínimo
    operacion_exitosa = Signal(str)        # Emite mensaje para QMessageBox informativo
    operacion_fallida = Signal(str)        # Emite mensaje de error para QMessageBox

    def __init__(self, inventario_service: Optional[InventarioService] = None) -> None:
        super().__init__()
        self._service = inventario_service or InventarioService()
        self._filtro_activo: Optional[bool] = True    # True: solo activos, False: inactivos, None: todos
        self._filtro_categoria: Optional[int] = None  # None: todas las categorías

    @property
    def filtro_activo(self) -> Optional[bool]:
        return self._filtro_activo

    @filtro_activo.setter
    def filtro_activo(self, valor: Optional[bool]) -> None:
        self._filtro_activo = valor

    @property
    def filtro_categoria(self) -> Optional[int]:
        return self._filtro_categoria

    @filtro_categoria.setter
    def filtro_categoria(self, valor: Optional[int]) -> None:
        self._filtro_categoria = valor

    def cambiar_filtro_estado(self, solo_activos: Optional[bool]) -> Sequence[Producto]:
        """Aplica un nuevo filtro de estado y recarga automáticamente el catálogo."""
        self._filtro_activo = solo_activos
        return self.cargar_catalogo()

    def cambiar_filtro_categoria(self, id_categoria: Optional[int]) -> Sequence[Producto]:
        """Aplica un filtro por categoría y recarga automáticamente el catálogo."""
        self._filtro_categoria = id_categoria
        return self.cargar_catalogo()

    def obtener_categorias(self) -> Sequence[Categoria]:
        """Obtiene las categorías activas para poblar combos en la interfaz."""
        try:
            return self._service.listar_categorias_activas()
        except Exception as exc:
            logger.error(f"Error al listar categorías en controller: {exc}", exc_info=True)
            return []

    def cargar_catalogo(self, skip: int = 0, limit: int = 100) -> Sequence[Producto]:
        """Carga la lista de productos respetando los filtros de estado y categoría activos."""
        try:
            productos = self._service.listar_productos(
                id_categoria=self._filtro_categoria,
                solo_activos=self._filtro_activo,
                skip=skip,
                limit=limit,
            )
            self.catalogo_actualizado.emit(list(productos))
            return productos
        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return []
        except Exception as exc:
            logger.error(f"Error al cargar catálogo: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error al cargar la lista de productos.")
            return []

    def buscar_productos(self, termino: str) -> Sequence[Producto]:
        """Búsqueda reactiva por nombre, SKU o código de barras respetando los filtros activos."""
        termino_limpio = termino.strip()
        if not termino_limpio:
            return self.cargar_catalogo()

        try:
            resultados = self._service.buscar_productos(
                termino=termino_limpio,
                id_categoria=self._filtro_categoria,
                solo_activos=self._filtro_activo,
            )
            self.catalogo_actualizado.emit(list(resultados))
            return resultados
        except Exception as exc:
            logger.error(f"Error en búsqueda de productos: {exc}", exc_info=True)
            return []

    def crear_producto(
        self,
        datos_formulario: Dict[str, Any],
        stock_inicial: int,
        id_usuario: int,
    ) -> Optional[Producto]:
        """Procesa el formulario de nuevo producto con su stock inicial y Kardex."""
        try:
            nuevo_prod = self._service.registrar_producto_con_stock_inicial(
                datos_producto=datos_formulario,
                stock_inicial=stock_inicial,
                id_usuario_operador=id_usuario,
            )
            self.producto_creado.emit(nuevo_prod)
            self.operacion_exitosa.emit(f"Producto '{nuevo_prod.nombre}' registrado con éxito.")
            self.cargar_catalogo()
            return nuevo_prod

        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return None
        except Exception as exc:
            logger.error(f"Error al crear producto: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error inesperado al guardar el producto.")
            return None

    def actualizar_producto(
        self, id_producto: int, datos_formulario: Dict[str, Any]
    ) -> Optional[Producto]:
        """Actualiza los datos de un producto existente."""
        try:
            prod_editado = self._service.actualizar_producto(
                id_producto=id_producto,
                datos_actualizacion=datos_formulario,
            )
            self.producto_actualizado.emit(prod_editado)
            self.operacion_exitosa.emit("Producto actualizado correctamente.")
            self.cargar_catalogo()
            return prod_editado

        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return None
        except Exception as exc:
            logger.error(f"Error al actualizar producto: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error inesperado al actualizar el producto.")
            return None

    def realizar_ajuste_stock(
        self,
        id_producto: int,
        cantidad_ajuste: int,
        tipo_movimiento: str,
        motivo: str,
        id_usuario: int,
    ) -> Optional[MovimientoInventario]:
        """Aplica una corrección física de stock con justificación en Kardex."""
        try:
            movimiento = self._service.ajustar_stock_manual(
                id_producto=id_producto,
                cantidad_ajuste=cantidad_ajuste,
                tipo_movimiento=tipo_movimiento,
                motivo=motivo,
                id_usuario=id_usuario,
            )
            self.ajuste_realizado.emit(movimiento)
            self.operacion_exitosa.emit(
                f"Ajuste ({tipo_movimiento} de {cantidad_ajuste} unid.) aplicado correctamente."
            )
            self.cargar_catalogo()
            return movimiento

        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return None
        except Exception as exc:
            logger.error(f"Error en ajuste de stock: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error inesperado al aplicar el ajuste de stock.")
            return None

    def cargar_alertas_stock(self) -> Sequence[Producto]:
        """Consulta los productos con existencias por debajo del umbral mínimo."""
        try:
            alertas = self._service.obtener_alertas_stock_minimo()
            self.alerta_stock.emit(list(alertas))
            return alertas
        except Exception as exc:
            logger.error(f"Error al cargar alertas de stock: {exc}", exc_info=True)
            return []

    def obtener_historial_kardex(
        self, id_producto: int, skip: int = 0, limit: int = 100
    ) -> Sequence[MovimientoInventario]:
        """Obtiene la bitácora de movimientos para mostrar en el diálogo de Kardex."""
        try:
            return self._service.obtener_historial_kardex(id_producto, skip, limit)
        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return []
        except Exception as exc:
            logger.error(f"Error al obtener Kardex: {exc}", exc_info=True)
            return []
