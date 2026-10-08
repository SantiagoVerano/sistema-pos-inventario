"""
Página de Gestión de Inventario y Catálogo (app/ui/pages/inventario_page.py)

Responsabilidad Arquitectónica:
-------------------------------
Vista del módulo de Inventario en PySide6:
1. Tabla de solo lectura del catálogo maestro (sin edición confusa de celdas).
2. Diálogo modal para creación de productos con stock inicial.
3. Diálogo modal 'EditarProductoDialog' para modificar precios, nombres, SKU y parámetros.
4. Diálogo modal para ajustes manuales de stock con justificación en Kardex.
5. Diálogo modal de auditoría histórica de Kardex por producto.
6. Doble clic en cualquier fila para editar rápidamente el producto.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence
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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.controllers.inventario.inventario_controller import InventarioController
from app.database.models.inventario.categoria import Categoria
from app.database.models.inventario.producto import Producto
from app.database.models.inventario.movimiento_inventario import MovimientoInventario
from app.services.seguridad.auth_service import UsuarioAutenticado
from app.ui.styles.theme import PALETA, TEMA_GLOBAL_QSS


# ==============================================================================
# 1. DIÁLOGO MODAL: CREAR NUEVO PRODUCTO
# ==============================================================================
class NuevoProductoDialog(QDialog):
    """Diálogo modal para dar de alta un producto con stock inicial y categoría."""

    def __init__(
        self,
        categorias: Optional[Sequence[Categoria]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.categorias = categorias or []
        self.setWindowTitle("Registrar Nuevo Producto")
        self.setFixedSize(500, 640)
        self.setStyleSheet(TEMA_GLOBAL_QSS)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # SKU
        layout.addWidget(QLabel("SKU / Código Interno (*):"))
        self.txt_sku = QLineEdit()
        self.txt_sku.setPlaceholderText("ej: PROD-MONITOR-01")
        layout.addWidget(self.txt_sku)

        # Código de Barras
        layout.addWidget(QLabel("Código de Barras (EAN / UPC):"))
        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("ej: 7751234567890")
        layout.addWidget(self.txt_barcode)

        # Nombre
        layout.addWidget(QLabel("Nombre del Producto (*):"))
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("ej: Teclado Mecánico RGB")
        layout.addWidget(self.txt_nombre)

        # Categoría
        layout.addWidget(QLabel("Categoría:"))
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItem("Sin categoría", None)
        for cat in self.categorias:
            self.cmb_categoria.addItem(cat.nombre, cat.id_categoria)
        layout.addWidget(self.cmb_categoria)

        # Precios
        layout_precios = QHBoxLayout()

        layout_compra = QVBoxLayout()
        layout_compra.addWidget(QLabel("Precio Compra ($):"))
        self.spn_compra = QDoubleSpinBox()
        self.spn_compra.setRange(0.0, 999999.0)
        self.spn_compra.setPrefix("$ ")
        self.spn_compra.setDecimals(2)
        layout_compra.addWidget(self.spn_compra)
        layout_precios.addLayout(layout_compra)

        layout_venta = QVBoxLayout()
        layout_venta.addWidget(QLabel("Precio Venta (*):"))
        self.spn_venta = QDoubleSpinBox()
        self.spn_venta.setRange(0.0, 999999.0)
        self.spn_venta.setPrefix("$ ")
        self.spn_venta.setDecimals(2)
        layout_venta.addWidget(self.spn_venta)
        layout_precios.addLayout(layout_venta)

        layout.addLayout(layout_precios)

        # Stock Inicial y Mínimo
        layout_stocks = QHBoxLayout()

        layout_inicial = QVBoxLayout()
        layout_inicial.addWidget(QLabel("Stock Inicial:"))
        self.spn_stock_ini = QSpinBox()
        self.spn_stock_ini.setRange(0, 999999)
        layout_inicial.addWidget(self.spn_stock_ini)
        layout_stocks.addLayout(layout_inicial)

        layout_minimo = QVBoxLayout()
        layout_minimo.addWidget(QLabel("Stock Mínimo Alerta:"))
        self.spn_stock_min = QSpinBox()
        self.spn_stock_min.setRange(0, 999999)
        self.spn_stock_min.setValue(5)
        layout_minimo.addWidget(self.spn_stock_min)
        layout_stocks.addLayout(layout_minimo)

        layout.addLayout(layout_stocks)

        # Descripción
        layout.addWidget(QLabel("Descripción / Ficha Técnica:"))
        self.txt_desc = QTextEdit()
        self.txt_desc.setFixedHeight(60)
        layout.addWidget(self.txt_desc)

        # Botones
        layout_btns = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_guardar = QPushButton("Guardar Producto")
        self.btn_guardar.setObjectName("btn_primary")

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar.clicked.connect(self.validar_y_aceptar)

        layout_btns.addWidget(self.btn_cancelar)
        layout_btns.addWidget(self.btn_guardar)
        layout.addLayout(layout_btns)

    def validar_y_aceptar(self) -> None:
        if not self.txt_sku.text().strip():
            QMessageBox.warning(self, "Validación", "El SKU es obligatorio.")
            self.txt_sku.setFocus()
            return
        if not self.txt_nombre.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre del producto es obligatorio.")
            self.txt_nombre.setFocus()
            return
        self.accept()

    def obtener_datos(self) -> dict:
        return {
            "datos_producto": {
                "sku": self.txt_sku.text().strip(),
                "codigo_barras": self.txt_barcode.text().strip() or None,
                "nombre": self.txt_nombre.text().strip(),
                "id_categoria": self.cmb_categoria.currentData(),
                "precio_compra": Decimal(str(self.spn_compra.value())),
                "precio_venta": Decimal(str(self.spn_venta.value())),
                "stock_minimo": self.spn_stock_min.value(),
                "descripcion": self.txt_desc.toPlainText().strip() or None,
                "activo": True,
            },
            "stock_inicial": self.spn_stock_ini.value(),
        }


# ==============================================================================
# 2. DIÁLOGO MODAL: EDITAR PRODUCTO (MODIFICAR PRECIOS Y DATOS)
# ==============================================================================
class EditarProductoDialog(QDialog):
    """Diálogo modal para modificar los datos, categoría y precios de un producto."""

    def __init__(
        self,
        producto: Producto,
        categorias: Optional[Sequence[Categoria]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.producto = producto
        self.categorias = categorias or []
        self.setWindowTitle(f"Editar Producto - {producto.nombre}")
        self.setFixedSize(500, 620)
        self.setStyleSheet(TEMA_GLOBAL_QSS)
        self.init_ui()
        self.cargar_datos()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # SKU
        layout.addWidget(QLabel("SKU / Código Interno (*):"))
        self.txt_sku = QLineEdit()
        layout.addWidget(self.txt_sku)

        # Código de Barras
        layout.addWidget(QLabel("Código de Barras:"))
        self.txt_barcode = QLineEdit()
        layout.addWidget(self.txt_barcode)

        # Nombre
        layout.addWidget(QLabel("Nombre del Producto (*):"))
        self.txt_nombre = QLineEdit()
        layout.addWidget(self.txt_nombre)

        # Categoría
        layout.addWidget(QLabel("Categoría:"))
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.addItem("Sin categoría", None)
        for cat in self.categorias:
            self.cmb_categoria.addItem(cat.nombre, cat.id_categoria)
        layout.addWidget(self.cmb_categoria)

        # Precios
        layout_precios = QHBoxLayout()

        layout_compra = QVBoxLayout()
        layout_compra.addWidget(QLabel("Precio Compra ($):"))
        self.spn_compra = QDoubleSpinBox()
        self.spn_compra.setRange(0.0, 999999.0)
        self.spn_compra.setPrefix("$ ")
        self.spn_compra.setDecimals(2)
        layout_compra.addWidget(self.spn_compra)
        layout_precios.addLayout(layout_compra)

        layout_venta = QVBoxLayout()
        layout_venta.addWidget(QLabel("Precio Venta (*):"))
        self.spn_venta = QDoubleSpinBox()
        self.spn_venta.setRange(0.0, 999999.0)
        self.spn_venta.setPrefix("$ ")
        self.spn_venta.setDecimals(2)
        layout_venta.addWidget(self.spn_venta)
        layout_precios.addLayout(layout_venta)

        layout.addLayout(layout_precios)

        # Stock Mínimo y Estado
        layout_params = QHBoxLayout()

        layout_minimo = QVBoxLayout()
        layout_minimo.addWidget(QLabel("Stock Mínimo Alerta:"))
        self.spn_stock_min = QSpinBox()
        self.spn_stock_min.setRange(0, 999999)
        layout_minimo.addWidget(self.spn_stock_min)
        layout_params.addLayout(layout_minimo)

        layout_estado = QVBoxLayout()
        layout_estado.addWidget(QLabel("Estado:"))
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["Activo (Habilitado)", "Inactivo (Deshabilitado)"])
        layout_estado.addWidget(self.cmb_estado)
        layout_params.addLayout(layout_estado)

        layout.addLayout(layout_params)

        # Descripción
        layout.addWidget(QLabel("Descripción / Notas:"))
        self.txt_desc = QTextEdit()
        self.txt_desc.setFixedHeight(60)
        layout.addWidget(self.txt_desc)

        # Botones
        layout_btns = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_guardar = QPushButton("Actualizar Producto")
        self.btn_guardar.setObjectName("btn_primary")

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar.clicked.connect(self.validar_y_aceptar)

        layout_btns.addWidget(self.btn_cancelar)
        layout_btns.addWidget(self.btn_guardar)
        layout.addLayout(layout_btns)

    def cargar_datos(self) -> None:
        """Carga la información actual del producto en los campos."""
        self.txt_sku.setText(self.producto.sku or "")
        self.txt_barcode.setText(self.producto.codigo_barras or "")
        self.txt_nombre.setText(self.producto.nombre or "")
        if self.producto.id_categoria:
            idx = self.cmb_categoria.findData(self.producto.id_categoria)
            if idx >= 0:
                self.cmb_categoria.setCurrentIndex(idx)
        self.spn_compra.setValue(float(self.producto.precio_compra))
        self.spn_venta.setValue(float(self.producto.precio_venta))
        self.spn_stock_min.setValue(self.producto.stock_minimo or 0)
        self.cmb_estado.setCurrentIndex(0 if self.producto.activo else 1)
        self.txt_desc.setPlainText(self.producto.descripcion or "")

    def validar_y_aceptar(self) -> None:
        if not self.txt_sku.text().strip():
            QMessageBox.warning(self, "Validación", "El SKU no puede estar vacío.")
            return
        if not self.txt_nombre.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre no puede estar vacío.")
            return
        self.accept()

    def obtener_datos(self) -> dict:
        return {
            "sku": self.txt_sku.text().strip(),
            "codigo_barras": self.txt_barcode.text().strip() or None,
            "nombre": self.txt_nombre.text().strip(),
            "id_categoria": self.cmb_categoria.currentData(),
            "precio_compra": Decimal(str(self.spn_compra.value())),
            "precio_venta": Decimal(str(self.spn_venta.value())),
            "stock_minimo": self.spn_stock_min.value(),
            "descripcion": self.txt_desc.toPlainText().strip() or None,
            "activo": (self.cmb_estado.currentIndex() == 0),
        }


# ==============================================================================
# 3. DIÁLOGO MODAL: AJUSTE DE STOCK MANUAL (KARDEX)
# ==============================================================================
class AjusteStockDialog(QDialog):
    """Diálogo para corrección física de inventario con justificación obligatoria."""

    def __init__(self, producto: Producto, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.producto = producto
        self.setWindowTitle(f"Ajuste de Stock: {producto.nombre}")
        self.setFixedSize(400, 360)
        self.setStyleSheet(TEMA_GLOBAL_QSS)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        stock_actual = self.producto.inventario.stock_actual if self.producto.inventario else 0
        lbl_info = QLabel(f"<b>Producto:</b> {self.producto.nombre}<br><b>Stock Actual:</b> {stock_actual} unid.")
        lbl_info.setStyleSheet(f"background-color: {PALETA['bg_secundario']}; padding: 10px; border-radius: 6px;")
        layout.addWidget(lbl_info)

        layout.addWidget(QLabel("Tipo de Movimiento:"))
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["ENTRADA", "SALIDA", "AJUSTE"])
        layout.addWidget(self.cmb_tipo)

        layout.addWidget(QLabel("Cantidad a Ajustar:"))
        self.spn_cantidad = QSpinBox()
        self.spn_cantidad.setRange(1, 999999)
        self.spn_cantidad.setValue(1)
        layout.addWidget(self.spn_cantidad)

        layout.addWidget(QLabel("Motivo / Justificación (*):"))
        self.txt_motivo = QTextEdit()
        self.txt_motivo.setPlaceholderText("ej: Merma por rotura de empaque / Conteo físico trimestral...")
        self.txt_motivo.setFixedHeight(70)
        layout.addWidget(self.txt_motivo)

        layout_btns = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_confirmar = QPushButton("Confirmar Ajuste")
        self.btn_confirmar.setObjectName("btn_primary")

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_confirmar.clicked.connect(self.validar_y_aceptar)

        layout_btns.addWidget(self.btn_cancelar)
        layout_btns.addWidget(self.btn_confirmar)
        layout.addLayout(layout_btns)

    def validar_y_aceptar(self) -> None:
        if len(self.txt_motivo.toPlainText().strip()) < 3:
            QMessageBox.warning(self, "Validación", "Debe ingresar un motivo para justificar el ajuste.")
            return
        self.accept()

    def obtener_datos(self) -> dict:
        return {
            "id_producto": self.producto.id_producto,
            "tipo_movimiento": self.cmb_tipo.currentText(),
            "cantidad_ajuste": self.spn_cantidad.value(),
            "motivo": self.txt_motivo.toPlainText().strip(),
        }


# ==============================================================================
# 4. DIÁLOGO MODAL: HISTORIAL DE KARDEX
# ==============================================================================
class KardexDialog(QDialog):
    """Diálogo modal para visualizar los asientos históricos de Kardex de un producto."""

    def __init__(
        self,
        producto: Producto,
        movimientos: List[MovimientoInventario],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Kardex Perpetuo - {producto.nombre} (SKU: {producto.sku})")
        self.resize(750, 450)
        self.setStyleSheet(TEMA_GLOBAL_QSS)

        layout = QVBoxLayout(self)

        tabla = QTableWidget()
        tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabla.setColumnCount(5)
        tabla.setHorizontalHeaderLabels([
            "Fecha / Hora", "Tipo", "Cantidad", "Referencia", "Observación / Motivo"
        ])
        tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        tabla.setRowCount(len(movimientos))

        for row, mov in enumerate(movimientos):
            fecha_str = mov.fecha_movimiento.strftime("%Y-%m-%d %H:%M") if mov.fecha_movimiento else ""
            tabla.setItem(row, 0, QTableWidgetItem(fecha_str))
            tabla.setItem(row, 1, QTableWidgetItem(mov.tipo_movimiento))
            tabla.setItem(row, 2, QTableWidgetItem(str(mov.cantidad)))
            tabla.setItem(row, 3, QTableWidgetItem(mov.referencia or "-"))
            tabla.setItem(row, 4, QTableWidgetItem(mov.observacion or "-"))

        layout.addWidget(tabla)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedWidth(100)
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignRight)


# ==============================================================================
# 5. PÁGINA PRINCIPAL DE INVENTARIO
# ==============================================================================
class InventarioPage(QWidget):
    """Página del catálogo maestro de productos y administración de inventario."""

    def __init__(
        self,
        usuario_actual: UsuarioAutenticado,
        inventario_controller: Optional[InventarioController] = None,
    ) -> None:
        super().__init__()
        self.usuario_actual = usuario_actual
        self.controller = inventario_controller or InventarioController()
        self._productos_actuales: List[Producto] = []
        self.init_ui()
        self.conectar_senales()
        self.cargar_categorias_filtro()
        self.controller.cargar_catalogo()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Barra Superior de Acciones
        barra_acciones = QFrame()
        barra_acciones.setObjectName("card")
        layout_acciones = QHBoxLayout(barra_acciones)
        layout_acciones.setContentsMargins(12, 12, 12, 12)
        layout_acciones.setSpacing(8)

        # Buscador
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por nombre, SKU o código de barras...")
        self.txt_buscar.setFixedHeight(38)
        layout_acciones.addWidget(self.txt_buscar, stretch=35)

        # Filtro de Categoría
        self.cmb_filtro_categoria = QComboBox()
        self.cmb_filtro_categoria.setFixedHeight(38)
        self.cmb_filtro_categoria.setToolTip("Filtrar productos por categoría")
        layout_acciones.addWidget(self.cmb_filtro_categoria)

        # Filtro de Estado (Activos / Inactivos / Todos)
        self.cmb_filtro_estado = QComboBox()
        self.cmb_filtro_estado.addItems(["🟢 Solo Activos", "📋 Todos los Productos", "🔴 Solo Inactivos"])
        self.cmb_filtro_estado.setFixedHeight(38)
        self.cmb_filtro_estado.setToolTip("Filtrar catálogo por estado de disponibilidad")
        layout_acciones.addWidget(self.cmb_filtro_estado)

        # Botón Nuevo Producto
        self.btn_nuevo = QPushButton("➕ Nuevo Producto")
        self.btn_nuevo.setObjectName("btn_primary")
        self.btn_nuevo.setFixedHeight(38)
        layout_acciones.addWidget(self.btn_nuevo)

        # Botón Editar Producto
        self.btn_editar = QPushButton("✏️ Editar Producto")
        self.btn_editar.setFixedHeight(38)
        self.btn_editar.setObjectName("btn_blue")
        layout_acciones.addWidget(self.btn_editar)

        # Botón Ajuste de Stock
        self.btn_ajuste = QPushButton("⚖️ Ajuste Stock")
        self.btn_ajuste.setFixedHeight(38)
        layout_acciones.addWidget(self.btn_ajuste)

        # Botón Ver Kardex
        self.btn_kardex = QPushButton("📜 Kardex")
        self.btn_kardex.setFixedHeight(38)
        layout_acciones.addWidget(self.btn_kardex)

        # Botón Cambiar Estado (Activar/Desactivar)
        self.btn_toggle_activo = QPushButton("🔄 Activar/Desactivar")
        self.btn_toggle_activo.setFixedHeight(38)
        layout_acciones.addWidget(self.btn_toggle_activo)

        # Botón Refrescar
        self.btn_refrescar = QPushButton("🔄")
        self.btn_refrescar.setFixedWidth(40)
        self.btn_refrescar.setFixedHeight(38)
        layout_acciones.addWidget(self.btn_refrescar)

        layout.addWidget(barra_acciones)

        # Indicador de doble clic
        lbl_hint = QLabel(
            "💡 <i>Tip: Puedes hacer doble clic en cualquier producto para editarlo. "
            "Filtra por categoría o estado para organizar el inventario rápidamente.</i>"
        )
        lbl_hint.setStyleSheet(f"color: {PALETA['text_secondary']}; font-size: 11px;")
        layout.addWidget(lbl_hint)

        # Tabla de Catálogo (Solo Lectura interactiva)
        self.tabla = QTableWidget()
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setColumnCount(10)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "SKU", "Código Barras", "Nombre del Producto", "Descripción", "Categoría", "P. Compra", "P. Venta", "Stock Actual", "Estado"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Descripción adaptable
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.tabla)

    def cargar_categorias_filtro(self) -> None:
        """Carga las categorías disponibles en el selector de la barra de acciones."""
        self.cmb_filtro_categoria.blockSignals(True)
        self.cmb_filtro_categoria.clear()
        self.cmb_filtro_categoria.addItem("📁 Todas las Categorías", None)
        for cat in self.controller.obtener_categorias():
            self.cmb_filtro_categoria.addItem(f"📁 {cat.nombre}", cat.id_categoria)
        self.cmb_filtro_categoria.blockSignals(False)

    def conectar_senales(self) -> None:
        self.txt_buscar.textChanged.connect(self.controller.buscar_productos)
        self.cmb_filtro_categoria.currentIndexChanged.connect(self.on_cambiar_filtro_categoria)
        self.cmb_filtro_estado.currentIndexChanged.connect(self.on_cambiar_filtro_estado)
        self.btn_refrescar.clicked.connect(self.on_refrescar)
        self.btn_nuevo.clicked.connect(self.on_nuevo_producto)
        self.btn_editar.clicked.connect(self.on_editar_producto)
        self.btn_ajuste.clicked.connect(self.on_ajustar_stock)
        self.btn_kardex.clicked.connect(self.on_ver_kardex)
        self.btn_toggle_activo.clicked.connect(self.on_toggle_activo)
        self.tabla.cellDoubleClicked.connect(lambda r, c: self.on_editar_producto())

        # Señales del Controlador
        self.controller.catalogo_actualizado.connect(self.on_catalogo_actualizado)
        self.controller.operacion_exitosa.connect(lambda msg: QMessageBox.information(self, "Éxito", msg))
        self.controller.operacion_fallida.connect(lambda msg: QMessageBox.critical(self, "Error", msg))

    def refrescar_datos(self) -> None:
        """Recarga automáticamente el catálogo y las categorías disponibles."""
        self.cargar_categorias_filtro()
        self.controller.cargar_catalogo()

    def showEvent(self, event) -> None:
        """Al hacerse visible la pestaña de inventario, recarga el stock en tiempo real."""
        super().showEvent(event)
        self.refrescar_datos()

    def on_refrescar(self) -> None:
        """Refresca categorías y recarga el catálogo."""
        self.refrescar_datos()

    def on_cambiar_filtro_categoria(self) -> None:
        id_cat = self.cmb_filtro_categoria.currentData()
        self.controller.cambiar_filtro_categoria(id_cat)

    def on_cambiar_filtro_estado(self, index: int) -> None:
        # 0: Activos (True), 1: Todos (None), 2: Inactivos (False)
        filtro_map = {0: True, 1: None, 2: False}
        filtro = filtro_map.get(index, True)
        self.controller.cambiar_filtro_estado(filtro)

    def on_catalogo_actualizado(self, productos: List[Producto]) -> None:
        self._productos_actuales = productos
        self.tabla.setRowCount(0)

        for row, prod in enumerate(productos):
            self.tabla.insertRow(row)
            stock_actual = prod.inventario.stock_actual if prod.inventario else 0

            self.tabla.setItem(row, 0, QTableWidgetItem(str(prod.id_producto)))
            self.tabla.setItem(row, 1, QTableWidgetItem(prod.sku or "-"))
            self.tabla.setItem(row, 2, QTableWidgetItem(prod.codigo_barras or "-"))
            self.tabla.setItem(row, 3, QTableWidgetItem(prod.nombre))
            self.tabla.setItem(row, 4, QTableWidgetItem(prod.descripcion or "-"))
            cat_nombre = prod.categoria.nombre if prod.categoria else "-"
            self.tabla.setItem(row, 5, QTableWidgetItem(cat_nombre))
            self.tabla.setItem(row, 6, QTableWidgetItem(f"${prod.precio_compra:.2f}"))
            self.tabla.setItem(row, 7, QTableWidgetItem(f"${prod.precio_venta:.2f}"))

            # Item Stock con alerta de color si está bajo el mínimo
            item_stock = QTableWidgetItem(str(stock_actual))
            if stock_actual <= (prod.stock_minimo or 0):
                item_stock.setForeground(Qt.GlobalColor.yellow)
            self.tabla.setItem(row, 8, item_stock)

            item_estado = QTableWidgetItem("🟢 Activo" if prod.activo else "🔴 Inactivo")
            self.tabla.setItem(row, 9, item_estado)

    def _obtener_producto_seleccionado(self) -> Optional[Producto]:
        row = self.tabla.currentRow()
        if row < 0 or row >= len(self._productos_actuales):
            QMessageBox.warning(self, "Atención", "Por favor seleccione un producto de la tabla.")
            return None
        return self._productos_actuales[row]

    def on_nuevo_producto(self) -> None:
        categorias = self.controller.obtener_categorias()
        dlg = NuevoProductoDialog(categorias=categorias, parent=self)
        if dlg.exec():
            datos = dlg.obtener_datos()
            self.controller.crear_producto(
                datos_formulario=datos["datos_producto"],
                stock_inicial=datos["stock_inicial"],
                id_usuario=self.usuario_actual.id_usuario,
            )

    def on_editar_producto(self) -> None:
        prod = self._obtener_producto_seleccionado()
        if prod:
            categorias = self.controller.obtener_categorias()
            dlg = EditarProductoDialog(prod, categorias=categorias, parent=self)
            if dlg.exec():
                datos_modificados = dlg.obtener_datos()
                self.controller.actualizar_producto(
                    id_producto=prod.id_producto,
                    datos_formulario=datos_modificados,
                )

    def on_toggle_activo(self) -> None:
        prod = self._obtener_producto_seleccionado()
        if prod:
            nuevo_estado = not prod.activo
            estado_txt = "activar" if nuevo_estado else "desactivar"
            resp = QMessageBox.question(
                self,
                "Confirmación",
                f"¿Está seguro de que desea {estado_txt} el producto '{prod.nombre}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if resp == QMessageBox.StandardButton.Yes:
                self.controller.actualizar_producto(
                    id_producto=prod.id_producto,
                    datos_formulario={"activo": nuevo_estado},
                )

    def on_ajustar_stock(self) -> None:
        prod = self._obtener_producto_seleccionado()
        if prod:
            dlg = AjusteStockDialog(prod, self)
            if dlg.exec():
                datos = dlg.obtener_datos()
                self.controller.realizar_ajuste_stock(
                    id_producto=datos["id_producto"],
                    cantidad_ajuste=datos["cantidad_ajuste"],
                    tipo_movimiento=datos["tipo_movimiento"],
                    motivo=datos["motivo"],
                    id_usuario=self.usuario_actual.id_usuario,
                )

    def on_ver_kardex(self) -> None:
        prod = self._obtener_producto_seleccionado()
        if prod:
            movimientos = self.controller.obtener_historial_kardex(prod.id_producto)
            dlg = KardexDialog(prod, list(movimientos), self)
            dlg.exec()
