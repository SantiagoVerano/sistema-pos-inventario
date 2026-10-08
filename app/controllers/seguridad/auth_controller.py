"""
Controlador de Autenticación y Sesión (app/controllers/seguridad/auth_controller.py)

Responsabilidad Arquitectónica:
-------------------------------
Gestionar el flujo de autenticación, la sesión activa del usuario y la captura de errores
de seguridad. Actúa como intermediario entre la ventana de Login de PySide6 y 'AuthService'.
"""

from typing import Any, Dict, List, Optional
from PySide6.QtCore import QObject, Signal

from app.core.exceptions import AppException, AuthenticationException, ValidationException
from app.core.logger import get_logger
from app.services.seguridad.auth_service import AuthService, UsuarioAutenticado

logger = get_logger(__name__)


class AuthController(QObject):
    """
    Controlador para el inicio de sesión y gestión de la sesión activa del usuario.
    Emite señales Qt para notificar a las vistas los cambios de estado.
    """
    # Señales Qt
    login_exitoso = Signal(object)      # Emite el DTO UsuarioAutenticado
    login_fallido = Signal(str)         # Emite el mensaje de error para mostrar en la UI
    sesion_cerrada = Signal()           # Notifica que se cerró la sesión

    def __init__(self, auth_service: Optional[AuthService] = None) -> None:
        super().__init__()
        self._service = auth_service or AuthService()
        self._usuario_actual: Optional[UsuarioAutenticado] = None

    @property
    def usuario_actual(self) -> Optional[UsuarioAutenticado]:
        """Retorna la sesión del usuario actualmente autenticado en la aplicación."""
        return self._usuario_actual

    @property
    def esta_autenticado(self) -> bool:
        """Indica si existe una sesión activa válida."""
        return self._usuario_actual is not None

    def iniciar_sesion(self, correo: str, password: str) -> bool:
        """
        Intenta autenticar al usuario con sus credenciales.
        Retorna True si fue exitoso o False si falló, emitiendo las señales correspondientes.
        """
        try:
            usuario_auth = self._service.autenticar(correo=correo, password=password)
            self._usuario_actual = usuario_auth
            logger.info(f"Sesión iniciada para: {usuario_auth.correo}")
            self.login_exitoso.emit(usuario_auth)
            return True

        except AuthenticationException as exc:
            mensaje_error = exc.mensaje
            logger.warning(f"Fallo de autenticación: {mensaje_error}")
            self.login_fallido.emit(mensaje_error)
            return False

        except ValidationException as exc:
            mensaje_error = exc.mensaje
            self.login_fallido.emit(mensaje_error)
            return False

        except AppException as exc:
            mensaje_error = f"Error del sistema: {exc.mensaje}"
            logger.error(f"Error en login: {exc}", exc_info=True)
            self.login_fallido.emit(mensaje_error)
            return False

        except Exception as exc:
            mensaje_error = "Ocurrió un error inesperado al intentar iniciar sesión."
            logger.critical(f"Error no controlado en AuthController: {exc}", exc_info=True)
            self.login_fallido.emit(mensaje_error)
            return False

    def cerrar_sesion(self) -> None:
        """Limpia la sesión activa y notifica a las vistas para volver al Login."""
        if self._usuario_actual:
            logger.info(f"Cerrando sesión de: {self._usuario_actual.correo}")
        self._usuario_actual = None
        self.sesion_cerrada.emit()

    def registrar_nuevo_usuario(
        self,
        nombre: str,
        correo: str,
        password: str,
        roles_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Permite a un administrador registrar a un nuevo usuario.
        Retorna un diccionario con {'exito': bool, 'mensaje': str, 'usuario': Optional[Usuario]}.
        """
        try:
            usuario = self._service.registrar_usuario(
                nombre=nombre,
                correo=correo,
                password=password,
                roles_ids=roles_ids,
            )
            return {
                "exito": True,
                "mensaje": f"Usuario '{usuario.nombre}' registrado con éxito.",
                "usuario": usuario,
            }
        except AppException as exc:
            return {"exito": False, "mensaje": exc.mensaje, "usuario": None}
        except Exception as exc:
            logger.error(f"Error inesperado al registrar usuario: {exc}", exc_info=True)
            return {
                "exito": False,
                "mensaje": "Error interno al procesar el registro del usuario.",
                "usuario": None,
            }

    def cambiar_password(
        self, password_actual: str, nueva_password: str
    ) -> Dict[str, Any]:
        """Cambia la contraseña del usuario con sesión activa."""
        if not self._usuario_actual:
            return {"exito": False, "mensaje": "No hay una sesión activa."}

        try:
            self._service.cambiar_password(
                id_usuario=self._usuario_actual.id_usuario,
                password_actual=password_actual,
                nueva_password=nueva_password,
            )
            return {"exito": True, "mensaje": "Contraseña actualizada exitosamente."}
        except AppException as exc:
            return {"exito": False, "mensaje": exc.mensaje}
        except Exception as exc:
            return {"exito": False, "mensaje": f"Error al cambiar contraseña: {exc}"}
