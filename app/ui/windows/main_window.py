"""
Ventana Principal de la Aplicación (app/ui/windows/main_window.py)

Responsabilidad Arquitectónica:
-------------------------------
Ventana contenedora principal del Sistema POS en PySide6:
1. Barra lateral de navegación (Sidebar) con acceso a los 5 módulos:
   - 💳 Punto de Venta (POS)
   - 📦 Inventario & Stock
   - 📥 Compras & Proveedores
   - 📊 Historial de Ventas
   - 👥 Usuarios & Seguridad
2. Contenedor multipágina 'QStackedWidget'.
3. Encabezado con información del usuario conectado, rol y botón de cierre de sesión.
4. Aplicación del tema visual QSS global.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.controllers.seguridad.auth_controller import AuthController
from app.services.seguridad.auth_service import UsuarioAutenticado
from app.ui.pages.compras_page import ComprasPage
from app.ui.pages.inventario_page import InventarioPage
from app.ui.pages.pos_page import POSPage
from app.ui.pages.ventas_page import VentasPage
from app.ui.pages.usuarios_page import UsuariosPage
from app.ui.styles.theme import PALETA, TEMA_GLOBAL_QSS


class MainWindow(QMainWindow):
    """
    Ventana de Escritorio Principal con Navegación Lateral y Módulos.
    """
    # Señal emitida al cerrar la sesión
    sesion_cerrada = Signal()

    def __init__(
        self,
        usuario: UsuarioAutenticado,
        auth_controller: Optional[AuthController] = None,
    ) -> None:
        super().__init__()
        self.usuario = usuario
        self.auth_controller = auth_controller or AuthController()
        self.init_ui()
        self.conectar_senales()

    def init_ui(self) -> None:
        """Construye el layout general: Sidebar lateral + Header + Contenedor de páginas."""
        self.setWindowTitle(f"CorePOS - Sistema de Inventarios & POS [{self.usuario.nombre}]")
        self.resize(1300, 820)
        self.setMinimumSize(1024, 700)
        self.setStyleSheet(TEMA_GLOBAL_QSS)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_central = QHBoxLayout(widget_central)
        layout_central.setContentsMargins(0, 0, 0, 0)
        layout_central.setSpacing(0)

        # ======================================================================
        # 1. BARRA LATERAL (Sidebar)
        # ======================================================================
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        layout_sidebar = QVBoxLayout(self.sidebar)
        layout_sidebar.setContentsMargins(16, 20, 16, 20)
        layout_sidebar.setSpacing(6)

        # Marca / Logo
        lbl_marca = QLabel("🛒 CorePOS")
        lbl_marca.setStyleSheet(
            f"font-size: 22px; font-weight: 900; color: {PALETA['accent_primary']}; margin-bottom: 20px;"
        )
        layout_sidebar.addWidget(lbl_marca)

        # Grupo de Botones de Navegación
        self.btn_group_nav = QButtonGroup(self)
        self.btn_group_nav.setExclusive(True)

        self.btn_nav_pos = QPushButton("💳 Punto de Venta")
        self.btn_nav_pos.setObjectName("btn_nav")
        self.btn_nav_pos.setCheckable(True)
        self.btn_nav_pos.setChecked(True)
        self.btn_nav_pos.setCursor(Qt.PointingHandCursor)
        self.btn_group_nav.addButton(self.btn_nav_pos, 0)
        layout_sidebar.addWidget(self.btn_nav_pos)

        self.btn_nav_inventario = QPushButton("📦 Inventario & Stock")
        self.btn_nav_inventario.setObjectName("btn_nav")
        self.btn_nav_inventario.setCheckable(True)
        self.btn_nav_inventario.setCursor(Qt.PointingHandCursor)
        self.btn_group_nav.addButton(self.btn_nav_inventario, 1)
        layout_sidebar.addWidget(self.btn_nav_inventario)

        self.btn_nav_compras = QPushButton("📥 Compras & Proveedores")
        self.btn_nav_compras.setObjectName("btn_nav")
        self.btn_nav_compras.setCheckable(True)
        self.btn_nav_compras.setCursor(Qt.PointingHandCursor)
        self.btn_group_nav.addButton(self.btn_nav_compras, 2)
        layout_sidebar.addWidget(self.btn_nav_compras)

        self.btn_nav_ventas = QPushButton("📊 Historial de Ventas")
        self.btn_nav_ventas.setObjectName("btn_nav")
        self.btn_nav_ventas.setCheckable(True)
        self.btn_nav_ventas.setCursor(Qt.PointingHandCursor)
        self.btn_group_nav.addButton(self.btn_nav_ventas, 3)
        layout_sidebar.addWidget(self.btn_nav_ventas)

        self.btn_nav_usuarios = QPushButton("👥 Usuarios & Roles")
        self.btn_nav_usuarios.setObjectName("btn_nav")
        self.btn_nav_usuarios.setCheckable(True)
        self.btn_nav_usuarios.setCursor(Qt.PointingHandCursor)
        self.btn_group_nav.addButton(self.btn_nav_usuarios, 4)
        layout_sidebar.addWidget(self.btn_nav_usuarios)

        layout_sidebar.addStretch()

        # Tarjeta de Usuario en el Sidebar
        card_user = QFrame()
        card_user.setStyleSheet(
            f"background-color: {PALETA['bg_terciario']}; border-radius: 8px; padding: 10px;"
        )
        layout_user = QVBoxLayout(card_user)
        layout_user.setSpacing(4)

        lbl_user_name = QLabel(f"👤 {self.usuario.nombre}")
        lbl_user_name.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout_user.addWidget(lbl_user_name)

        rol_principal = self.usuario.roles[0] if self.usuario.roles else "Operador"
        lbl_user_role = QLabel(f"Rol: {rol_principal}")
        lbl_user_role.setStyleSheet(f"font-size: 11px; color: {PALETA['accent_primary']};")
        layout_user.addWidget(lbl_user_role)

        layout_sidebar.addWidget(card_user)

        # Botón Cerrar Sesión
        self.btn_logout = QPushButton("🚪 Cerrar Sesión")
        self.btn_logout.setObjectName("btn_danger")
        self.btn_logout.setFixedHeight(36)
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        layout_sidebar.addWidget(self.btn_logout)

        layout_central.addWidget(self.sidebar)

        # ======================================================================
        # 2. CONTENEDOR MULTIPÁGINA (QStackedWidget)
        # ======================================================================
        self.stacked_widget = QStackedWidget()

        # Instanciar las 5 Páginas
        self.page_pos = POSPage(usuario_actual=self.usuario)
        self.page_inventario = InventarioPage(usuario_actual=self.usuario)
        self.page_compras = ComprasPage(usuario_actual=self.usuario)
        self.page_ventas = VentasPage(usuario_actual=self.usuario)
        self.page_usuarios = UsuariosPage(usuario_actual=self.usuario)

        self.stacked_widget.addWidget(self.page_pos)          # Índice 0
        self.stacked_widget.addWidget(self.page_inventario)   # Índice 1
        self.stacked_widget.addWidget(self.page_compras)      # Índice 2
        self.stacked_widget.addWidget(self.page_ventas)       # Índice 3
        self.stacked_widget.addWidget(self.page_usuarios)     # Índice 4

        layout_central.addWidget(self.stacked_widget)

    def conectar_senales(self) -> None:
        """Conecta eventos de navegación, cierre de sesión y sincronización reactiva entre módulos."""
        self.btn_group_nav.idClicked.connect(self.cambiar_pagina)
        self.btn_logout.clicked.connect(self.ejecutar_cierre_sesion)

        # Sincronización Reactiva en Tiempo Real:
        # 1. Cuando se completa una venta en POS -> actualiza Inventario y el Historial de Ventas
        self.page_pos.pos_controller.venta_completada.connect(
            lambda *_: self._al_completar_venta()
        )

        # 2. Cuando se anula una venta en VentasPage -> actualiza el Inventario (reintegro de stock)
        self.page_ventas.venta_anulada_confirmada.connect(
            lambda *_: self.page_inventario.refrescar_datos()
        )

        # 3. Cuando ingresa una compra en ComprasPage -> actualiza el Inventario (nuevo stock)
        self.page_compras.compras_controller.compra_procesada.connect(
            lambda *_: self.page_inventario.refrescar_datos()
        )

    def _al_completar_venta(self) -> None:
        """Sincroniza stock y ventas tras una transacción en POS."""
        self.page_inventario.refrescar_datos()
        self.page_ventas.refrescar_datos()

    def cambiar_pagina(self, page_id: int) -> None:
        """Cambia la vista activa del StackedWidget y refresca sus datos en vivo."""
        self.stacked_widget.setCurrentIndex(page_id)

        # Refrescar automáticamente según la página que entra en foco
        if page_id == 0:  # POS
            self.page_pos.actualizar_display_cliente()
            self.page_pos.txt_barcode.setFocus()
        elif page_id == 1:  # Inventario
            self.page_inventario.refrescar_datos()
        elif page_id == 2:  # Compras
            self.page_compras.cargar_datos_iniciales()
        elif page_id == 3:  # Historial de Ventas
            self.page_ventas.refrescar_datos()

    def ejecutar_cierre_sesion(self) -> None:
        """Notifica el cierre de sesión y cierra la ventana."""
        self.auth_controller.cerrar_sesion()
        self.sesion_cerrada.emit()
        self.close()
