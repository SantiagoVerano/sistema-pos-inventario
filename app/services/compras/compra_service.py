"""
Servicio de Gestión de Compras y Abastecimiento (app/services/compras/compra_service.py)

Responsabilidad Arquitectónica:
-------------------------------
Orquestar las operaciones de compras a proveedores e ingresos a bodega:
1. Registro y actualización de proveedores.
2. Procesamiento transaccional de compras y detalles.
3. Integración atómica con Inventario y Kardex (incremento de stock en compras completadas).
4. Anulación de compras con reversión segura de existencias en el Kardex.
5. Transaccionalidad atómica mediante 'session_scope()'.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence
from app.core.constants import EstadoCompra, TipoMovimiento
from app.core.exceptions import (
    DuplicateResourceException,
    InvalidOperationException,
    ResourceNotFoundException,
    ValidationException,
)
from app.core.logger import get_logger
from app.database.connection import session_scope
from app.database.models.compras.proveedor import Proveedor
from app.database.models.compras.compra import Compra
from app.database.repositories.compras.proveedor_repository import ProveedorRepository
from app.database.repositories.compras.compra_repository import CompraRepository
from app.database.repositories.inventario.producto_repository import ProductoRepository
from app.database.repositories.inventario.stock_repository import StockRepository
from app.database.repositories.inventario.movimiento_repository import MovimientoRepository

logger = get_logger(__name__)


class CompraService:
    """
    Servicio para el Módulo de Compras y Proveedores.
    """

    # ==========================================================================
    # 1. GESTIÓN DE PROVEEDORES
    # ==========================================================================
    def registrar_proveedor(
        self,
        razon_social: str,
        nit: Optional[str] = None,
        telefono: Optional[str] = None,
        correo: Optional[str] = None,
        direccion: Optional[str] = None,
    ) -> Proveedor:
        """Registra un nuevo proveedor validando duplicidad de NIT."""
        razon_limpia = razon_social.strip()
        nit_limpio = nit.strip() if nit else None

        if not razon_limpia:
            raise ValidationException("La razón social del proveedor es obligatoria.")

        with session_scope() as session:
            repo_prov = ProveedorRepository(session)

            if nit_limpio and repo_prov.obtener_por_nit(nit_limpio):
                raise DuplicateResourceException("Proveedor", "nit", nit_limpio)

            nuevo_prov = Proveedor(
                razon_social=razon_limpia,
                nit=nit_limpio,
                telefono=telefono.strip() if telefono else None,
                correo=correo.strip().lower() if correo else None,
                direccion=direccion.strip() if direccion else None,
                estado=True,
            )
            proveedor_guardado = repo_prov.create(nuevo_prov)
            logger.info(f"Proveedor '{proveedor_guardado.razon_social}' registrado con ID: {proveedor_guardado.id_proveedor}")
            return proveedor_guardado

    def listar_proveedores_activos(self) -> Sequence[Proveedor]:
        """Retorna todos los proveedores activos."""
        with session_scope() as session:
            repo_prov = ProveedorRepository(session)
            return repo_prov.listar_activos()

    def buscar_proveedores(self, termino: str) -> Sequence[Proveedor]:
        """Búsqueda rápida de proveedores por NIT o razón social."""
        with session_scope() as session:
            repo_prov = ProveedorRepository(session)
            return repo_prov.buscar_por_termino(termino)

    # ==========================================================================
    # 2. PROCESAMIENTO DE COMPRAS E INGRESO A BODEGA
    # ==========================================================================
    def procesar_compra(
        self,
        id_proveedor: int,
        id_usuario: int,
        items: List[Dict[str, Any]],
        impuestos: Optional[Decimal] = None,
        estado: str = EstadoCompra.COMPLETADA.value,
    ) -> Compra:
        """
        Registra una compra con sus líneas de detalle.
        Si el estado es COMPLETADA, incrementa el stock físico de cada producto
        y genera los asientos correspondientes en el Kardex de forma atómica.

        Estructura esperada en cada elemento de 'items':
            {
                "id_producto": int,
                "cantidad": int,
                "costo_unitario": Decimal | float | str
            }
        """
        if not items:
            raise ValidationException("La compra debe incluir al menos un producto.")

        if estado not in [e.value for e in EstadoCompra]:
            raise ValidationException(f"Estado de compra no válido: '{estado}'")

        with session_scope() as session:
            repo_prov = ProveedorRepository(session)
            repo_prod = ProductoRepository(session)
            repo_compra = CompraRepository(session)
            repo_stock = StockRepository(session)
            repo_mov = MovimientoRepository(session)

            # 1. Validar que el proveedor exista
            proveedor = repo_prov.get_by_id(id_proveedor)
            if not proveedor:
                raise ResourceNotFoundException("Proveedor", id_proveedor)

            # 2. Validar productos y calcular totales
            detalles_procesados: List[Dict[str, Any]] = []
            subtotal_acumulado = Decimal("0.00")

            for idx, item in enumerate(items, start=1):
                id_prod = int(item.get("id_producto", 0))
                cantidad = int(item.get("cantidad", 0))
                costo_u = Decimal(str(item.get("costo_unitario", "0.00")))

                if cantidad <= 0:
                    raise ValidationException(f"Línea #{idx}: La cantidad debe ser mayor a 0.")
                if costo_u < 0:
                    raise ValidationException(f"Línea #{idx}: El costo unitario no puede ser negativo.")

                producto = repo_prod.get_by_id(id_prod)
                if not producto:
                    raise ResourceNotFoundException("Producto", id_prod)

                subtotal_linea = (Decimal(cantidad) * costo_u).quantize(Decimal("0.01"))
                subtotal_acumulado += subtotal_linea

                detalles_procesados.append({
                    "id_producto": id_prod,
                    "cantidad": cantidad,
                    "costo_unitario": costo_u,
                    "subtotal": subtotal_linea,
                })

            monto_impuestos = impuestos if impuestos is not None else Decimal("0.00")
            total_general = (subtotal_acumulado + monto_impuestos).quantize(Decimal("0.01"))

            # 3. Guardar cabecera y detalles de compra
            compra = repo_compra.crear_compra(
                id_proveedor=id_proveedor,
                id_usuario=id_usuario,
                subtotal=subtotal_acumulado,
                impuestos=monto_impuestos,
                total=total_general,
                detalles_data=detalles_procesados,
                estado=estado,
            )

            # 4. Si la compra está COMPLETADA, ingresar existencias a Inventario y Kardex
            if estado == EstadoCompra.COMPLETADA.value:
                for det in detalles_procesados:
                    id_p = det["id_producto"]
                    cant = det["cantidad"]
                    costo = det["costo_unitario"]

                    # Actualizar stock físico
                    repo_stock.modificar_stock(id_p, cant)

                    # Actualizar último precio de compra en el catálogo
                    prod_obj = repo_prod.get_by_id(id_p)
                    if prod_obj:
                        prod_obj.precio_compra = costo

                    # Asiento en Kardex
                    repo_mov.registrar_movimiento(
                        id_producto=id_p,
                        tipo_movimiento=TipoMovimiento.ENTRADA.value,
                        cantidad=cant,
                        id_usuario=id_usuario,
                        referencia=f"COMPRA-#{compra.id_compra}",
                        observacion=f"Ingreso de mercancía por compra ID {compra.id_compra} (Proveedor: {proveedor.razon_social})",
                    )

            logger.info(f"Compra ID {compra.id_compra} procesada exitosamente. Total: {total_general}")
            return compra

    # ==========================================================================
    # 3. ANULACIÓN DE COMPRAS
    # ==========================================================================
    def anular_compra(
        self, id_compra: int, id_usuario_operador: int, motivo: str
    ) -> Compra:
        """
        Anula una compra previamente completada, revirtiendo el stock ingresado
        y dejando trazabilidad en el Kardex.
        """
        if not motivo or len(motivo.strip()) < 3:
            raise ValidationException("Debe proporcionar un motivo justificado para anular la compra.")

        with session_scope() as session:
            repo_compra = CompraRepository(session)
            repo_stock = StockRepository(session)
            repo_mov = MovimientoRepository(session)

            compra = repo_compra.obtener_por_id_con_detalles(id_compra)
            if not compra:
                raise ResourceNotFoundException("Compra", id_compra)

            if compra.estado == EstadoCompra.ANULADA.value:
                raise InvalidOperationException("La compra ya se encuentra anulada.")

            # Revertir stock si la compra fue completada
            if compra.estado == EstadoCompra.COMPLETADA.value:
                for detalle in compra.detalles:
                    # Descontar existencias ingresadas
                    repo_stock.modificar_stock(detalle.id_producto, -detalle.cantidad)

                    # Registrar salida en Kardex por anulación
                    repo_mov.registrar_movimiento(
                        id_producto=detalle.id_producto,
                        tipo_movimiento=TipoMovimiento.DEVOLUCION.value,
                        cantidad=detalle.cantidad,
                        id_usuario=id_usuario_operador,
                        referencia=f"ANULACION-COMPRA-#{compra.id_compra}",
                        observacion=f"Anulación de compra ID {compra.id_compra}. Motivo: {motivo.strip()}",
                    )

            compra.estado = EstadoCompra.ANULADA.value
            logger.info(f"Compra ID {id_compra} anulada correctamente.")
            return compra

    # ==========================================================================
    # 4. CONSULTAS DE COMPRAS
    # ==========================================================================
    def obtener_compra_por_id(self, id_compra: int) -> Compra:
        """Obtiene una compra con detalles, proveedor y usuario."""
        with session_scope() as session:
            repo = CompraRepository(session)
            compra = repo.obtener_por_id_con_detalles(id_compra)
            if not compra:
                raise ResourceNotFoundException("Compra", id_compra)
            return compra

    def listar_compras_por_rango_fechas(
        self, fecha_inicio: datetime, fecha_fin: datetime
    ) -> Sequence[Compra]:
        """Retorna compras realizadas dentro de un periodo."""
        with session_scope() as session:
            repo = CompraRepository(session)
            return repo.listar_por_rango_fechas(fecha_inicio, fecha_fin)
