"""
Pruebas Unitarias para el Servicio de Autenticación y Seguridad (AuthService).
"""

import unittest
from app.core.exceptions import ValidationException
from app.services.seguridad.auth_service import AuthService, UsuarioAutenticado


class TestAuthService(unittest.TestCase):
    """Casos de prueba para hashing, verificación de contraseñas y permisos de usuario."""

    def setUp(self) -> None:
        self.auth_service = AuthService()

    def test_hashear_password_exitoso(self) -> None:
        """Verifica que una contraseña válida genere un hash seguro con salt."""
        password = "ClaveSegura123!"
        hash_result = self.auth_service.hashear_password(password)

        self.assertIsInstance(hash_result, str)
        self.assertNotEqual(password, hash_result)
        self.assertTrue(len(hash_result) > 20)

    def test_hashear_password_demasiado_corta(self) -> None:
        """Verifica que contraseñas con menos de 6 caracteres lancen ValidationException."""
        with self.assertRaises(ValidationException):
            self.auth_service.hashear_password("12345")

    def test_verificar_password_correcta(self) -> None:
        """Verifica que la contraseña correcta valide True contra su hash."""
        password = "AdminSuperSecret2026"
        pwd_hash = self.auth_service.hashear_password(password)

        es_valida = self.auth_service.verificar_password(password, pwd_hash)
        self.assertTrue(es_valida)

    def test_verificar_password_incorrecta(self) -> None:
        """Verifica que una contraseña incorrecta retorne False."""
        password = "PasswordCorrecta123"
        pwd_hash = self.auth_service.hashear_password(password)

        es_valida = self.auth_service.verificar_password("PasswordErronea999", pwd_hash)
        self.assertFalse(es_valida)

    def test_usuario_autenticado_permisos_y_roles(self) -> None:
        """Verifica los métodos del DTO UsuarioAutenticado para RBAC."""
        usuario_admin = UsuarioAutenticado(
            id_usuario=1,
            nombre="Juan Perez",
            correo="juan@pos.com",
            roles=["ADMINISTRADOR", "CAJERO"]
        )
        self.assertTrue(usuario_admin.es_admin)
        self.assertTrue(usuario_admin.tiene_rol("cajero"))
        self.assertFalse(usuario_admin.tiene_rol("supervisor"))

        usuario_cajero = UsuarioAutenticado(
            id_usuario=2,
            nombre="Ana Gomez",
            correo="ana@pos.com",
            roles=["CAJERO"]
        )
        self.assertFalse(usuario_cajero.es_admin)
        self.assertTrue(usuario_cajero.tiene_rol("CAJERO"))


if __name__ == "__main__":
    unittest.main()
