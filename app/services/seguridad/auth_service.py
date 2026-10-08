"""
Servicio de Autenticación y Seguridad (app/services/seguridad/auth_service.py)

Responsabilidad Arquitectónica:
-------------------------------
Orquestar la seguridad del sistema:
1. Hashing seguro de contraseñas mediante Argon2 (con fallback automático a PBKDF2-HMAC-SHA256).
2. Autenticación de credenciales de usuarios.
3. Gestión de usuarios, roles y control de acceso (RBAC).
4. Coordinación transaccional con 'session_scope()'.
"""

from dataclasses import dataclass
import hashlib
import secrets
from typing import List, Optional

from app.core.exceptions import (
    AuthenticationException,
    DuplicateResourceException,
    ResourceNotFoundException,
    ValidationException,
)
from app.core.logger import get_logger
from app.database.connection import session_scope
from app.database.models.seguridad.usuario import Usuario
from app.database.repositories.seguridad.usuario_repository import UsuarioRepository
from app.database.repositories.seguridad.rol_repository import RolRepository

logger = get_logger(__name__)

# Detección dinámica de librería Argon2
try:
    import argon2
    from argon2.exceptions import VerifyMismatchError, VerificationError
    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False
    logger.info("argon2-cffi no está instalado. Usando PBKDF2-SHA256 (estándar de Python) como fallback.")


@dataclass(frozen=True)
class UsuarioAutenticado:
    """
    Objeto de valor (DTO inmutable) que representa la sesión activa de un usuario en memoria.
    Utilizado por controladores y la interfaz gráfica de PySide6 para verificar permisos.
    """
    id_usuario: int
    nombre: str
    correo: str
    roles: List[str]

    def tiene_rol(self, nombre_rol: str) -> bool:
        """Verifica si el usuario autenticado posee un rol específico."""
        return nombre_rol.upper() in [r.upper() for r in self.roles]

    @property
    def es_admin(self) -> bool:
        """Helper rápido para verificar si el usuario es ADMINISTRADOR."""
        return self.tiene_rol("ADMINISTRADOR")


class AuthService:
    """
    Servicio central de Autenticación y Gestión de Usuarios.
    """

    def __init__(self) -> None:
        self._hasher = None
        if HAS_ARGON2:
            self._hasher = argon2.PasswordHasher(
                time_cost=3,
                memory_cost=65536,
                parallelism=4,
                hash_len=32,
                salt_len=16
            )

    def hashear_password(self, password: str) -> str:
        """Genera un hash criptográfico seguro con salt para la contraseña."""
        if not password or len(password) < 6:
            raise ValidationException("La contraseña debe tener al menos 6 caracteres.")

        if HAS_ARGON2 and self._hasher:
            return self._hasher.hash(password)
        else:
            # Fallback nativo de Python (PBKDF2 con 100,000 iteraciones y salt criptográfico)
            salt = secrets.token_hex(16)
            hash_val = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
            ).hex()
            return f"pbkdf2:sha256:100000${salt}${hash_val}"

    def verificar_password(self, password: str, password_hash: str) -> bool:
        """Comprueba si una contraseña en texto plano coincide con el hash almacenado."""
        try:
            if password_hash.startswith("pbkdf2:"):
                partes = password_hash.split("$")
                salt = partes[1]
                expected_hash = partes[2]
                computed = hashlib.pbkdf2_hmac(
                    "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000
                ).hex()
                return secrets.compare_digest(computed, expected_hash)
            elif HAS_ARGON2 and self._hasher:
                return self._hasher.verify(password_hash, password)
            else:
                return False
        except Exception as exc:
            logger.error(f"Error al verificar hash de contraseña: {exc}")
            return False

    def autenticar(self, correo: str, password: str) -> UsuarioAutenticado:
        """
        Valida las credenciales de un usuario.
        Retorna el DTO UsuarioAutenticado si es exitoso o lanza AuthenticationException.
        """
        correo_normalizado = correo.strip().lower()
        if not correo_normalizado or not password:
            raise AuthenticationException("Debe ingresar correo y contraseña.")

        with session_scope() as session:
            repo_usuario = UsuarioRepository(session)
            usuario = repo_usuario.obtener_por_correo(correo_normalizado)

            # Validar existencia y estado activo
            if not usuario:
                logger.warning(f"Intento de inicio de sesión con correo inexistente: {correo_normalizado}")
                raise AuthenticationException("Credenciales de acceso incorrectas.")

            if not usuario.activo:
                logger.warning(f"Intento de inicio de sesión de usuario inactivo: {correo_normalizado}")
                raise AuthenticationException("La cuenta de usuario se encuentra deshabilitada.")

            # Validar contraseña
            if not self.verificar_password(password, usuario.password_hash):
                logger.warning(f"Contraseña incorrecta para el usuario: {correo_normalizado}")
                raise AuthenticationException("Credenciales de acceso incorrectas.")

            # Extraer roles asociados
            nombres_roles = [ur.rol.nombre for ur in usuario.roles_asociados if ur.rol]

            logger.info(f"Usuario autenticado con éxito: {usuario.correo} (Roles: {nombres_roles})")

            return UsuarioAutenticado(
                id_usuario=usuario.id_usuario,
                nombre=usuario.nombre,
                correo=usuario.correo,
                roles=nombres_roles,
            )

    def registrar_usuario(
        self,
        nombre: str,
        correo: str,
        password: str,
        roles_ids: Optional[List[int]] = None,
    ) -> Usuario:
        """
        Registra un nuevo usuario en la base de datos con contraseña cifrada y roles asignados.
        """
        correo_normalizado = correo.strip().lower()
        nombre_limpio = nombre.strip()

        if not nombre_limpio:
            raise ValidationException("El nombre del usuario no puede estar vacío.")

        with session_scope() as session:
            repo_usuario = UsuarioRepository(session)
            repo_rol = RolRepository(session)

            # 1. Comprobar que el correo no exista
            if repo_usuario.obtener_por_correo(correo_normalizado):
                raise DuplicateResourceException("Usuario", "correo", correo_normalizado)

            # 2. Hashear contraseña
            hash_pw = self.hashear_password(password)

            # 3. Crear entidad Usuario
            nuevo_usuario = Usuario(
                nombre=nombre_limpio,
                correo=correo_normalizado,
                password_hash=hash_pw,
                activo=True,
            )
            usuario_guardado = repo_usuario.create(nuevo_usuario)

            # 4. Asignar roles si se especificaron
            if roles_ids:
                for id_rol in roles_ids:
                    rol = repo_rol.get_by_id(id_rol)
                    if rol:
                        repo_usuario.asignar_rol(usuario_guardado.id_usuario, id_rol)

            logger.info(f"Usuario registrado exitosamente: {usuario_guardado.correo} (ID: {usuario_guardado.id_usuario})")
            return usuario_guardado

    def cambiar_password(
        self, id_usuario: int, password_actual: str, nueva_password: str
    ) -> bool:
        """
        Permite a un usuario modificar su contraseña validando primero la anterior.
        """
        with session_scope() as session:
            repo_usuario = UsuarioRepository(session)
            usuario = repo_usuario.get_by_id(id_usuario)

            if not usuario:
                raise ResourceNotFoundException("Usuario", id_usuario)

            if not self.verificar_password(password_actual, usuario.password_hash):
                raise AuthenticationException("La contraseña actual es incorrecta.")

            usuario.password_hash = self.hashear_password(nueva_password)
            logger.info(f"Contraseña actualizada para el usuario ID: {id_usuario}")
            return True
