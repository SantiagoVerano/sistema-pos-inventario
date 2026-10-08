"""
Página de Registro de Compras y Abastecimiento (app/ui/pages/compras_page.py)

Responsabilidad Arquitectónica:
-------------------------------
Vista de registro de compras a proveedores en PySide6:
1. Selección y alta rápida de proveedores.
2. Formulario de carga de ítems recibidos (cantidad y costo de compra unitario).
3. Tabla temporal de la orden de compra antes de confirmar.
4. Totalización y botón de confirmación de ingreso a bodega.
5. Conexión con 'ComprasController'.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.controllers.compras.compras_controller import ComprasController
from app.database.models.compras.proveedor import Proveedor
from app.database.models.inventario.producto import Producto
from app.services.inventario.inventario_service import InventarioService
from app.services.seguridad.auth_service import UsuarioAutenticado
from app.ui.styles.theme import PALETA, TEMA_GLOBAL_QSS


# ==============================================================================
# DIÁLOGO MODAL: NUEVO PROVEEDOR
# ==============================================================================
class NuevoProveedorDialog(QDialog):
    """Modal para registro de un nuevo proveedor comercial."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar Proveedor")
        self.setFixedSize(380, 420)
        self.setStyleSheet(TEMA_GLOBAL_QSS)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Razón Social (*):"))
        self.txt_razon = QLineEdit()
        self.txt_razon.setPlaceholderText("ej: Distribuidora Central S.A.")
        layout.addWidget(self.txt_razon)

        layout.addWidget(QLabel("NIT / RUC / Identificación:"))
        self.txt_nit = QLineEdit()
        self.txt_nit.setPlaceholderText("ej: 900123456-1")
        layout.addWidget(self.txt_nit)

        layout.addWidget(QLabel("Teléfono:"))
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("ej: +57 300 1234567")
        layout.addWidget(self.txt_telefono)

        layout.addWidget(QLabel("Correo Electrónico:"))
        self.txt_correo = QLineEdit()
        self.txt_correo.setPlaceholderText("ej: ventas@distribuidora.com")
        layout.addWidget(self.txt_correo)

        layout.addWidget(QLabel("Dirección:"))
        self.txt_direccion = QLineEdit()
        self.txt_direccion.setPlaceholderText("ej: Calle 10 # 20-30")
        layout.addWidget(self.txt_direccion)

        layout_btns = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setObjectName("btn_primary")

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar.clicked.connect(self.validar_y_aceptar)

        layout_btns.addWidget(self.btn_cancelar)
        layout_btns.addWidget(self.btn_guardar)
        layout.addLayout(layout_btns)

    def validar_y_aceptar(self) -> None:
        if not self.txt_razon.text().strip():
            QMessageBox.warning(self, "Validación", "La razón social es obligatoria.")
            return
        self.accept()

    def obtener_datos(self) -> dict:
        return {
            "razon_social": self.txt_razon.text().strip(),
            "nit": self.txt_nit.text().strip() or None,
            "telefono": self.txt_telefono.text().strip() or None,
            "correo": self.txt_correo.text().strip() or None,
            "direccion": self.txt_direccion.text().strip() or None,
        }


