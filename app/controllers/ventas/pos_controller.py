"""
Controlador del Terminal de Punto de Venta / POS (app/controllers/ventas/pos_controller.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar el estado interactivo del terminal POS en PySide6:
1. Carrito de compras en memoria (agregar, editar cantidad, eliminar ítem).
2. Procesamiento instantáneo de lecturas de código de barras desde lectores láser.
3. Validación interactiva de existencias físicas disponibles antes del cobro.
4. Cálculo en tiempo real de subtotales, impuestos, descuentos y cambio/vuelto.
5. Emisión de comprobante de venta y coordinación con 'VentaService'.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence
from PySide6.QtCore import QObject, Signal

from app.core.exceptions import AppException, InsufficientStockException
from app.core.logger import get_logger
from app.database.models.inventario.producto import Producto
from app.database.models.ventas.cliente import Cliente
from app.database.models.ventas.venta import Venta
from app.services.inventario.inventario_service import InventarioService
from app.services.ventas.venta_service import VentaService

logger = get_logger(__name__)


@dataclass
class ItemCarrito:
    """Representa una línea activa de producto en el carrito del terminal POS."""
    id_producto: int
    sku: str
    nombre: str
    precio_unitario: Decimal
    cantidad: int
    stock_disponible: int

    @property
    def subtotal(self) -> Decimal:
        return (Decimal(self.cantidad) * self.precio_unitario).quantize(Decimal("0.01"))


class POSController(QObject):
    """
    Controlador para el terminal de ventas POS y gestión de caja.
    """
    # Señales Qt
    carrito_actualizado = Signal(list, dict)  # Emite lista de ItemCarrito y diccionario de totales
    cliente_asignado = Signal(object)          # Emite el Cliente actual asignado a la venta
    venta_completada = Signal(object, dict)    # Emite Venta y desglose de pago (monto_recibido, cambio)
    venta_anulada = Signal(object)             # Emite Venta anulada
    producto_no_encontrado = Signal(str)       # Emite el código que no se encontró en catálogo
    stock_insuficiente = Signal(str)           # Emite mensaje con el producto sin stock suficiente
    operacion_exitosa = Signal(str)            # Emite mensaje informativo para UI
    operacion_fallida = Signal(str)            # Emite mensaje de error para UI

    def __init__(
        self,
        venta_service: Optional[VentaService] = None,
        inventario_service: Optional[InventarioService] = None,
    ) -> None:
        super().__init__()
        self._venta_service = venta_service or VentaService()
        self._inventario_service = inventario_service or InventarioService()

        # Estado en memoria del POS
        self._carrito: Dict[int, ItemCarrito] = {}  # Mapeo: id_producto -> ItemCarrito
        self._cliente_actual: Optional[Cliente] = None
        self._descuento_global: Decimal = Decimal("0.00")

    # ==========================================================================
    # 1. GESTIÓN DEL CLIENTE Y CARRITO DE VENTAS
    # ==========================================================================
    def obtener_cliente_por_defecto(self) -> Cliente:
        """Retorna el cliente genérico 'Cliente Rápido' (Consumidor Final)."""
        try:
            return self._venta_service.obtener_o_crear_cliente_rapido()
        except Exception as exc:
            logger.error(f"Error al obtener cliente rápido por defecto: {exc}", exc_info=True)
            return Cliente(
                id_cliente=1,
                tipo_documento="CC",
                numero_documento="00000000",
                nombre="Cliente",
                apellido="Rápido",
            )

    @property
    def cliente_actual(self) -> Cliente:
        if self._cliente_actual is None:
            self._cliente_actual = self.obtener_cliente_por_defecto()
        return self._cliente_actual

    def asignar_cliente(self, cliente: Optional[Cliente]) -> None:
        """Asigna o resetea el cliente asociado a la venta actual."""
        self._cliente_actual = cliente if cliente is not None else self.obtener_cliente_por_defecto()
        self.cliente_asignado.emit(self._cliente_actual)
        self._notificar_actualizacion_carrito()

    def buscar_clientes(self, termino: str) -> Sequence[Cliente]:
        """Búsqueda reactiva de clientes por cédula, nombre o apellido."""
        try:
            return self._venta_service.buscar_clientes(termino)
        except Exception as exc:
            logger.error(f"Error al buscar clientes: {exc}", exc_info=True)
            return []

    def listar_clientes_recientes(self) -> Sequence[Cliente]:
        """Retorna los clientes recientemente registrados para selección rápida."""
        try:
            return self._venta_service.listar_clientes_recientes()
        except Exception as exc:
            logger.error(f"Error al listar clientes: {exc}", exc_info=True)
            return []

    def registrar_cliente(
        self,
        numero_documento: str,
        nombre: str,
        apellido: Optional[str] = None,
        tipo_documento: str = "CC",
        telefono: Optional[str] = None,
        correo: Optional[str] = None,
        direccion: Optional[str] = None,
    ) -> Optional[Cliente]:
        """Crea un nuevo cliente en ventas.clientes y lo asigna inmediatamente a la venta."""
        try:
            nuevo_cli = self._venta_service.registrar_cliente(
                numero_documento=numero_documento,
                nombre=nombre,
                apellido=apellido,
                tipo_documento=tipo_documento,
                telefono=telefono,
                correo=correo,
                direccion=direccion,
            )
            self.asignar_cliente(nuevo_cli)
            self.operacion_exitosa.emit(
                f"Cliente '{nuevo_cli.nombre} {nuevo_cli.apellido or ''}' registrado y asignado."
            )
            return nuevo_cli
        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return None
        except Exception as exc:
            logger.error(f"Error al crear cliente: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error inesperado al registrar el cliente.")
            return None

    def obtener_categorias(self) -> Sequence[Any]:
        """Retorna las categorías activas para los selectores de productos en POS."""
        try:
            return self._inventario_service.listar_categorias_activas()
        except Exception as exc:
            logger.error(f"Error al obtener categorías en POS: {exc}", exc_info=True)
            return []

    def escanear_codigo_barras(self, codigo_barras: str) -> bool:
        """
        Busca un producto por código de barras escaneado y lo agrega automáticamente
        o incrementa su cantidad si ya estaba en el carrito.
        """
        codigo_limpio = codigo_barras.strip()
        if not codigo_limpio:
            return False

        try:
            # Buscar productos por coincidencia exacta
            productos = self._inventario_service.buscar_productos(termino=codigo_limpio, limit=5)
            producto_hallado = next(
                (p for p in productos if p.codigo_barras == codigo_limpio or p.sku == codigo_limpio),
                None
            )

            if not producto_hallado:
                logger.warning(f"Código de barras no encontrado en catálogo: {codigo_limpio}")
                self.producto_no_encontrado.emit(codigo_limpio)
                return False

            return self.agregar_producto(producto_hallado, cantidad=1)

        except Exception as exc:
            logger.error(f"Error al escanear código de barras: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error al procesar el código escaneado.")
            return False

    def agregar_producto(self, producto: Producto, cantidad: int = 1) -> bool:
        """Agrega un producto al carrito verificando existencias físicas preliminares."""
        if not producto.activo:
            self.operacion_fallida.emit(f"El producto '{producto.nombre}' está deshabilitado.")
            return False

        stock_disponible = producto.inventario.stock_actual if producto.inventario else 0

        # Verificar si ya está en el carrito
        if producto.id_producto in self._carrito:
            item_existente = self._carrito[producto.id_producto]
            nueva_cantidad = item_existente.cantidad + cantidad

            if nueva_cantidad > stock_disponible:
                msg = f"Stock insuficiente para '{producto.nombre}'. Disponible: {stock_disponible}, en carrito: {nueva_cantidad}."
                self.stock_insuficiente.emit(msg)
                return False

            item_existente.cantidad = nueva_cantidad
            item_existente.stock_disponible = stock_disponible
        else:
            if cantidad > stock_disponible:
                msg = f"Stock insuficiente para '{producto.nombre}'. Disponible: {stock_disponible}, solicitado: {cantidad}."
                self.stock_insuficiente.emit(msg)
                return False

            self._carrito[producto.id_producto] = ItemCarrito(
                id_producto=producto.id_producto,
                sku=producto.sku or "",
                nombre=producto.nombre,
                precio_unitario=producto.precio_venta,
                cantidad=cantidad,
                stock_disponible=stock_disponible,
            )

        self._notificar_actualizacion_carrito()
        return True

    def actualizar_cantidad(self, id_producto: int, nueva_cantidad: int) -> bool:
        """Modifica la cantidad de un ítem ya presente en el carrito."""
        if id_producto not in self._carrito:
            return False

        if nueva_cantidad <= 0:
            return self.remover_producto(id_producto)

        item = self._carrito[id_producto]
        if nueva_cantidad > item.stock_disponible:
            msg = f"Stock insuficiente para '{item.nombre}'. Disponible: {item.stock_disponible}, solicitado: {nueva_cantidad}."
            self.stock_insuficiente.emit(msg)
            return False

        item.cantidad = nueva_cantidad
        self._notificar_actualizacion_carrito()
        return True

    def remover_producto(self, id_producto: int) -> bool:
        """Elimina una línea del carrito."""
        if id_producto in self._carrito:
            del self._carrito[id_producto]
            self._notificar_actualizacion_carrito()
            return True
        return False

    def aplicar_descuento_global(self, descuento: Decimal) -> None:
        """Aplica un descuento global en valor monetario al total de la venta."""
        self._descuento_global = max(Decimal("0.00"), descuento)
        self._notificar_actualizacion_carrito()

    def vaciar_carrito(self) -> None:
        """Limpia todos los productos del carrito y resetea el cliente a Cliente Rápido."""
        self._carrito.clear()
        self._descuento_global = Decimal("0.00")
        self.asignar_cliente(self.obtener_cliente_por_defecto())
        self._notificar_actualizacion_carrito()

    def calcular_totales(self) -> Dict[str, Decimal]:
        """Calcula el subtotal acumulado, descuento y total a cobrar."""
        subtotal = sum((item.subtotal for item in self._carrito.values()), Decimal("0.00"))
        descuento = min(self._descuento_global, subtotal)
        total = (subtotal - descuento).quantize(Decimal("0.01"))

        return {
            "subtotal": subtotal,
            "descuento": descuento,
            "impuestos": Decimal("0.00"),
            "total": total,
            "items_count": len(self._carrito),
            "unidades_count": sum(item.cantidad for item in self._carrito.values()),
        }

    def _notificar_actualizacion_carrito(self) -> None:
        """Emite la señal Qt con la lista de ítems y el resumen financiero para la vista."""
        lista_items = list(self._carrito.values())
        totales = self.calcular_totales()
        self.carrito_actualizado.emit(lista_items, totales)

    # ==========================================================================
    # 2. PROCESAMIENTO DE COBRO Y EMISIÓN DE VENTA
    # ==========================================================================
    def procesar_cobro(
        self,
        id_usuario_cajero: int,
        monto_recibido: Decimal,
    ) -> Optional[Venta]:
        """
        Ejecuta la venta en la base de datos:
        1. Valida el efectivo recibido frente al total.
        2. Bloquea pesimistamente el stock en PostgreSQL.
        3. Genera la venta y el movimiento en Kardex.
        4. Calcula el vuelto exacto y limpia el carrito.
        """
        if not self._carrito:
            self.operacion_fallida.emit("El carrito de compras está vacío.")
            return None

        totales = self.calcular_totales()
        total_a_cobrar = totales["total"]

        if monto_recibido < total_a_cobrar:
            faltante = total_a_cobrar - monto_recibido
            self.operacion_fallida.emit(f"Monto recibido insuficiente. Faltan ${faltante:.2f}")
            return None

        cambio_vuelto = (monto_recibido - total_a_cobrar).quantize(Decimal("0.01"))

        # Preparar ítems para el servicio
        items_payload: List[Dict[str, Any]] = [
            {
                "id_producto": item.id_producto,
                "cantidad": item.cantidad,
                "precio_unitario": item.precio_unitario,
            }
            for item in self._carrito.values()
        ]

        try:
            cliente = self.cliente_actual
            id_cliente = cliente.id_cliente if cliente else None

            venta_procesada = self._venta_service.procesar_venta(
                id_usuario_cajero=id_usuario_cajero,
                items=items_payload,
                id_cliente=id_cliente,
                descuento=totales["descuento"],
                impuestos=totales["impuestos"],
            )

            # Notificar éxito y entregar desglose de vuelto a la UI
            desglose_cobro = {
                "monto_recibido": monto_recibido,
                "total_pagado": total_a_cobrar,
                "cambio_vuelto": cambio_vuelto,
            }
            self.venta_completada.emit(venta_procesada, desglose_cobro)
            self.operacion_exitosa.emit(
                f"Venta #{venta_procesada.id_venta} completada. Cambio / Vuelto: ${cambio_vuelto:.2f}"
            )

            # Limpiar carrito para la siguiente transacción
            self.vaciar_carrito()
            return venta_procesada

        except InsufficientStockException as exc:
            self.stock_insuficiente.emit(exc.mensaje)
            return None
        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return None
        except Exception as exc:
            logger.error(f"Error inesperado al procesar cobro en POS: {exc}", exc_info=True)
            self.operacion_fallida.emit("Ocurrió un error inesperado al procesar la venta.")
            return None

    def anular_venta(
        self, id_venta: int, id_usuario_supervisor: int, motivo: str
    ) -> Optional[Venta]:
        """Anula una venta y reintegra las existencias a almacén."""
        try:
            venta = self._venta_service.anular_venta(
                id_venta=id_venta,
                id_usuario_supervisor=id_usuario_supervisor,
                motivo=motivo,
            )
            self.venta_anulada.emit(venta)
            self.operacion_exitosa.emit(f"Venta #{id_venta} anulada exitosamente.")
            return venta
        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return None
        except Exception as exc:
            logger.error(f"Error al anular venta en POSController: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error inesperado al anular la venta.")
            return None
