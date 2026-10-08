"""
Servicio de Ventas y Punto de Venta / POS (app/services/ventas/venta_service.py)

Responsabilidad Arquitectónica:
-------------------------------
Orquestar las transacciones del terminal POS:
1. Gestión de clientes para facturación.
2. Cumplimiento de la Regla N° 1: Validación estricta y bloqueo pesimista contra stock negativo.
3. Cumplimiento de la Regla N° 2: Asiento automático de salida en el Kardex Perpetuo.
4. Anulación de ventas con reintegro seguro de existencias físicas.
5. Cuadre y resumen de caja por cajero y turno.
6. Transaccionalidad atómica mediante 'session_scope()'.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence
from app.core.constants import EstadoVenta, TipoMovimiento
from app.core.exceptions import (
    DuplicateResourceException,
    InsufficientStockException,
    InvalidOperationException,
    ResourceNotFoundException,
    ValidationException,
)
from app.core.logger import get_logger
from app.database.connection import session_scope
from app.database.models.ventas.cliente import Cliente
from app.database.models.ventas.venta import Venta
from app.database.repositories.ventas.cliente_repository import ClienteRepository
from app.database.repositories.ventas.venta_repository import VentaRepository
from app.database.repositories.inventario.producto_repository import ProductoRepository
from app.database.repositories.inventario.stock_repository import StockRepository
from app.database.repositories.inventario.movimiento_repository import MovimientoRepository

logger = get_logger(__name__)


class VentaService:
    """
    Servicio para el Módulo de Ventas y Terminal POS.
    """

    # ==========================================================================
    # 1. GESTIÓN DE CLIENTES
    # ==========================================================================
    def registrar_cliente(
        self,
        numero_documento: str,
        nombre: str,
        apellido: Optional[str] = None,
        tipo_documento: str = "DNI",
        telefono: Optional[str] = None,
        correo: Optional[str] = None,
        direccion: Optional[str] = None,
    ) -> Cliente:
        """Registra un nuevo cliente para facturación en POS."""
        doc_limpio = numero_documento.strip()
        nom_limpio = nombre.strip()

        if not doc_limpio:
            raise ValidationException("El número de documento del cliente es obligatorio.")
        if not nom_limpio:
            raise ValidationException("El nombre del cliente es obligatorio.")

        with session_scope() as session:
            repo_cliente = ClienteRepository(session)

            if repo_cliente.obtener_por_documento(doc_limpio):
                raise DuplicateResourceException("Cliente", "numero_documento", doc_limpio)

            nuevo_cli = Cliente(
                tipo_documento=tipo_documento.strip().upper(),
                numero_documento=doc_limpio,
                nombre=nom_limpio,
                apellido=apellido.strip() if apellido else None,
                telefono=telefono.strip() if telefono else None,
                correo=correo.strip().lower() if correo else None,
                direccion=direccion.strip() if direccion else None,
            )
            cliente_guardado = repo_cliente.create(nuevo_cli)
            logger.info(f"Cliente '{cliente_guardado.nombre}' registrado con ID: {cliente_guardado.id_cliente}")
            return cliente_guardado

    def buscar_clientes(self, termino: str, limit: int = 20) -> Sequence[Cliente]:
        """Búsqueda rápida de clientes por cédula/documento, nombre o apellido."""
        with session_scope() as session:
            repo_cliente = ClienteRepository(session)
            return repo_cliente.buscar_por_termino(termino, limit)

    def listar_clientes_recientes(self, limit: int = 50) -> Sequence[Cliente]:
        """Retorna la lista de clientes registrados recientemente."""
        with session_scope() as session:
            repo_cliente = ClienteRepository(session)
            return repo_cliente.listar_recientes(limit)

    def obtener_cliente_por_documento(self, numero_documento: str) -> Optional[Cliente]:
        """Busca un cliente por su número de identificación exacto."""
        with session_scope() as session:
            repo_cliente = ClienteRepository(session)
            return repo_cliente.obtener_por_documento(numero_documento)

    def obtener_o_crear_cliente_rapido(self) -> Cliente:
        """
        Garantiza la existencia del cliente por defecto 'Cliente Rápido' (Cédula: 00000000).
        Si no existe en 'ventas.clientes', lo crea automáticamente.
        """
        doc_rapido = "00000000"
        with session_scope() as session:
            repo_cliente = ClienteRepository(session)
            cli = repo_cliente.obtener_por_documento(doc_rapido)
            if not cli:
                cli = Cliente(
                    tipo_documento="CC",
                    numero_documento=doc_rapido,
                    nombre="Cliente",
                    apellido="Rápido",
                    telefono=None,
                    correo=None,
                    direccion="Venta Mostrador / Consumidor Final",
                )
                cli = repo_cliente.create(cli)
                logger.info("Cliente Rápido por defecto inicializado exitosamente en BD.")
            return cli

    # ==========================================================================
    # 2. MOTOR DE VENTAS POS (Con Bloqueo Pesimista y Kardex)
    # ==========================================================================
    def procesar_venta(
        self,
        id_usuario_cajero: int,
        items: List[Dict[str, Any]],
        id_cliente: Optional[int] = None,
        descuento: Decimal = Decimal("0.00"),
        impuestos: Optional[Decimal] = None,
    ) -> Venta:
        """
        Procesa una venta completa en el terminal POS:
        1. Bloquea pesimistamente las existencias de cada artículo con SELECT FOR UPDATE.
        2. Valida disponibilidad real de stock.
        3. Aplica descuento de existencias físicas.
        4. Inserta cabecera y líneas de venta.
        5. Genera asientos de salida en el Kardex.

        Estructura esperada en cada elemento de 'items':
            {
                "id_producto": int,
                "cantidad": int,
                "precio_unitario": Decimal | float | str (opcional, si no viene usa el de BD)
            }
        """
        if not items:
            raise ValidationException("La venta debe incluir al menos un producto.")

        if descuento < 0:
            raise ValidationException("El descuento no puede ser un valor negativo.")

        with session_scope() as session:
            repo_prod = ProductoRepository(session)
            repo_stock = StockRepository(session)
            repo_venta = VentaRepository(session)
            repo_mov = MovimientoRepository(session)
            repo_cli = ClienteRepository(session)

            # Validar cliente si fue provisto
            if id_cliente is not None:
                cliente = repo_cli.get_by_id(id_cliente)
                if not cliente:
                    raise ResourceNotFoundException("Cliente", id_cliente)

            detalles_procesados: List[Dict[str, Any]] = []
            subtotal_acumulado = Decimal("0.00")

            # Paso 1: Validación y Bloqueo Pesimista de Stock por cada ítem
            for idx, item in enumerate(items, start=1):
                id_prod = int(item.get("id_producto", 0))
                cantidad_solicitada = int(item.get("cantidad", 0))

                if cantidad_solicitada <= 0:
                    raise ValidationException(f"Línea #{idx}: La cantidad debe ser un número entero mayor a 0.")

                producto = repo_prod.get_by_id(id_prod)
                if not producto:
                    raise ResourceNotFoundException("Producto", id_prod)

                if not producto.activo:
                    raise InvalidOperationException(f"El producto '{producto.nombre}' se encuentra deshabilitado.")

                # Bloqueo pesimista de stock en PostgreSQL (SELECT ... FOR UPDATE)
                stock_record = repo_stock.obtener_con_bloqueo(id_prod)
                stock_disponible = stock_record.stock_actual if stock_record else 0

                # Regla N° 1: Prohibición Absoluta de Stock Negativo
                if stock_disponible < cantidad_solicitada:
                    raise InsufficientStockException(
                        id_producto=id_prod,
                        stock_disponible=stock_disponible,
                        cantidad_solicitada=cantidad_solicitada,
                        nombre_producto=producto.nombre,
                    )

                # Determinar precio unitario
                precio_u = (
                    Decimal(str(item["precio_unitario"]))
                    if "precio_unitario" in item
                    else producto.precio_venta
                )
                if precio_u < 0:
                    raise ValidationException(f"Línea #{idx}: El precio unitario no puede ser negativo.")

                subtotal_linea = (Decimal(cantidad_solicitada) * precio_u).quantize(Decimal("0.01"))
                subtotal_acumulado += subtotal_linea

                detalles_procesados.append({
                    "id_producto": id_prod,
                    "cantidad": cantidad_solicitada,
                    "precio_unitario": precio_u,
                    "subtotal": subtotal_linea,
                })

            # Validar que el descuento no supere el subtotal
            if descuento > subtotal_acumulado:
                raise ValidationException("El descuento no puede ser mayor que el subtotal de la venta.")

            monto_impuestos = impuestos if impuestos is not None else Decimal("0.00")
            total_general = (subtotal_acumulado + monto_impuestos - descuento).quantize(Decimal("0.01"))

            # Paso 2: Crear registro de Venta y DetalleVenta
            venta = repo_venta.crear_venta(
                id_cliente=id_cliente,
                id_usuario=id_usuario_cajero,
                subtotal=subtotal_acumulado,
                impuestos=monto_impuestos,
                descuento=descuento,
                total=total_general,
                detalles_data=detalles_procesados,
                estado=EstadoVenta.COMPLETADA.value,
            )

            # Paso 3: Debitar Stock y Asentar en Kardex Perpetuo
            for det in detalles_procesados:
                id_p = det["id_producto"]
                cant = det["cantidad"]

                # Descontar del inventario
                repo_stock.modificar_stock(id_p, -cant)

                # Registrar asiento inmutable en Kardex
                repo_mov.registrar_movimiento(
                    id_producto=id_p,
                    tipo_movimiento=TipoMovimiento.SALIDA.value,
                    cantidad=cant,
                    id_usuario=id_usuario_cajero,
                    referencia=f"VENTA-#{venta.id_venta}",
                    observacion=f"Despacho por venta POS ID {venta.id_venta}",
                )

            logger.info(f"Venta ID {venta.id_venta} completada con éxito. Total cobrado: {total_general}")
            return venta

    # ==========================================================================
    # 3. ANULACIÓN DE VENTAS
    # ==========================================================================
    def anular_venta(
        self, id_venta: int, id_usuario_supervisor: int, motivo: str
    ) -> Venta:
        """
        Anula una venta completada, reintegrando físicamente el stock a la bodega
        y generando un movimiento de DEVOLUCIÓN en el Kardex.
        """
        if not motivo or len(motivo.strip()) < 3:
            raise ValidationException("Debe ingresar un motivo justificado para la anulación de la venta.")

        with session_scope() as session:
            repo_venta = VentaRepository(session)
            repo_stock = StockRepository(session)
            repo_mov = MovimientoRepository(session)

            venta = repo_venta.obtener_por_id_con_detalles(id_venta)
            if not venta:
                raise ResourceNotFoundException("Venta", id_venta)

            if venta.estado == EstadoVenta.ANULADA.value:
                raise InvalidOperationException("La venta ya se encuentra anulada.")

            # Reintegrar productos al stock y al Kardex
            for detalle in venta.detalles:
                # Reingreso a inventario físico
                repo_stock.modificar_stock(detalle.id_producto, detalle.cantidad)

                # Asiento en Kardex por anulación
                repo_mov.registrar_movimiento(
                    id_producto=detalle.id_producto,
                    tipo_movimiento=TipoMovimiento.DEVOLUCION.value,
                    cantidad=detalle.cantidad,
                    id_usuario=id_usuario_supervisor,
                    referencia=f"ANULACION-VENTA-#{venta.id_venta}",
                    observacion=f"Anulación de venta POS ID {venta.id_venta}. Motivo: {motivo.strip()}",
                )

            venta.estado = EstadoVenta.ANULADA.value
            logger.info(f"Venta ID {id_venta} anulada exitosamente por usuario ID {id_usuario_supervisor}.")
            return venta

    # ==========================================================================
    # 4. CONSULTAS Y RESÚMENES DE CAJA
    # ==========================================================================
    def obtener_venta_por_id(self, id_venta: int) -> Venta:
        """Obtiene una venta con cliente, cajero y detalles."""
        with session_scope() as session:
            repo = VentaRepository(session)
            venta = repo.obtener_por_id_con_detalles(id_venta)
            if not venta:
                raise ResourceNotFoundException("Venta", id_venta)
            return venta

    def listar_ventas_por_rango_fechas(
        self, fecha_inicio: datetime, fecha_fin: datetime
    ) -> Sequence[Venta]:
        """Retorna las ventas realizadas dentro de un periodo."""
        with session_scope() as session:
            repo = VentaRepository(session)
            return repo.listar_por_rango_fechas(fecha_inicio, fecha_fin)

    def listar_ventas_recientes(self, limit: int = 100) -> Sequence[Venta]:
        """Retorna las ventas más recientes registradas."""
        with session_scope() as session:
            repo = VentaRepository(session)
            return repo.listar_recientes(limit)

    def obtener_resumen_cajero(self, id_usuario_cajero: int) -> Dict[str, Any]:
        """Calcula el total de ventas completadas y anuladas de un cajero."""
        with session_scope() as session:
            repo = VentaRepository(session)
            ventas = repo.listar_por_usuario(id_usuario_cajero)

            completadas = [v for v in ventas if v.estado == EstadoVenta.COMPLETADA.value]
            anuladas = [v for v in ventas if v.estado == EstadoVenta.ANULADA.value]

            total_recaudado = sum(v.total for v in completadas)

            return {
                "id_usuario_cajero": id_usuario_cajero,
                "cantidad_ventas_completadas": len(completadas),
                "cantidad_ventas_anuladas": len(anuladas),
                "total_recaudado": total_recaudado,
            }