# ==============================================================================
# PÁGINA PRINCIPAL DE COMPRAS
# ==============================================================================
class ComprasPage(QWidget):
    """Página para formulación de órdenes de compra e ingreso de existencias."""

    def __init__(
        self,
        usuario_actual: UsuarioAutenticado,
        compras_controller: Optional[ComprasController] = None,
    ) -> None:
        super().__init__()
        self.usuario_actual = usuario_actual
        self.compras_controller = compras_controller or ComprasController()
        self.inventario_service = InventarioService()

        self._items_compra: List[Dict[str, Any]] = []
        self._proveedores: List[Proveedor] = []
        self._productos: List[Producto] = []

        self.init_ui()
        self.conectar_senales()
        self.cargar_datos_iniciales()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # 1. Panel de Proveedor
        card_prov = QFrame()
        card_prov.setObjectName("card")
        layout_prov = QHBoxLayout(card_prov)

        layout_prov.addWidget(QLabel("Proveedor (*):"))
        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.setFixedHeight(38)
        layout_prov.addWidget(self.cmb_proveedor, stretch=70)

        self.btn_nuevo_prov = QPushButton("➕ Nuevo Proveedor")
        self.btn_nuevo_prov.setFixedHeight(38)
        layout_prov.addWidget(self.btn_nuevo_prov)

        layout.addWidget(card_prov)

        # 2. Panel de Selección de Producto y Costo
        card_item = QFrame()
        card_item.setObjectName("card")
        layout_item = QHBoxLayout(card_item)

        layout_item.addWidget(QLabel("Producto:"))
        self.cmb_producto = QComboBox()
        self.cmb_producto.setFixedHeight(38)
        layout_item.addWidget(self.cmb_producto, stretch=45)

        layout_item.addWidget(QLabel("Cant:"))
        self.spn_cant = QSpinBox()
        self.spn_cant.setRange(1, 999999)
        self.spn_cant.setValue(10)
        self.spn_cant.setFixedHeight(38)
        layout_item.addWidget(self.spn_cant)

        layout_item.addWidget(QLabel("Costo Unitario ($):"))
        self.spn_costo = QDoubleSpinBox()
        self.spn_costo.setRange(0.0, 999999.0)
        self.spn_costo.setPrefix("$ ")
        self.spn_costo.setFixedHeight(38)
        layout_item.addWidget(self.spn_costo)

        self.btn_agregar_item = QPushButton("➕ Agregar a la Orden")
        self.btn_agregar_item.setObjectName("btn_blue")
        self.btn_agregar_item.setFixedHeight(38)
        layout_item.addWidget(self.btn_agregar_item)

        layout.addWidget(card_item)

        # 3. Tabla de Ítems de la Compra
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "ID Producto", "Producto", "Cantidad", "Costo Unitario", "Subtotal"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.setColumnHidden(0, True)
        layout.addWidget(self.tabla)

        # 4. Pie de Página: Totales y Botón Confirmar
        card_totales = QFrame()
        card_totales.setObjectName("card")
        layout_totales = QHBoxLayout(card_totales)

        self.lbl_total = QLabel("TOTAL COMPRA: $0.00")
        self.lbl_total.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {PALETA['accent_primary']};")
        layout_totales.addWidget(self.lbl_total)
        layout_totales.addStretch()

        self.btn_limpiar = QPushButton("Limpiar")
        self.btn_limpiar.setFixedHeight(42)
        layout_totales.addWidget(self.btn_limpiar)

        self.btn_procesar = QPushButton("📥 Registrar Compra e Ingresar a Bodega")
        self.btn_procesar.setObjectName("btn_primary")
        self.btn_procesar.setFixedHeight(42)
        layout_totales.addWidget(self.btn_procesar)

        layout.addWidget(card_totales)

    def conectar_senales(self) -> None:
        self.btn_nuevo_prov.clicked.connect(self.on_nuevo_proveedor)
        self.btn_agregar_item.clicked.connect(self.on_agregar_item)
        self.btn_limpiar.clicked.connect(self.limpiar_formulario)
        self.btn_procesar.clicked.connect(self.on_procesar_compra)
        self.cmb_producto.currentIndexChanged.connect(self.on_cambio_producto)

        # Señales del Controlador
        self.compras_controller.proveedores_actualizados.connect(self.on_proveedores_actualizados)
        self.compras_controller.operacion_exitosa.connect(lambda msg: QMessageBox.information(self, "Éxito", msg))
        self.compras_controller.operacion_fallida.connect(lambda msg: QMessageBox.critical(self, "Error", msg))

    def cargar_datos_iniciales(self) -> None:
        self.compras_controller.cargar_proveedores()
        self._productos = list(self.inventario_service.listar_productos_activos())
        self.cmb_producto.clear()
        for prod in self._productos:
            self.cmb_producto.addItem(f"{prod.nombre} (SKU: {prod.sku})", prod.id_producto)

    def on_proveedores_actualizados(self, proveedores: List[Proveedor]) -> None:
        self._proveedores = proveedores
        self.cmb_proveedor.clear()
        for prov in proveedores:
            self.cmb_proveedor.addItem(prov.razon_social, prov.id_proveedor)

    def on_cambio_producto(self, index: int) -> None:
        if 0 <= index < len(self._productos):
            prod = self._productos[index]
            self.spn_costo.setValue(float(prod.precio_compra))

    def on_nuevo_proveedor(self) -> None:
        dlg = NuevoProveedorDialog(self)
        if dlg.exec():
            datos = dlg.obtener_datos()
            self.compras_controller.registrar_proveedor(
                razon_social=datos["razon_social"],
                nit=datos["nit"],
                telefono=datos["telefono"],
                correo=datos["correo"],
                direccion=datos["direccion"],
            )

    def on_agregar_item(self) -> None:
        idx_prod = self.cmb_producto.currentIndex()
        if idx_prod < 0 or idx_prod >= len(self._productos):
            return

        prod = self._productos[idx_prod]
        cant = self.spn_cant.value()
        costo = Decimal(str(self.spn_costo.value()))
        subtotal = (Decimal(cant) * costo).quantize(Decimal("0.01"))

        # Agregar a lista interna
        self._items_compra.append({
            "id_producto": prod.id_producto,
            "nombre": prod.nombre,
            "cantidad": cant,
            "costo_unitario": costo,
            "subtotal": subtotal,
        })

        self.actualizar_tabla_items()

    def actualizar_tabla_items(self) -> None:
        self.tabla.setRowCount(0)
        total_acum = Decimal("0.00")

        for row, item in enumerate(self._items_compra):
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(str(item["id_producto"])))
            self.tabla.setItem(row, 1, QTableWidgetItem(item["nombre"]))
            self.tabla.setItem(row, 2, QTableWidgetItem(str(item["cantidad"])))
            self.tabla.setItem(row, 3, QTableWidgetItem(f"${item['costo_unitario']:.2f}"))
            self.tabla.setItem(row, 4, QTableWidgetItem(f"${item['subtotal']:.2f}"))
            total_acum += item["subtotal"]

        self.lbl_total.setText(f"TOTAL COMPRA: ${total_acum:.2f}")

    def limpiar_formulario(self) -> None:
        self._items_compra.clear()
        self.tabla.setRowCount(0)
        self.lbl_total.setText("TOTAL COMPRA: $0.00")

    def on_procesar_compra(self) -> None:
        if not self._items_compra:
            QMessageBox.warning(self, "Atención", "Debe agregar al menos un producto a la compra.")
            return

        id_prov = self.cmb_proveedor.currentData()
        if not id_prov:
            QMessageBox.warning(self, "Atención", "Debe seleccionar un proveedor.")
            return

        compra = self.compras_controller.procesar_orden_compra(
            id_proveedor=id_prov,
            id_usuario=self.usuario_actual.id_usuario,
            items=self._items_compra,
        )

        if compra:
            self.limpiar_formulario()
            self.cargar_datos_iniciales()
