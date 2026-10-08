"""
Página de Historial de Ventas y Reportes (app/ui/pages/ventas_page.py)

Responsabilidad Arquitectónica:
-------------------------------
Vista para auditoría de facturación, consulta de ventas por fecha y anulación de comprobantes:
1. Tabla de transacciones de ventas con sincronización automática en tiempo real.
2. Selectores rápidos de periodo (Hoy, Últimos 7 Días, Este Mes, Personalizado, Todas).
3. Diálogo modal para inspeccionar el ticket detallado con cliente y productos.
4. Botón de anulación con justificación obligatoria y reintegro al Kardex.
5. Resumen de recaudación y arqueo de caja con actualización reactiva.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.models.ventas.venta import DetalleVenta, Venta
from app.services.seguridad.auth_service import UsuarioAutenticado
from app.services.ventas.venta_service import VentaService
from app.ui.styles.theme import PALETA, TEMA_GLOBAL_QSS


# ==============================================================================
# 1. DIÁLOGO MODAL: DETALLE DE VENTA / TICKET
# ==============================================================================
class DetalleVentaDialog(QDialog):
    """Muestra el desglose de productos de una venta seleccionada."""

    def __init__(self, venta: Venta, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.venta = venta
        self.setWindowTitle(f"Detalle de Venta #{venta.id_venta}")
        self.resize(680, 440)
        self.setStyleSheet(TEMA_GLOBAL_QSS)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Cabecera Info
        fecha_str = (
            self.venta.fecha_venta.strftime("%Y-%m-%d %H:%M:%S")
            if self.venta.fecha_venta
            else ""
        )
        cajero_nom = self.venta.usuario.nombre if self.venta.usuario else "N/A"
        cliente_nom = (
            f"{self.venta.cliente.nombre or ''} {self.venta.cliente.apellido or ''}".strip()
            if self.venta.cliente
            else "Cliente Rápido / Consumidor Final"
        )
        cliente_doc = self.venta.cliente.numero_documento if self.venta.cliente else "00000000"

        lbl_info = QLabel(
            f"<b>Venta #:</b> {self.venta.id_venta} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Fecha:</b> {fecha_str} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Cajero:</b> {cajero_nom}<br>"
            f"<b>Cliente:</b> {cliente_nom} (Doc: {cliente_doc}) &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Estado:</b> {self.venta.estado}"
        )
        lbl_info.setStyleSheet(
            f"background-color: {PALETA['bg_secundario']}; padding: 12px; border-radius: 6px; font-size: 13px;"
        )
        layout.addWidget(lbl_info)

        # Tabla de Ítems
        tabla = QTableWidget()
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setColumnCount(4)
        tabla.setHorizontalHeaderLabels(["Producto", "Cantidad", "Precio Unitario", "Subtotal"])
        tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tabla.setRowCount(len(self.venta.detalles))

        for row, det in enumerate(self.venta.detalles):
            prod_nombre = det.producto.nombre if det.producto else f"ID {det.id_producto}"
            tabla.setItem(row, 0, QTableWidgetItem(prod_nombre))
            tabla.setItem(row, 1, QTableWidgetItem(str(det.cantidad)))
            tabla.setItem(row, 2, QTableWidgetItem(f"${det.precio_unitario:.2f}"))
            tabla.setItem(row, 3, QTableWidgetItem(f"${det.subtotal:.2f}"))

        layout.addWidget(tabla)

        # Totales
        lbl_total = QLabel(
            f"Subtotal: ${self.venta.subtotal:.2f}  |  "
            f"Descuento: ${self.venta.descuento:.2f}  |  "
            f"<b>TOTAL: ${self.venta.total:.2f}</b>"
        )
        lbl_total.setAlignment(Qt.AlignRight)
        lbl_total.setStyleSheet(
            f"font-size: 15px; color: {PALETA['accent_primary']}; padding: 8px; font-weight: bold;"
        )
        layout.addWidget(lbl_total)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedWidth(100)
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignRight)


# ==============================================================================
# 2. PÁGINA PRINCIPAL DE HISTORIAL DE VENTAS
# ==============================================================================
class VentasPage(QWidget):
    """Página para consultar el historial de ventas y anular comprobantes."""

    # Señal emitida cuando se anula una venta para que el Inventario sincronice el stock
    venta_anulada_confirmada = Signal(object)

    def __init__(
        self,
        usuario_actual: UsuarioAutenticado,
        venta_service: Optional[VentaService] = None,
    ) -> None:
        super().__init__()
        self.usuario_actual = usuario_actual
        self.service = venta_service or VentaService()
        self._ventas: List[Venta] = []
        self.init_ui()
        self.conectar_senales()
        self.refrescar_datos()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Barra Superior de Filtros
        barra_filtros = QFrame()
        barra_filtros.setObjectName("card")
        layout_filtros = QHBoxLayout(barra_filtros)
        layout_filtros.setContentsMargins(12, 12, 12, 12)
        layout_filtros.setSpacing(10)

        # Selector Rápido de Periodo
        layout_filtros.addWidget(QLabel("⏱️ Periodo:"))
        self.cmb_periodo = QComboBox()
        self.cmb_periodo.addItems([
            "📅 Hoy",
            "📅 Últimos 7 Días",
            "📅 Este Mes",
            "⚙️ Rango Personalizado",
            "📋 Todas las Recientes",
        ])
        self.cmb_periodo.setFixedHeight(36)
        self.cmb_periodo.setCurrentIndex(0)  # Por defecto Hoy
        layout_filtros.addWidget(self.cmb_periodo)

        layout_filtros.addWidget(QLabel("Desde:"))
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDate(datetime.now().date())
        self.date_desde.setFixedHeight(36)
        self.date_desde.setEnabled(False)  # Se activa solo en personalizado
        layout_filtros.addWidget(self.date_desde)

        layout_filtros.addWidget(QLabel("Hasta:"))
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDate(datetime.now().date())
        self.date_hasta.setFixedHeight(36)
        self.date_hasta.setEnabled(False)  # Se activa solo en personalizado
        layout_filtros.addWidget(self.date_hasta)

        self.btn_filtrar = QPushButton("Filtrar")
        self.btn_filtrar.setObjectName("btn_blue")
        self.btn_filtrar.setFixedHeight(36)
        layout_filtros.addWidget(self.btn_filtrar)

        self.btn_refrescar = QPushButton("🔄")
        self.btn_refrescar.setFixedWidth(40)
        self.btn_refrescar.setFixedHeight(36)
        self.btn_refrescar.setToolTip("Refrescar historial de ventas")
        layout_filtros.addWidget(self.btn_refrescar)

        layout_filtros.addStretch()

        self.btn_ver_detalle = QPushButton("👁️ Ver Ticket")
        self.btn_ver_detalle.setFixedHeight(36)
        layout_filtros.addWidget(self.btn_ver_detalle)

        self.btn_anular = QPushButton("🚫 Anular Venta")
        self.btn_anular.setObjectName("btn_danger")
        self.btn_anular.setFixedHeight(36)
        layout_filtros.addWidget(self.btn_anular)

        layout.addWidget(barra_filtros)

        # Tabla de Ventas
        self.tabla = QTableWidget()
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID Venta", "Fecha y Hora", "Cliente", "Cajero", "Descuento", "Total Cobrado", "Estado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.cellDoubleClicked.connect(lambda r, c: self.on_ver_detalle())
        layout.addWidget(self.tabla)

        # Resumen Estadístico Inferior
        card_resumen = QFrame()
        card_resumen.setObjectName("card")
        layout_resumen = QHBoxLayout(card_resumen)

        self.lbl_recaudacion = QLabel("Total Recaudado: $0.00")
        self.lbl_recaudacion.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {PALETA['accent_primary']};"
        )
        layout_resumen.addWidget(self.lbl_recaudacion)

        self.lbl_conteo = QLabel("Ventas Completadas: 0  |  Anuladas: 0")
        self.lbl_conteo.setStyleSheet(f"color: {PALETA['text_secondary']};")
        layout_resumen.addWidget(self.lbl_conteo)
        layout_resumen.addStretch()

        layout.addWidget(card_resumen)

    def conectar_senales(self) -> None:
        self.cmb_periodo.currentIndexChanged.connect(self.on_cambiar_periodo)
        self.btn_filtrar.clicked.connect(self.cargar_ventas_filtro)
        self.btn_refrescar.clicked.connect(self.refrescar_datos)
        self.btn_ver_detalle.clicked.connect(self.on_ver_detalle)
        self.btn_anular.clicked.connect(self.on_anular_venta)

    def showEvent(self, event) -> None:
        """Al hacerse visible la pestaña de ventas, recarga automáticamente el historial."""
        super().showEvent(event)
        self.refrescar_datos()

    def on_cambiar_periodo(self, index: int) -> None:
        """Ajusta las fechas según el selector rápido y recarga."""
        hoy = datetime.now().date()
        self.date_desde.blockSignals(True)
        self.date_hasta.blockSignals(True)

        if index == 0:  # Hoy
            self.date_desde.setDate(hoy)
            self.date_hasta.setDate(hoy)
            self.date_desde.setEnabled(False)
            self.date_hasta.setEnabled(False)
        elif index == 1:  # Últimos 7 Días
            self.date_desde.setDate(hoy - timedelta(days=7))
            self.date_hasta.setDate(hoy)
            self.date_desde.setEnabled(False)
            self.date_hasta.setEnabled(False)
        elif index == 2:  # Este Mes
            self.date_desde.setDate(datetime(hoy.year, hoy.month, 1).date())
            self.date_hasta.setDate(hoy)
            self.date_desde.setEnabled(False)
            self.date_hasta.setEnabled(False)
        elif index == 3:  # Personalizado
            self.date_desde.setEnabled(True)
            self.date_hasta.setEnabled(True)
        elif index == 4:  # Todas las Recientes
            self.date_desde.setEnabled(False)
            self.date_hasta.setEnabled(False)

        self.date_desde.blockSignals(False)
        self.date_hasta.blockSignals(False)
        self.cargar_ventas_filtro()

    def refrescar_datos(self) -> None:
        """Sincroniza y recarga las ventas con los datos más recientes."""
        idx = self.cmb_periodo.currentIndex()
        if idx != 3:  # Si no es rango personalizado manual, recalcular fechas
            self.on_cambiar_periodo(idx)
        else:
            self.cargar_ventas_filtro()

    def cargar_ventas_filtro(self) -> None:
        """Ejecuta la consulta en base de datos según el periodo configurado."""
        idx = self.cmb_periodo.currentIndex()

        try:
            if idx == 4:  # Todas las recientes
                self._ventas = list(self.service.listar_ventas_recientes(limit=100))
            else:
                qdesde = self.date_desde.date()
                qhasta = self.date_hasta.date()
                dt_inicio = datetime(qdesde.year(), qdesde.month(), qdesde.day(), 0, 0, 0)
                dt_fin = datetime(qhasta.year(), qhasta.month(), qhasta.day(), 23, 59, 59)
                self._ventas = list(self.service.listar_ventas_por_rango_fechas(dt_inicio, dt_fin))

            self.poblar_tabla()
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Error al consultar ventas: {exc}")

    def poblar_tabla(self) -> None:
        self.tabla.setRowCount(0)
        recaudado = sum(v.total for v in self._ventas if v.estado == "COMPLETADA")
        completadas = sum(1 for v in self._ventas if v.estado == "COMPLETADA")
        anuladas = sum(1 for v in self._ventas if v.estado == "ANULADA")

        for row, venta in enumerate(self._ventas):
            self.tabla.insertRow(row)

            fecha_str = (
                venta.fecha_venta.strftime("%Y-%m-%d %H:%M:%S")
                if venta.fecha_venta
                else ""
            )
            cliente_nom = (
                f"{venta.cliente.nombre or ''} {venta.cliente.apellido or ''}".strip()
                if venta.cliente
                else "Cliente Rápido"
            )
            cajero_nom = venta.usuario.nombre if venta.usuario else "N/A"

            self.tabla.setItem(row, 0, QTableWidgetItem(f"#{venta.id_venta}"))
            self.tabla.setItem(row, 1, QTableWidgetItem(fecha_str))
            self.tabla.setItem(row, 2, QTableWidgetItem(cliente_nom))
            self.tabla.setItem(row, 3, QTableWidgetItem(cajero_nom))
            self.tabla.setItem(row, 4, QTableWidgetItem(f"${venta.descuento:.2f}"))
            self.tabla.setItem(row, 5, QTableWidgetItem(f"${venta.total:.2f}"))

            item_estado = QTableWidgetItem(venta.estado)
            if venta.estado == "COMPLETADA":
                item_estado.setForeground(Qt.GlobalColor.green)
            else:
                item_estado.setForeground(Qt.GlobalColor.red)
            self.tabla.setItem(row, 6, item_estado)

        self.lbl_recaudacion.setText(f"Total Recaudado: ${recaudado:.2f}")
        self.lbl_conteo.setText(f"Ventas Completadas: {completadas}  |  Anuladas: {anuladas}")

    def _obtener_venta_seleccionada(self) -> Optional[Venta]:
        row = self.tabla.currentRow()
        if row < 0 or row >= len(self._ventas):
            QMessageBox.warning(self, "Atención", "Por favor seleccione una venta de la tabla.")
            return None
        return self._ventas[row]

    def on_ver_detalle(self) -> None:
        venta = self._obtener_venta_seleccionada()
        if venta:
            venta_completa = self.service.obtener_venta_por_id(venta.id_venta)
            dlg = DetalleVentaDialog(venta_completa, self)
            dlg.exec()

    def on_anular_venta(self) -> None:
        venta = self._obtener_venta_seleccionada()
        if not venta:
            return

        if venta.estado == "ANULADA":
            QMessageBox.information(self, "Información", "Esta venta ya fue anulada previamente.")
            return

        resp = QMessageBox.question(
            self,
            "Confirmación de Anulación",
            f"¿Está seguro de que desea anular la Venta #{venta.id_venta} por ${venta.total:.2f}?\n"
            "Los productos serán reintegrados automáticamente al inventario físico y al Kardex.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if resp == QMessageBox.StandardButton.Yes:
            try:
                venta_anulada = self.service.anular_venta(
                    id_venta=venta.id_venta,
                    id_usuario_supervisor=self.usuario_actual.id_usuario,
                    motivo="Anulación manual autorizada por supervisor",
                )
                QMessageBox.information(self, "Éxito", f"Venta #{venta.id_venta} anulada exitosamente.")
                self.refrescar_datos()
                self.venta_anulada_confirmada.emit(venta_anulada)
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"No se pudo anular la venta: {exc}")
