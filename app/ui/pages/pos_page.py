"""
Página del Terminal Punto de Venta / POS (app/ui/pages/pos_page.py)

Responsabilidad Arquitectónica:
-------------------------------
Vista interactiva del cajero:
1. Entrada de lector láser de código de barras y buscador predictivo rápido.
2. Filtrado por categorías tanto en escáner como en el diálogo visual de catálogo.
3. Selección y creación de clientes en 'ventas.clientes' (búsqueda por cédula o nombre).
4. Selección automática del 'Cliente Rápido' (Consumidor Final) por defecto.
5. Carrito reactivo con edición de cantidad en vivo y prevención de stock negativo.
6. Panel financiero de cobro con cálculo de vuelto en tiempo real.
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

from app.controllers.ventas.pos_controller import ItemCarrito, POSController
from app.database.models.inventario.categoria import Categoria
from app.database.models.inventario.producto import Producto
from app.database.models.ventas.cliente import Cliente
from app.database.models.ventas.venta import Venta
from app.services.inventario.inventario_service import InventarioService
from app.services.seguridad.auth_service import UsuarioAutenticado
from app.ui.styles.theme import PALETA, TEMA_GLOBAL_QSS


# ==============================================================================
# 1. DIÁLOGO MODAL: CREAR NUEVO CLIENTE (ventas.clientes)
# ==============================================================================
class NuevoClienteDialog(QDialog):
    """Diálogo modal para dar de alta un nuevo cliente en el esquema 'ventas.clientes'."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar Nuevo Cliente")
        self.setFixedSize(480, 520)
        self.setStyleSheet(TEMA_GLOBAL_QSS)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Tipo Documento y Número Documento
        layout_doc = QHBoxLayout()

        layout_tipo = QVBoxLayout()
        layout_tipo.addWidget(QLabel("Tipo Doc:"))
        self.cmb_tipo_doc = QComboBox()
        self.cmb_tipo_doc.addItems(["CC", "NIT", "DNI", "RUC", "PASAPORTE"])
        self.cmb_tipo_doc.setFixedWidth(110)
        layout_tipo.addWidget(self.cmb_tipo_doc)
        layout_doc.addLayout(layout_tipo)

        layout_num = QVBoxLayout()
        layout_num.addWidget(QLabel("N° Documento / Cédula (*):"))
        self.txt_num_doc = QLineEdit()
        self.txt_num_doc.setPlaceholderText("ej: 1020304050")
        layout_num.addWidget(self.txt_num_doc)
        layout_doc.addLayout(layout_num)

        layout.addLayout(layout_doc)

        # Nombres y Apellidos
        layout_nombres = QHBoxLayout()

        layout_nom = QVBoxLayout()
        layout_nom.addWidget(QLabel("Nombre (*):"))
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("ej: Carlos")
        layout_nom.addWidget(self.txt_nombre)
        layout_nombres.addLayout(layout_nom)

        layout_ape = QVBoxLayout()
        layout_ape.addWidget(QLabel("Apellido:"))
        self.txt_apellido = QLineEdit()
        self.txt_apellido.setPlaceholderText("ej: Gómez")
        layout_ape.addWidget(self.txt_apellido)
        layout_nombres.addLayout(layout_ape)

        layout.addLayout(layout_nombres)

        # Teléfono
        layout.addWidget(QLabel("Teléfono / Móvil:"))
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("ej: +57 300 1234567")
        layout.addWidget(self.txt_telefono)

        # Correo Electrónico
        layout.addWidget(QLabel("Correo Electrónico:"))
        self.txt_correo = QLineEdit()
        self.txt_correo.setPlaceholderText("ej: cliente@ejemplo.com")
        layout.addWidget(self.txt_correo)

        # Dirección
        layout.addWidget(QLabel("Dirección:"))
        self.txt_direccion = QLineEdit()
        self.txt_direccion.setPlaceholderText("ej: Calle 10 # 20 - 30")
        layout.addWidget(self.txt_direccion)

        # Botones
        layout_btns = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_guardar = QPushButton("Guardar y Asignar")
        self.btn_guardar.setObjectName("btn_primary")

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar.clicked.connect(self.validar_y_aceptar)

        layout_btns.addWidget(self.btn_cancelar)
        layout_btns.addWidget(self.btn_guardar)
        layout.addLayout(layout_btns)

    def validar_y_aceptar(self) -> None:
        if not self.txt_num_doc.text().strip():
            QMessageBox.warning(self, "Validación", "El número de documento / cédula es obligatorio.")
            self.txt_num_doc.setFocus()
            return
        if not self.txt_nombre.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre del cliente es obligatorio.")
            self.txt_nombre.setFocus()
            return
        self.accept()

    def obtener_datos(self) -> dict:
        return {
            "tipo_documento": self.cmb_tipo_doc.currentText(),
            "numero_documento": self.txt_num_doc.text().strip(),
            "nombre": self.txt_nombre.text().strip(),
            "apellido": self.txt_apellido.text().strip() or None,
            "telefono": self.txt_telefono.text().strip() or None,
            "correo": self.txt_correo.text().strip() or None,
            "direccion": self.txt_direccion.text().strip() or None,
        }


