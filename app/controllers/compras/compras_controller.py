"""
Controlador de Compras y Abastecimiento (app/controllers/compras/compras_controller.py)

Responsabilidad Arquitectónica:
-------------------------------
Conectar las vistas de registro de compras a proveedores, catálogo de compras y gestión
de proveedores con 'CompraService'.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence
from PySide6.QtCore import QObject, Signal

from app.core.exceptions import AppException
from app.core.logger import get_logger
from app.database.models.compras.proveedor import Proveedor
from app.database.models.compras.compra import Compra
from app.services.compras.compra_service import CompraService

logger = get_logger(__name__)


class ComprasController(QObject):
    """
    Controlador para el flujo de compras a proveedores y recepción de mercancía.
    """
    # Señales Qt
    proveedores_actualizados = Signal(list)  # Emite lista de Proveedor
    compra_procesada = Signal(object)        # Emite Compra recién completada
    compra_anulada = Signal(object)          # Emite Compra recién anulada
    operacion_exitosa = Signal(str)          # Emite mensaje informativo para UI
    operacion_fallida = Signal(str)          # Emite mensaje de error para UI

    def __init__(self, compra_service: Optional[CompraService] = None) -> None:
        super().__init__()
        self._service = compra_service or CompraService()

    def cargar_proveedores(self) -> Sequence[Proveedor]:
        """Obtiene la lista de proveedores activos para combos de selección en UI."""
        try:
            proveedores = self._service.listar_proveedores_activos()
            self.proveedores_actualizados.emit(list(proveedores))
            return proveedores
        except Exception as exc:
            logger.error(f"Error al cargar proveedores: {exc}", exc_info=True)
            return []

    def registrar_proveedor(
        self,
        razon_social: str,
        nit: Optional[str] = None,
        telefono: Optional[str] = None,
        correo: Optional[str] = None,
        direccion: Optional[str] = None,
    ) -> Optional[Proveedor]:
        """Registra un nuevo proveedor en el sistema."""
        try:
            prov = self._service.registrar_proveedor(
                razon_social=razon_social,
                nit=nit,
                telefono=telefono,
                correo=correo,
                direccion=direccion,
            )
            self.operacion_exitosa.emit(f"Proveedor '{prov.razon_social}' registrado con éxito.")
            self.cargar_proveedores()
            return prov
        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return None
        except Exception as exc:
            logger.error(f"Error al registrar proveedor: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error inesperado al guardar el proveedor.")
            return None

    def procesar_orden_compra(
        self,
        id_proveedor: int,
        id_usuario: int,
        items: List[Dict[str, Any]],
        impuestos: Optional[Decimal] = None,
    ) -> Optional[Compra]:
        """Registra la compra e incrementa existencias en el inventario."""
        try:
            compra = self._service.procesar_compra(
                id_proveedor=id_proveedor,
                id_usuario=id_usuario,
                items=items,
                impuestos=impuestos,
            )
            self.compra_procesada.emit(compra)
            self.operacion_exitosa.emit(
                f"Compra #{compra.id_compra} registrada exitosamente por un total de ${compra.total}."
            )
            return compra
        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return None
        except Exception as exc:
            logger.error(f"Error al procesar compra: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error inesperado al registrar la compra.")
            return None

    def anular_compra(
        self, id_compra: int, id_usuario: int, motivo: str
    ) -> Optional[Compra]:
        """Anula una compra y revierte el stock físico."""
        try:
            compra = self._service.anular_compra(
                id_compra=id_compra,
                id_usuario_operador=id_usuario,
                motivo=motivo,
            )
            self.compra_anulada.emit(compra)
            self.operacion_exitosa.emit(f"Compra #{id_compra} anulada y existencias revertidas.")
            return compra
        except AppException as exc:
            self.operacion_fallida.emit(exc.mensaje)
            return None
        except Exception as exc:
            logger.error(f"Error al anular compra: {exc}", exc_info=True)
            self.operacion_fallida.emit("Error inesperado al anular la compra.")
            return None
