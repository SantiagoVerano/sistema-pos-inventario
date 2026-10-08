"""
Módulo de Excepciones Centralizadas del Sistema (app/core/exceptions.py)

Responsabilidad Arquitectónica:
-------------------------------
Proveer una jerarquía de excepciones fuertemente tipada y semántica para toda la
aplicación. Ninguna capa debe lanzar excepciones genéricas (como Exception o RuntimeError)
para flujos de negocio controlados.

Jerarquía:
    AppException (Base del sistema)
    ├── BusinessException (Violación de reglas de negocio)
    │   ├── InsufficientStockException (Stock insuficiente para venta/salida)
    │   ├── DuplicateResourceException (SKU, código de barras o usuario duplicado)
    │   ├── ResourceNotFoundException (Recurso no encontrado por ID o clave)
    │   └── InvalidOperationException (Operación no válida en el estado actual)
    ├── SecurityException (Fallos de autenticación, autorización o permisos)
    │   ├── AuthenticationException (Credenciales inválidas o usuario inactivo)
    │   └── AuthorizationException (Permisos insuficientes para la acción)
    ├── DatabaseException (Errores de conexión, restricciones SQL o concurrencia)
    │   ├── ConcurrentModificationException (Conflicto de bloqueo pesimista/optimista)
    │   └── ForeignKeyViolationException (Intento de borrar registro con dependencias)
    └── ValidationException (Datos de entrada no conformes con esquemas de validación)
"""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Excepción raíz para todos los errores controlados de la aplicación."""

    def __init__(
        self,
        mensaje: str,
        codigo: str = "INTERNAL_ERROR",
        detalles: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
        self.detalles = detalles or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la excepción para logs o respuestas en capas superiores."""
        return {
            "error": self.__class__.__name__,
            "codigo": self.codigo,
            "mensaje": self.mensaje,
            "detalles": self.detalles,
        }


# ==============================================================================
# 1. EXCEPCIONES DE REGLAS DE NEGOCIO (Dominio y Servicios)
# ==============================================================================
class BusinessException(AppException):
    """Lanzada cuando una operación viola una regla de negocio explícita."""

    def __init__(
        self,
        mensaje: str,
        codigo: str = "BUSINESS_RULE_VIOLATION",
        detalles: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mensaje, codigo, detalles)


class InsufficientStockException(BusinessException):
    """Lanzada cuando se intenta debitar más stock del disponible."""

    def __init__(
        self,
        id_producto: int,
        stock_disponible: int,
        cantidad_solicitada: int,
        nombre_producto: Optional[str] = None,
    ) -> None:
        mensaje = (
            f"Stock insuficiente para el producto ID {id_producto}"
            + (f" ('{nombre_producto}')" if nombre_producto else "")
            + f". Disponible: {stock_disponible}, Solicitado: {cantidad_solicitada}."
        )
        detalles = {
            "id_producto": id_producto,
            "nombre_producto": nombre_producto,
            "stock_disponible": stock_disponible,
            "cantidad_solicitada": cantidad_solicitada,
        }
        super().__init__(mensaje, codigo="INSUFFICIENT_STOCK", detalles=detalles)


class DuplicateResourceException(BusinessException):
    """Lanzada cuando un recurso ya existe (ej: SKU o código de barras duplicado)."""

    def __init__(self, entidad: str, campo: str, valor: Any) -> None:
        mensaje = f"Ya existe un registro de '{entidad}' con {campo} = '{valor}'."
        detalles = {"entidad": entidad, "campo": campo, "valor": valor}
        super().__init__(mensaje, codigo="DUPLICATE_RESOURCE", detalles=detalles)


class ResourceNotFoundException(BusinessException):
    """Lanzada cuando no se encuentra una entidad requerida."""

    def __init__(self, entidad: str, identificador: Any) -> None:
        mensaje = f"No se encontró la entidad '{entidad}' con identificador: {identificador}."
        detalles = {"entidad": entidad, "identificador": identificador}
        super().__init__(mensaje, codigo="RESOURCE_NOT_FOUND", detalles=detalles)


class InvalidOperationException(BusinessException):
    """Lanzada cuando una acción no está permitida en el estado actual del objeto."""

    def __init__(self, mensaje: str, estado_actual: Optional[str] = None) -> None:
        detalles = {"estado_actual": estado_actual} if estado_actual else {}
        super().__init__(mensaje, codigo="INVALID_OPERATION", detalles=detalles)


# ==============================================================================
# 2. EXCEPCIONES DE SEGURIDAD Y PERMISOS
# ==============================================================================
class SecurityException(AppException):
    """Lanzada ante fallos en autenticación, autorización o integridad de seguridad."""

    def __init__(
        self,
        mensaje: str,
        codigo: str = "SECURITY_VIOLATION",
        detalles: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mensaje, codigo, detalles)


class AuthenticationException(SecurityException):
    """Credenciales incorrectas o usuario deshabilitado."""

    def __init__(self, mensaje: str = "Credenciales de acceso inválidas.") -> None:
        super().__init__(mensaje, codigo="AUTHENTICATION_FAILED")


class AuthorizationException(SecurityException):
    """Usuario no posee el rol o permiso requerido para ejecutar la acción."""

    def __init__(self, permiso_requerido: str, usuario: Optional[str] = None) -> None:
        mensaje = f"Acceso denegado. Se requiere el permiso: '{permiso_requerido}'."
        detalles = {"permiso_requerido": permiso_requerido, "usuario": usuario}
        super().__init__(mensaje, codigo="PERMISSION_DENIED", detalles=detalles)


# ==============================================================================
# 3. EXCEPCIONES DE PERSISTENCIA Y BASE DE DATOS
# ==============================================================================
class DatabaseException(AppException):
    """Lanzada ante fallos no recuperables en la capa de persistencia."""

    def __init__(
        self,
        mensaje: str,
        codigo: str = "DATABASE_ERROR",
        detalles: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(mensaje, codigo, detalles)


class ConcurrentModificationException(DatabaseException):
    """Lanzada cuando falla un bloqueo pesimista o se detecta concurrencia en stock."""

    def __init__(self, entidad: str, id_registro: Any) -> None:
        mensaje = f"Conflicto de concurrencia al intentar modificar '{entidad}' ID {id_registro}. Reintente la operación."
        detalles = {"entidad": entidad, "id_registro": id_registro}
        super().__init__(mensaje, codigo="CONCURRENCY_CONFLICT", detalles=detalles)


# ==============================================================================
# 4. EXCEPCIONES DE VALIDACIÓN DE FORMULARIOS / ENTRADAS
# ==============================================================================
class ValidationException(AppException):
    """Lanzada cuando los datos suministrados por la UI o API no superan la validación."""

    def __init__(self, mensaje: str, errores: Optional[Dict[str, str]] = None) -> None:
        detalles = {"errores": errores or {}}
        super().__init__(mensaje, codigo="VALIDATION_ERROR", detalles=detalles)
