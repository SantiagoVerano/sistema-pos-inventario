"""
Ventana de Inicio de Sesión / Login (app/ui/windows/login_window.py)

Responsabilidad Arquitectónica:
-------------------------------
Vista de autenticación de usuario en PySide6.
Captura credenciales (correo y contraseña), valida campos vacíos y delega
la autenticación a 'AuthController'. No contiene lógica de base de datos ni hashing.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.controllers.seguridad.auth_controller import AuthController
from app.services.seguridad.auth_service import UsuarioAutenticado
from app.ui.styles.theme import PALETA, TEMA_GLOBAL_QSS


class LoginWindow(QWidget):
    """
    Ventana de Login moderna para autenticación en el Sistema POS.
    """
    # Señal emitida cuando el usuario se loguea exitosamente
    usuario_autenticado = Signal(object)  # Emite UsuarioAutenticado

    def __init__(self, auth_controller: Optional[AuthController] = None) -> None:
        super().__init__()
        self.auth_controller = auth_controller or AuthController()
        self.init_ui()
        self.conectar_senales()

    def init_ui(self) -> None:
        """Construye la interfaz gráfica y los componentes visuales."""
        self.setWindowTitle("Sistema POS - Iniciar Sesión")
        self.setFixedSize(420, 520)
        self.setStyleSheet(TEMA_GLOBAL_QSS)

        # Layout Principal Centrado
        layout_principal = QVBoxLayout(self)
        layout_principal.setAlignment(Qt.AlignCenter)
        layout_principal.setContentsMargins(24, 24, 24, 24)

        # Tarjeta Central Contenedora
        tarjeta = QFrame()
        tarjeta.setObjectName("card")
        tarjeta.setStyleSheet(
            f"QFrame#card {{ background-color: {PALETA['bg_secundario']}; border: 1px solid {PALETA['border']}; border-radius: 12px; padding: 24px; }}"
        )
        layout_tarjeta = QVBoxLayout(tarjeta)
        layout_tarjeta.setSpacing(16)

        # Logo / Título del Sistema
        lbl_logo = QLabel("🛒")
        lbl_logo.setAlignment(Qt.AlignCenter)
        lbl_logo.setStyleSheet("font-size: 48px; margin-bottom: 4px;")
        layout_tarjeta.addWidget(lbl_logo)

        lbl_titulo = QLabel("Bienvenido")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        lbl_titulo.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {PALETA['text_primary']};")
        layout_tarjeta.addWidget(lbl_titulo)

        lbl_subtitulo = QLabel("Sistema de Inventarios & Punto de Venta")
        lbl_subtitulo.setAlignment(Qt.AlignCenter)
        lbl_subtitulo.setStyleSheet(f"font-size: 12px; color: {PALETA['text_secondary']}; margin-bottom: 8px;")
        layout_tarjeta.addWidget(lbl_subtitulo)

        # Campo: Correo Electrónico
        lbl_correo = QLabel("Correo Electrónico:")
        lbl_correo.setStyleSheet(f"font-weight: 600; color: {PALETA['text_secondary']};")
        layout_tarjeta.addWidget(lbl_correo)

        self.txt_correo = QLineEdit()
        self.txt_correo.setPlaceholderText("ejemplo: admin@pos.com")
        self.txt_correo.setText("admin@pos.com")  # Default de conveniencia para pruebas
        self.txt_correo.setFixedHeight(40)
        layout_tarjeta.addWidget(self.txt_correo)

        # Campo: Contraseña
        lbl_password = QLabel("Contraseña:")
        lbl_password.setStyleSheet(f"font-weight: 600; color: {PALETA['text_secondary']};")
        layout_tarjeta.addWidget(lbl_password)

        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("••••••••")
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setFixedHeight(40)
        layout_tarjeta.addWidget(self.txt_password)

        # Etiqueta de Mensajes de Error / Estado
        self.lbl_mensaje = QLabel("")
        self.lbl_mensaje.setAlignment(Qt.AlignCenter)
        self.lbl_mensaje.setWordWrap(True)
        self.lbl_mensaje.setStyleSheet(f"color: {PALETA['danger']}; font-size: 12px; font-weight: 500;")
        self.lbl_mensaje.hide()
        layout_tarjeta.addWidget(self.lbl_mensaje)

        # Botón Iniciar Sesión
        self.btn_login = QPushButton("Ingresar al Sistema")
        self.btn_login.setObjectName("btn_primary")
        self.btn_login.setFixedHeight(44)
        self.btn_login.setCursor(Qt.PointingHandCursor)
        layout_tarjeta.addWidget(self.btn_login)

        layout_principal.addWidget(tarjeta)

    def conectar_senales(self) -> None:
        """Conecta eventos visuales con el controlador de autenticación."""
        self.btn_login.clicked.connect(self.ejecutar_login)
        self.txt_correo.returnPressed.connect(self.ejecutar_login)
        self.txt_password.returnPressed.connect(self.ejecutar_login)

        # Señales del Controlador
        self.auth_controller.login_exitoso.connect(self.on_login_exitoso)
        self.auth_controller.login_fallido.connect(self.on_login_fallido)

    def ejecutar_login(self) -> None:
        """Valida campos básicos y llama al controlador."""
        correo = self.txt_correo.text().strip()
        password = self.txt_password.text()

        if not correo:
            self.mostrar_error("Por favor ingrese su correo electrónico.")
            self.txt_correo.setFocus()
            return

        if not password:
            self.mostrar_error("Por favor ingrese su contraseña.")
            self.txt_password.setFocus()
            return

        self.lbl_mensaje.setText("Validando credenciales...")
        self.lbl_mensaje.setStyleSheet(f"color: {PALETA['accent_primary']}; font-size: 12px;")
        self.lbl_mensaje.show()
        self.btn_login.setEnabled(False)

        # Invocar controlador
        self.auth_controller.iniciar_sesion(correo, password)

    def on_login_exitoso(self, usuario: UsuarioAutenticado) -> None:
        """Slot llamado cuando el inicio de sesión es exitoso."""
        self.lbl_mensaje.hide()
        self.btn_login.setEnabled(True)
        self.usuario_autenticado.emit(usuario)
        self.close()

    def on_login_fallido(self, mensaje_error: str) -> None:
        """Slot llamado cuando el login falla."""
        self.btn_login.setEnabled(True)
        self.mostrar_error(mensaje_error)

    def mostrar_error(self, mensaje: str) -> None:
        """Muestra una alerta visual en la tarjeta de login."""
        self.lbl_mensaje.setText(mensaje)
        self.lbl_mensaje.setStyleSheet(f"color: {PALETA['danger']}; font-size: 12px; font-weight: bold;")
        self.lbl_mensaje.show()
