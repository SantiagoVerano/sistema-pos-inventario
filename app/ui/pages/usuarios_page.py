"""
Página de Gestión de Usuarios y Seguridad (app/ui/pages/usuarios_page.py)

Responsabilidad Arquitectónica:
-------------------------------
Vista para administración de colaboradores, control de acceso RBAC y usuarios:
1. Tabla de usuarios registrados con sus roles y estado activo.
2. Diálogo modal para registrar nuevos usuarios con contraseña y rol.
3. Diálogo modal para cambiar contraseñas.
4. Habilitación / Deshabilitación de acceso (borrado lógico).
"""

from typing import List, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
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
    QVBoxLayout,
    QWidget,
)

from app.database.connection import session_scope
from app.database.models.seguridad.usuario import Usuario
from app.database.repositories.seguridad.usuario_repository import UsuarioRepository
from app.database.repositories.seguridad.rol_repository import RolRepository
from app.services.seguridad.auth_service import AuthService, UsuarioAutenticado
from app.ui.styles.theme import PALETA, TEMA_GLOBAL_QSS


# ==============================================================================
# DIÁLOGO MODAL: CREAR USUARIO
# ==============================================================================
class CrearUsuarioDialog(QDialog):
    """Modal para registrar un nuevo usuario con rol."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Registrar Colaborador")
        self.setFixedSize(400, 380)
        self.setStyleSheet(TEMA_GLOBAL_QSS)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Nombre Completo (*):"))
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("ej: Carlos López")
        layout.addWidget(self.txt_nombre)

        layout.addWidget(QLabel("Correo Electrónico (*):"))
        self.txt_correo = QLineEdit()
        self.txt_correo.setPlaceholderText("ej: clopez@pos.com")
        layout.addWidget(self.txt_correo)

        layout.addWidget(QLabel("Contraseña (*):"))
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("Mínimo 6 caracteres")
        layout.addWidget(self.txt_password)

        layout.addWidget(QLabel("Rol Asignado:"))
        self.cmb_rol = QComboBox()
        self.cmb_rol.addItems(["ADMINISTRADOR", "CAJERO", "BODEGUERO", "SUPERVISOR"])
        layout.addWidget(self.cmb_rol)

        layout_btns = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_guardar = QPushButton("Guardar Usuario")
        self.btn_guardar.setObjectName("btn_primary")

        self.btn_cancelar.clicked.connect(self.reject)
        self.btn_guardar.clicked.connect(self.validar_y_aceptar)

        layout_btns.addWidget(self.btn_cancelar)
        layout_btns.addWidget(self.btn_guardar)
        layout.addLayout(layout_btns)

    def validar_y_aceptar(self) -> None:
        if not self.txt_nombre.text().strip():
            QMessageBox.warning(self, "Validación", "El nombre es obligatorio.")
            return
        if not self.txt_correo.text().strip():
            QMessageBox.warning(self, "Validación", "El correo es obligatorio.")
            return
        if len(self.txt_password.text()) < 6:
            QMessageBox.warning(self, "Validación", "La contraseña debe tener al menos 6 caracteres.")
            return
        self.accept()

    def obtener_datos(self) -> dict:
        return {
            "nombre": self.txt_nombre.text().strip(),
            "correo": self.txt_correo.text().strip().lower(),
            "password": self.txt_password.text(),
            "rol": self.cmb_rol.currentText(),
        }


# ==============================================================================
# PÁGINA PRINCIPAL DE USUARIOS
# ==============================================================================
class UsuariosPage(QWidget):
    """Página de administración de cuentas de usuario."""

    def __init__(self, usuario_actual: UsuarioAutenticado) -> None:
        super().__init__()
        self.usuario_actual = usuario_actual
        self.auth_service = AuthService()
        self._usuarios: List[Usuario] = []
        self.init_ui()
        self.conectar_senales()
        self.cargar_usuarios()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Barra Superior de Acciones
        barra = QFrame()
        barra.setObjectName("card")
        layout_barra = QHBoxLayout(barra)
        layout_barra.setContentsMargins(12, 12, 12, 12)

        lbl_titulo = QLabel("Gestión de Usuarios & Seguridad")
        lbl_titulo.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {PALETA['text_primary']};")
        layout_barra.addWidget(lbl_titulo)
        layout_barra.addStretch()

        self.btn_nuevo = QPushButton("➕ Nuevo Colaborador")
        self.btn_nuevo.setObjectName("btn_primary")
        self.btn_nuevo.setFixedHeight(38)
        layout_barra.addWidget(self.btn_nuevo)

        self.btn_toggle_activo = QPushButton("🔄 Activar / Desactivar")
        self.btn_toggle_activo.setFixedHeight(38)
        layout_barra.addWidget(self.btn_toggle_activo)

        self.btn_refrescar = QPushButton("🔄")
        self.btn_refrescar.setFixedWidth(40)
        self.btn_refrescar.setFixedHeight(38)
        layout_barra.addWidget(self.btn_refrescar)

        layout.addWidget(barra)

        # Tabla de Usuarios
        self.tabla = QTableWidget()
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre Completo", "Correo Electrónico", "Roles", "Estado"])
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.tabla)

    def conectar_senales(self) -> None:
        self.btn_nuevo.clicked.connect(self.on_nuevo_usuario)
        self.btn_toggle_activo.clicked.connect(self.on_toggle_activo)
        self.btn_refrescar.clicked.connect(self.cargar_usuarios)

    def cargar_usuarios(self) -> None:
        """Consulta todos los usuarios registrados."""
        with session_scope() as session:
            repo = UsuarioRepository(session)
            self._usuarios = list(repo.get_all(limit=200))

            self.tabla.setRowCount(0)
            for row, user in enumerate(self._usuarios):
                self.tabla.insertRow(row)

                roles_str = ", ".join([ur.rol.nombre for ur in user.roles_asociados if ur.rol]) or "Sin Rol"
                estado_str = "🟢 Activo" if user.activo else "🔴 Inactivo"

                self.tabla.setItem(row, 0, QTableWidgetItem(str(user.id_usuario)))
                self.tabla.setItem(row, 1, QTableWidgetItem(user.nombre))
                self.tabla.setItem(row, 2, QTableWidgetItem(user.correo))
                self.tabla.setItem(row, 3, QTableWidgetItem(roles_str))

                item_est = QTableWidgetItem(estado_str)
                if not user.activo:
                    item_est.setForeground(Qt.GlobalColor.red)
                self.tabla.setItem(row, 4, item_est)

    def _obtener_usuario_seleccionado(self) -> Optional[Usuario]:
        row = self.tabla.currentRow()
        if row < 0 or row >= len(self._usuarios):
            QMessageBox.warning(self, "Atención", "Seleccione un usuario de la tabla.")
            return None
        return self._usuarios[row]

    def on_nuevo_usuario(self) -> None:
        dlg = CrearUsuarioDialog(self)
        if dlg.exec():
            datos = dlg.obtener_datos()
            try:
                # Obtener ID del rol
                id_rol = None
                with session_scope() as session:
                    repo_rol = RolRepository(session)
                    rol_obj = repo_rol.obtener_por_nombre(datos["rol"])
                    if not rol_obj:
                        rol_obj = repo_rol.create(app.database.models.seguridad.Rol(nombre=datos["rol"]))
                    id_rol = rol_obj.id_rol

                self.auth_service.registrar_usuario(
                    nombre=datos["nombre"],
                    correo=datos["correo"],
                    password=datos["password"],
                    roles_ids=[id_rol] if id_rol else None,
                )
                QMessageBox.information(self, "Éxito", f"Usuario '{datos['nombre']}' registrado exitosamente.")
                self.cargar_usuarios()
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"No se pudo registrar al usuario: {exc}")

    def on_toggle_activo(self) -> None:
        user = self._obtener_usuario_seleccionado()
        if user:
            if user.id_usuario == self.usuario_actual.id_usuario:
                QMessageBox.warning(self, "Acción no permitida", "No puede deshabilitar su propia cuenta en uso.")
                return

            nuevo_estado = not user.activo
            accion_txt = "activar" if nuevo_estado else "desactivar"

            resp = QMessageBox.question(
                self,
                "Confirmación",
                f"¿Está seguro de que desea {accion_txt} la cuenta de '{user.nombre}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if resp == QMessageBox.StandardButton.Yes:
                with session_scope() as session:
                    repo = UsuarioRepository(session)
                    repo.cambiar_estado_activo(user.id_usuario, nuevo_estado)
                self.cargar_usuarios()