# ==============================================================================
# 2. DIÁLOGO MODAL: BUSCADOR Y SELECCIÓN DE CLIENTES
# ==============================================================================
class BuscadorClientesDialog(QDialog):
    """Diálogo modal para buscar y seleccionar clientes por cédula o nombre en el POS."""

    def __init__(
        self,
        pos_controller: POSController,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.pos_controller = pos_controller
        self.cliente_seleccionado: Optional[Cliente] = None
        self._clientes: List[Cliente] = []

        self.setWindowTitle("Buscar y Seleccionar Cliente")
        self.resize(750, 480)
        self.setStyleSheet(TEMA_GLOBAL_QSS)
        self.init_ui()
        self.buscar("")

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Barra superior con buscador y botón nuevo cliente
        layout_top = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por Cédula / Documento o Nombre...")
        self.txt_buscar.setFixedHeight(38)
        self.txt_buscar.textChanged.connect(self.buscar)
        layout_top.addWidget(self.txt_buscar, stretch=60)

        self.btn_nuevo_cliente = QPushButton("➕ Nuevo Cliente")
        self.btn_nuevo_cliente.setFixedHeight(38)
        self.btn_nuevo_cliente.setObjectName("btn_primary")
        self.btn_nuevo_cliente.clicked.connect(self.on_crear_nuevo_cliente)
        layout_top.addWidget(self.btn_nuevo_cliente)

        self.btn_cliente_rapido = QPushButton("⚡ 'Cliente Rápido'")
        self.btn_cliente_rapido.setFixedHeight(38)
        self.btn_cliente_rapido.setToolTip("Asignar Consumidor Final por defecto")
        self.btn_cliente_rapido.clicked.connect(self.seleccionar_cliente_rapido)
        layout_top.addWidget(self.btn_cliente_rapido)

        layout.addLayout(layout_top)

        # Tabla de Clientes
        self.tabla = QTableWidget()
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Documento / Cédula", "Nombre Completo", "Teléfono", "Correo"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.cellDoubleClicked.connect(self.seleccionar_y_cerrar)
        layout.addWidget(self.tabla)

        # Botones de pie
        layout_bottom = QHBoxLayout()
        lbl_hint = QLabel("💡 <i>Doble clic en un cliente para seleccionarlo</i>")
        lbl_hint.setStyleSheet(f"color: {PALETA['text_secondary']};")
        layout_bottom.addWidget(lbl_hint)
        layout_bottom.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        layout_bottom.addWidget(btn_cancelar)

        self.btn_seleccionar = QPushButton("✔ Seleccionar Cliente")
        self.btn_seleccionar.setObjectName("btn_blue")
        self.btn_seleccionar.clicked.connect(self.seleccionar_y_cerrar)
        layout_bottom.addWidget(self.btn_seleccionar)

        layout.addLayout(layout_bottom)

    def buscar(self, texto: str) -> None:
        query = texto.strip()
        if query:
            self._clientes = list(self.pos_controller.buscar_clientes(query))
        else:
            self._clientes = list(self.pos_controller.listar_clientes_recientes())

        self.tabla.setRowCount(0)
        for row, cli in enumerate(self._clientes):
            self.tabla.insertRow(row)
            doc_str = f"{cli.tipo_documento or 'CC'}: {cli.numero_documento or '-'}"
            nombre_completo = f"{cli.nombre or ''} {cli.apellido or ''}".strip()
            self.tabla.setItem(row, 0, QTableWidgetItem(str(cli.id_cliente)))
            self.tabla.setItem(row, 1, QTableWidgetItem(doc_str))
            self.tabla.setItem(row, 2, QTableWidgetItem(nombre_completo))
            self.tabla.setItem(row, 3, QTableWidgetItem(cli.telefono or "-"))
            self.tabla.setItem(row, 4, QTableWidgetItem(cli.correo or "-"))

    def seleccionar_y_cerrar(self) -> None:
        row = self.tabla.currentRow()
        if 0 <= row < len(self._clientes):
            self.cliente_seleccionado = self._clientes[row]
            self.accept()
        else:
            QMessageBox.warning(self, "Atención", "Seleccione un cliente de la lista.")

    def seleccionar_cliente_rapido(self) -> None:
        self.cliente_seleccionado = self.pos_controller.obtener_cliente_por_defecto()
        self.accept()

    def on_crear_nuevo_cliente(self) -> None:
        dlg = NuevoClienteDialog(self)
        if dlg.exec():
            datos = dlg.obtener_datos()
            cli = self.pos_controller.registrar_cliente(
                numero_documento=datos["numero_documento"],
                nombre=datos["nombre"],
                apellido=datos["apellido"],
                tipo_documento=datos["tipo_documento"],
                telefono=datos["telefono"],
                correo=datos["correo"],
                direccion=datos["direccion"],
            )
            if cli:
                self.cliente_seleccionado = cli
                self.accept()


# ==============================================================================
# 3. DIÁLOGO MODAL: BUSCADOR RÁPIDO DE PRODUCTOS (CON CATEGORÍAS) EN POS
# ==============================================================================
class BuscadorProductosDialog(QDialog):
    """Modal para buscar y seleccionar productos del catálogo con filtro por categoría."""

    def __init__(
        self,
        inventario_service: InventarioService,
        categoria_inicial: Optional[int] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.service = inventario_service
        self.categoria_inicial = categoria_inicial
        self.producto_seleccionado: Optional[Producto] = None
        self._productos: List[Producto] = []

        self.setWindowTitle("Buscar Producto para Carrito")
        self.resize(780, 500)
        self.setStyleSheet(TEMA_GLOBAL_QSS)
        self.init_ui()
        self.cargar_categorias()
        self.buscar("")

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Barra de Búsqueda y Filtro de Categoría
        layout_filtros = QHBoxLayout()

        self.txt_query = QLineEdit()
        self.txt_query.setPlaceholderText("🔍 Escriba nombre, SKU o código de barras...")
        self.txt_query.setFixedHeight(40)
        self.txt_query.textChanged.connect(lambda: self.buscar(self.txt_query.text()))
        layout_filtros.addWidget(self.txt_query, stretch=60)

        self.cmb_categoria = QComboBox()
        self.cmb_categoria.setFixedHeight(40)
        self.cmb_categoria.setToolTip("Filtrar por categoría")
        self.cmb_categoria.currentIndexChanged.connect(lambda: self.buscar(self.txt_query.text()))
        layout_filtros.addWidget(self.cmb_categoria, stretch=40)

        layout.addLayout(layout_filtros)

        # Tabla de Selección
        self.tabla = QTableWidget()
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "SKU", "Nombre", "Categoría", "Precio Venta", "Stock"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.setColumnHidden(0, True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla.cellDoubleClicked.connect(self.seleccionar_y_cerrar)
        layout.addWidget(self.tabla)

        # Botones
        layout_btns = QHBoxLayout()
        lbl_hint = QLabel("💡 <i>Doble clic o Enter para agregar al carrito</i>")
        lbl_hint.setStyleSheet(f"color: {PALETA['text_secondary']};")
        layout_btns.addWidget(lbl_hint)
        layout_btns.addStretch()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_agregar = QPushButton("➕ Agregar al Carrito")
        self.btn_agregar.setObjectName("btn_primary")

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_agregar.clicked.connect(self.seleccionar_y_cerrar)

        layout_btns.addWidget(self.btn_cancelar)
        layout_btns.addWidget(self.btn_agregar)
        layout.addLayout(layout_btns)

    def cargar_categorias(self) -> None:
        """Puebla el selector de categorías."""
        self.cmb_categoria.blockSignals(True)
        self.cmb_categoria.clear()
        self.cmb_categoria.addItem("📁 Todas las Categorías", None)
        categorias = self.service.listar_categorias_activas()
        idx_seleccionar = 0
        for i, cat in enumerate(categorias, start=1):
            self.cmb_categoria.addItem(f"📁 {cat.nombre}", cat.id_categoria)
            if self.categoria_inicial and cat.id_categoria == self.categoria_inicial:
                idx_seleccionar = i
        self.cmb_categoria.setCurrentIndex(idx_seleccionar)
        self.cmb_categoria.blockSignals(False)

    def buscar(self, texto: str) -> None:
        """Filtra productos activos en la base de datos por término y categoría."""
        query = texto.strip()
        id_categoria = self.cmb_categoria.currentData() if hasattr(self, "cmb_categoria") else None

        if query:
            self._productos = list(
                self.service.buscar_productos(
                    termino=query, id_categoria=id_categoria, solo_activos=True, limit=40
                )
            )
        else:
            self._productos = list(
                self.service.listar_productos_activos(
                    id_categoria=id_categoria, limit=40
                )
            )

        self.tabla.setRowCount(0)
        for row, prod in enumerate(self._productos):
            self.tabla.insertRow(row)
            stock = prod.inventario.stock_actual if prod.inventario else 0
            cat_nom = prod.categoria.nombre if prod.categoria else "-"
            self.tabla.setItem(row, 0, QTableWidgetItem(str(prod.id_producto)))
            self.tabla.setItem(row, 1, QTableWidgetItem(prod.sku or "-"))
            self.tabla.setItem(row, 2, QTableWidgetItem(prod.nombre))
            self.tabla.setItem(row, 3, QTableWidgetItem(cat_nom))
            self.tabla.setItem(row, 4, QTableWidgetItem(f"${prod.precio_venta:.2f}"))
            self.tabla.setItem(row, 5, QTableWidgetItem(str(stock)))

    def seleccionar_y_cerrar(self) -> None:
        row = self.tabla.currentRow()
        if 0 <= row < len(self._productos):
            self.producto_seleccionado = self._productos[row]
            self.accept()
        else:
            QMessageBox.warning(self, "Atención", "Seleccione un producto de la lista.")


# ==============================================================================
# 4. PÁGINA PRINCIPAL DEL TERMINAL POS
# ==============================================================================
class POSPage(QWidget):
    """
    Página principal del Terminal POS para despacho y facturación.
    """

    def __init__(
        self,
        usuario_actual: UsuarioAutenticado,
        pos_controller: Optional[POSController] = None,
    ) -> None:
        super().__init__()
        self.usuario_actual = usuario_actual
        self.pos_controller = pos_controller or POSController()
        self.inventario_service = InventarioService()
        self.init_ui()
        self.conectar_senales()
        self.cargar_categorias_pos()
        self.actualizar_display_cliente()

    def init_ui(self) -> None:
        """Construye la distribución visual en dos columnas (Lector/Buscador + Carrito/Cobro)."""
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(16, 16, 16, 16)
        layout_principal.setSpacing(16)

        # ======================================================================
        # COLUMNA IZQUIERDA: Lector de Barras y Tabla del Carrito (65% del ancho)
        # ======================================================================
        col_izquierda = QWidget()
        layout_izq = QVBoxLayout(col_izquierda)
        layout_izq.setContentsMargins(0, 0, 0, 0)
        layout_izq.setSpacing(12)

        # Barra de Escaneo Rápido, Filtro de Categoría y Búsqueda
        card_escaneo = QFrame()
        card_escaneo.setObjectName("card")
        layout_escaneo = QHBoxLayout(card_escaneo)
        layout_escaneo.setContentsMargins(12, 12, 12, 12)
        layout_escaneo.setSpacing(8)

        lbl_scanner = QLabel("📷 Escáner / SKU:")
        lbl_scanner.setStyleSheet(f"font-weight: bold; color: {PALETA['text_secondary']};")
        layout_escaneo.addWidget(lbl_scanner)

        self.txt_barcode = QLineEdit()
        self.txt_barcode.setPlaceholderText("Pase el código de barras o escriba SKU...")
        self.txt_barcode.setFixedHeight(38)
        layout_escaneo.addWidget(self.txt_barcode, stretch=40)

        self.btn_agregar_scanner = QPushButton("Agregar")
        self.btn_agregar_scanner.setFixedHeight(38)
        self.btn_agregar_scanner.setObjectName("btn_blue")
        layout_escaneo.addWidget(self.btn_agregar_scanner)

        # Selector de Categoría Rápido
        self.cmb_categoria_pos = QComboBox()
        self.cmb_categoria_pos.setFixedHeight(38)
        self.cmb_categoria_pos.setToolTip("Filtrar productos por categoría")
        layout_escaneo.addWidget(self.cmb_categoria_pos, stretch=25)

        self.btn_buscar_catalogo = QPushButton("🔍 Catálogo [F3]")
        self.btn_buscar_catalogo.setFixedHeight(38)
        layout_escaneo.addWidget(self.btn_buscar_catalogo)

        layout_izq.addWidget(card_escaneo)

        # Tabla de Productos en el Carrito
        self.tabla_carrito = QTableWidget()
        self.tabla_carrito.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_carrito.setColumnCount(7)
        self.tabla_carrito.setHorizontalHeaderLabels([
            "ID", "SKU / Código", "Descripción", "P. Unitario", "Cantidad", "Subtotal", "Quitar"
        ])
        self.tabla_carrito.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla_carrito.setColumnHidden(0, True)
        self.tabla_carrito.verticalHeader().setVisible(False)
        self.tabla_carrito.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout_izq.addWidget(self.tabla_carrito)

        # Botón para vaciar carrito
        layout_botones_izq = QHBoxLayout()
        self.btn_vaciar = QPushButton("🗑️ Vaciar Carrito")
        self.btn_vaciar.setObjectName("btn_danger")
        self.btn_vaciar.setFixedWidth(140)
        layout_botones_izq.addWidget(self.btn_vaciar)
        layout_botones_izq.addStretch()

        layout_izq.addLayout(layout_botones_izq)
        layout_principal.addWidget(col_izquierda, stretch=65)

        # ======================================================================
        # COLUMNA DERECHA: Cliente, Panel Financiero y Cobro (35% del ancho)
        # ======================================================================
        col_derecha = QWidget()
        layout_der = QVBoxLayout(col_derecha)
        layout_der.setContentsMargins(0, 0, 0, 0)
        layout_der.setSpacing(14)

        # ======================================================================
        # CARD CLIENTE DE LA VENTA
        # ======================================================================
        card_cliente = QFrame()
        card_cliente.setObjectName("card")
        layout_card_cliente = QVBoxLayout(card_cliente)
        layout_card_cliente.setContentsMargins(14, 12, 14, 12)
        layout_card_cliente.setSpacing(8)

        lbl_cli_header = QLabel("👤 Cliente para Facturación:")
        lbl_cli_header.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {PALETA['text_secondary']};"
        )
        layout_card_cliente.addWidget(lbl_cli_header)

        # Etiqueta con el nombre del cliente actual
        self.lbl_cliente_nombre = QLabel("⚡ Cliente Rápido")
        self.lbl_cliente_nombre.setStyleSheet(
            f"font-size: 15px; font-weight: 800; color: {PALETA['accent_primary']};"
        )
        layout_card_cliente.addWidget(self.lbl_cliente_nombre)

        # Etiqueta con cédula/documento del cliente
        self.lbl_cliente_doc = QLabel("Cédula/NIT: 00000000 | Consumidor Final")
        self.lbl_cliente_doc.setStyleSheet(
            f"color: {PALETA['text_secondary']}; font-size: 12px;"
        )
        layout_card_cliente.addWidget(self.lbl_cliente_doc)

        # Botones de gestión rápida de cliente
        layout_btns_cli = QHBoxLayout()
        self.btn_cambiar_cliente = QPushButton("🔍 Buscar / Cambiar")
        self.btn_cambiar_cliente.setFixedHeight(34)
        self.btn_cambiar_cliente.setObjectName("btn_blue")

        self.btn_nuevo_cliente = QPushButton("➕ Nuevo")
        self.btn_nuevo_cliente.setFixedHeight(34)

        self.btn_cliente_rapido = QPushButton("⚡ Rápido")
        self.btn_cliente_rapido.setFixedHeight(34)
        self.btn_cliente_rapido.setToolTip("Restablecer a Cliente Rápido")

        layout_btns_cli.addWidget(self.btn_cambiar_cliente)
        layout_btns_cli.addWidget(self.btn_nuevo_cliente)
        layout_btns_cli.addWidget(self.btn_cliente_rapido)
        layout_card_cliente.addLayout(layout_btns_cli)

        layout_der.addWidget(card_cliente)

        # ======================================================================
        # CARD RESUMEN FINANCIERO Y COBRO
        # ======================================================================
        card_cobro = QFrame()
        card_cobro.setObjectName("card")
        layout_card_cobro = QVBoxLayout(card_cobro)
        layout_card_cobro.setSpacing(14)

        # Título Panel
        lbl_resumen_titulo = QLabel("Resumen de Cobro")
        lbl_resumen_titulo.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {PALETA['text_primary']};"
        )
        layout_card_cobro.addWidget(lbl_resumen_titulo)

        # Subtotal
        layout_subtotal = QHBoxLayout()
        lbl_sub_txt = QLabel("Subtotal:")
        lbl_sub_txt.setStyleSheet(f"color: {PALETA['text_secondary']}; font-size: 14px;")
        self.lbl_subtotal_val = QLabel("$0.00")
        self.lbl_subtotal_val.setStyleSheet("font-size: 14px; font-weight: 600;")
        layout_subtotal.addWidget(lbl_sub_txt)
        layout_subtotal.addStretch()
        layout_subtotal.addWidget(self.lbl_subtotal_val)
        layout_card_cobro.addLayout(layout_subtotal)

        # Descuento
        layout_desc = QHBoxLayout()
        lbl_desc_txt = QLabel("Descuento ($):")
        lbl_desc_txt.setStyleSheet(f"color: {PALETA['text_secondary']};")
        self.spn_descuento = QDoubleSpinBox()
        self.spn_descuento.setRange(0.0, 99999.0)
        self.spn_descuento.setPrefix("$ ")
        self.spn_descuento.setFixedWidth(110)
        layout_desc.addWidget(lbl_desc_txt)
        layout_desc.addStretch()
        layout_desc.addWidget(self.spn_descuento)
        layout_card_cobro.addLayout(layout_desc)

        # TOTAL GRANDE
        layout_total = QVBoxLayout()
        lbl_total_txt = QLabel("TOTAL A COBRAR:")
        lbl_total_txt.setStyleSheet(
            f"color: {PALETA['accent_primary']}; font-weight: bold; font-size: 14px;"
        )
        self.lbl_total_val = QLabel("$0.00")
        self.lbl_total_val.setAlignment(Qt.AlignCenter)
        self.lbl_total_val.setStyleSheet(
            f"font-size: 32px; font-weight: 900; color: {PALETA['accent_primary']}; "
            f"background-color: {PALETA['bg_principal']}; border: 2px solid {PALETA['accent_primary']}; "
            f"border-radius: 8px; padding: 12px;"
        )
        layout_total.addWidget(lbl_total_txt)
        layout_total.addWidget(self.lbl_total_val)
        layout_card_cobro.addLayout(layout_total)

        # Efectivo Recibido
        layout_recibido = QHBoxLayout()
        lbl_rec_txt = QLabel("Efectivo Recibido:")
        lbl_rec_txt.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {PALETA['text_secondary']};"
        )
        self.spn_recibido = QDoubleSpinBox()
        self.spn_recibido.setRange(0.0, 999999.0)
        self.spn_recibido.setPrefix("$ ")
        self.spn_recibido.setFixedHeight(40)
        self.spn_recibido.setFixedWidth(140)
        layout_recibido.addWidget(lbl_rec_txt)
        layout_recibido.addStretch()
        layout_recibido.addWidget(self.spn_recibido)
        layout_card_cobro.addLayout(layout_recibido)

        # Vuelto / Cambio
        layout_cambio = QHBoxLayout()
        lbl_cambio_txt = QLabel("Cambio / Vuelto:")
        lbl_cambio_txt.setStyleSheet(
            f"font-size: 14px; font-weight: 600; color: {PALETA['text_secondary']};"
        )
        self.lbl_cambio_val = QLabel("$0.00")
        self.lbl_cambio_val.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {PALETA['warning']};"
        )
        layout_cambio.addWidget(lbl_cambio_txt)
        layout_cambio.addStretch()
        layout_cambio.addWidget(self.lbl_cambio_val)
        layout_card_cobro.addLayout(layout_cambio)

        # Botón COBRAR VENTA
        self.btn_cobrar = QPushButton("💳 COBRAR VENTA [F5]")
        self.btn_cobrar.setObjectName("btn_primary")
        self.btn_cobrar.setFixedHeight(50)
        self.btn_cobrar.setCursor(Qt.PointingHandCursor)
        layout_card_cobro.addWidget(self.btn_cobrar)

        layout_der.addWidget(card_cobro)
        layout_der.addStretch()
        layout_principal.addWidget(col_derecha, stretch=35)

    def cargar_categorias_pos(self) -> None:
        """Carga el combo de categorías en la barra de escaneo."""
        self.cmb_categoria_pos.blockSignals(True)
        self.cmb_categoria_pos.clear()
        self.cmb_categoria_pos.addItem("📁 Todas las Categorías", None)
        for cat in self.pos_controller.obtener_categorias():
            self.cmb_categoria_pos.addItem(f"📁 {cat.nombre}", cat.id_categoria)
        self.cmb_categoria_pos.blockSignals(False)

    def conectar_senales(self) -> None:
        """Conecta eventos visuales con el controlador de ventas."""
        self.txt_barcode.returnPressed.connect(self.on_escanear_barcode)
        self.btn_agregar_scanner.clicked.connect(self.on_escanear_barcode)
        self.btn_buscar_catalogo.clicked.connect(self.on_abrir_buscador_catalogo)
        self.btn_vaciar.clicked.connect(self.pos_controller.vaciar_carrito)
        self.spn_descuento.valueChanged.connect(self.on_cambio_descuento)
        self.spn_recibido.valueChanged.connect(self.actualizar_vuelto)
        self.btn_cobrar.clicked.connect(self.on_procesar_cobro)

        # Eventos de Cliente
        self.btn_cambiar_cliente.clicked.connect(self.on_abrir_buscador_cliente)
        self.btn_nuevo_cliente.clicked.connect(self.on_crear_nuevo_cliente)
        self.btn_cliente_rapido.clicked.connect(self.on_restablecer_cliente_rapido)

        # Señales del Controlador POS
        self.pos_controller.carrito_actualizado.connect(self.on_carrito_actualizado)
        self.pos_controller.cliente_asignado.connect(self.actualizar_display_cliente)
        self.pos_controller.venta_completada.connect(self.on_venta_completada)
        self.pos_controller.stock_insuficiente.connect(self.mostrar_alerta_stock)
        self.pos_controller.producto_no_encontrado.connect(self.mostrar_producto_no_encontrado)
        self.pos_controller.operacion_fallida.connect(self.mostrar_error)

    def actualizar_display_cliente(self, cliente: Optional[Cliente] = None) -> None:
        """Actualiza las etiquetas con la información del cliente asignado."""
        cli = cliente or self.pos_controller.cliente_actual
        if cli:
            nombre_completo = f"{cli.nombre or ''} {cli.apellido or ''}".strip()
            es_rapido = (cli.numero_documento == "00000000")
            icono = "⚡" if es_rapido else "👤"
            self.lbl_cliente_nombre.setText(f"{icono} {nombre_completo}")

            doc_info = f"{cli.tipo_documento or 'CC'}: {cli.numero_documento or '-'}"
            if cli.telefono:
                doc_info += f" | Tel: {cli.telefono}"
            if es_rapido:
                doc_info += " (Consumidor Final)"
            self.lbl_cliente_doc.setText(doc_info)

    def on_abrir_buscador_cliente(self) -> None:
        """Abre el diálogo para buscar y seleccionar clientes por cédula o nombre."""
        dlg = BuscadorClientesDialog(self.pos_controller, self)
        if dlg.exec():
            cli = dlg.cliente_seleccionado
            if cli:
                self.pos_controller.asignar_cliente(cli)

    def on_crear_nuevo_cliente(self) -> None:
        """Abre el diálogo modal para registrar un nuevo cliente en ventas.clientes."""
        dlg = NuevoClienteDialog(self)
        if dlg.exec():
            datos = dlg.obtener_datos()
            self.pos_controller.registrar_cliente(
                numero_documento=datos["numero_documento"],
                nombre=datos["nombre"],
                apellido=datos["apellido"],
                tipo_documento=datos["tipo_documento"],
                telefono=datos["telefono"],
                correo=datos["correo"],
                direccion=datos["direccion"],
            )

    def on_restablecer_cliente_rapido(self) -> None:
        """Restablece al cliente rápido por defecto."""
        self.pos_controller.asignar_cliente(None)

    def on_escanear_barcode(self) -> None:
        """Procesa la entrada del lector de código de barras."""
        codigo = self.txt_barcode.text().strip()
        if codigo:
            if self.pos_controller.escanear_codigo_barras(codigo):
                self.txt_barcode.clear()
            self.txt_barcode.setFocus()

    def on_abrir_buscador_catalogo(self) -> None:
        """Abre el diálogo modal de catálogo con la categoría preseleccionada si existe."""
        cat_seleccionada = self.cmb_categoria_pos.currentData()
        dlg = BuscadorProductosDialog(
            inventario_service=self.inventario_service,
            categoria_inicial=cat_seleccionada,
            parent=self,
        )
        if dlg.exec():
            prod = dlg.producto_seleccionado
            if prod:
                self.pos_controller.agregar_producto(prod, cantidad=1)

    def on_cambio_descuento(self, valor: float) -> None:
        """Aplica el descuento en tiempo real al carrito."""
        self.pos_controller.aplicar_descuento_global(Decimal(str(valor)))

    def on_carrito_actualizado(self, items: List[ItemCarrito], totales: Dict[str, Decimal]) -> None:
        """Refresca la tabla del carrito y el panel de totales."""
        self.tabla_carrito.setRowCount(0)

        for row_idx, item in enumerate(items):
            self.tabla_carrito.insertRow(row_idx)

            # Columnas de datos
            self.tabla_carrito.setItem(row_idx, 0, QTableWidgetItem(str(item.id_producto)))
            self.tabla_carrito.setItem(row_idx, 1, QTableWidgetItem(item.sku))
            self.tabla_carrito.setItem(row_idx, 2, QTableWidgetItem(item.nombre))
            self.tabla_carrito.setItem(row_idx, 3, QTableWidgetItem(f"${item.precio_unitario:.2f}"))

            # SpinBox para editar cantidad directamente en la tabla
            spn_cant = QSpinBox()
            spn_cant.setRange(1, item.stock_disponible)
            spn_cant.setValue(item.cantidad)
            spn_cant.valueChanged.connect(
                lambda val, id_p=item.id_producto: self.pos_controller.actualizar_cantidad(id_p, val)
            )
            self.tabla_carrito.setCellWidget(row_idx, 4, spn_cant)

            self.tabla_carrito.setItem(row_idx, 5, QTableWidgetItem(f"${item.subtotal:.2f}"))

            # Botón Quitar Fila
            btn_quitar = QPushButton("❌")
            btn_quitar.setFixedSize(30, 28)
            btn_quitar.setStyleSheet("background-color: transparent; border: none; font-size: 14px;")
            btn_quitar.setCursor(Qt.PointingHandCursor)
            btn_quitar.clicked.connect(
                lambda _, id_p=item.id_producto: self.pos_controller.remover_producto(id_p)
            )
            self.tabla_carrito.setCellWidget(row_idx, 6, btn_quitar)

        # Actualizar Etiquetas de Totales
        subtotal = totales["subtotal"]
        total = totales["total"]

        self.lbl_subtotal_val.setText(f"${subtotal:.2f}")
        self.lbl_total_val.setText(f"${total:.2f}")

        # Ajustar monto recibido por defecto
        if self.spn_recibido.value() < float(total):
            self.spn_recibido.setValue(float(total))

        self.actualizar_vuelto()

    def actualizar_vuelto(self) -> None:
        """Calcula en vivo la diferencia de efectivo para el vuelto del cliente."""
        totales = self.pos_controller.calcular_totales()
        total = totales["total"]
        recibido = Decimal(str(self.spn_recibido.value()))
        cambio = max(Decimal("0.00"), recibido - total)
        self.lbl_cambio_val.setText(f"${cambio:.2f}")

    def on_procesar_cobro(self) -> None:
        """Envía el cobro al controlador con el efectivo recibido."""
        monto_recibido = Decimal(str(self.spn_recibido.value()))
        self.pos_controller.procesar_cobro(
            id_usuario_cajero=self.usuario_actual.id_usuario,
            monto_recibido=monto_recibido,
        )

    def on_venta_completada(self, venta: Venta, desglose: Dict[str, Any]) -> None:
        """Muestra ticket de confirmación y vuelto."""
        cambio = desglose["cambio_vuelto"]
        cli = self.pos_controller.cliente_actual
        cli_nombre = f"{cli.nombre or ''} {cli.apellido or ''}".strip() if cli else "Cliente Rápido"

        QMessageBox.information(
            self,
            "¡Venta Exitosa!",
            f"Venta #{venta.id_venta} registrada correctamente.\n\n"
            f"Cliente: {cli_nombre} (Doc: {cli.numero_documento if cli else '00000000'})\n"
            f"Total Cobrado: ${venta.total:.2f}\n"
            f"Efectivo Recibido: ${desglose['monto_recibido']:.2f}\n"
            f"Cambio a Devolver: ${cambio:.2f}",
        )
        self.spn_descuento.setValue(0.0)
        self.spn_recibido.setValue(0.0)
        self.actualizar_display_cliente()
        self.txt_barcode.setFocus()

    def mostrar_alerta_stock(self, mensaje: str) -> None:
        QMessageBox.warning(self, "Stock Insuficiente", mensaje)

    def mostrar_producto_no_encontrado(self, codigo: str) -> None:
        QMessageBox.warning(
            self,
            "Producto No Encontrado",
            f"No se encontró ningún artículo activo con el código: '{codigo}'.",
        )

    def mostrar_error(self, mensaje: str) -> None:
        QMessageBox.critical(self, "Error en Venta", mensaje)
